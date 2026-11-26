from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Slide, Unit, User
from app.schemas import MaterialUploadResponse, SlideCreate, SlideOut, UnitCreate, UnitDetailOut, UnitOut
from app.services.ai_board_generator import (
    generate_slides_with_ai,
    load_saved_ai_config,
    save_ai_key,
)
from app.services.material_parser import extract_text_from_pdf_bytes, parse_material_to_slides

router = APIRouter(prefix="/api/units", tags=["units"])


@router.get("", response_model=List[UnitOut])
def list_units(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    units = db.query(Unit).order_by(Unit.sort_order.asc(), Unit.id.asc()).all()
    return [
        UnitOut(
            id=u.id,
            code=u.code,
            title=u.title,
            grade_term=u.grade_term,
            description=u.description or "",
            sort_order=u.sort_order,
            slide_count=len(u.slides),
        )
        for u in units
    ]


@router.get("/{unit_id}", response_model=UnitDetailOut)
def get_unit(
    unit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    u = db.query(Unit).filter(Unit.id == unit_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="找不到單元")
    return UnitDetailOut(
        id=u.id,
        code=u.code,
        title=u.title,
        grade_term=u.grade_term,
        description=u.description or "",
        sort_order=u.sort_order,
        slide_count=len(u.slides),
        slides=u.slides,
    )


@router.post("", response_model=UnitDetailOut)
def create_unit(
    req: UnitCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(Unit).filter(Unit.code == req.code).first():
        raise HTTPException(status_code=400, detail="單元代碼已存在")

    u = Unit(
        code=req.code,
        title=req.title,
        grade_term=req.grade_term,
        description=req.description,
        sort_order=req.sort_order,
    )
    db.add(u)
    db.flush()
    for s in req.slides:
        db.add(Slide(unit_id=u.id, **s.model_dump()))
    db.commit()
    db.refresh(u)
    return UnitDetailOut(
        id=u.id,
        code=u.code,
        title=u.title,
        grade_term=u.grade_term,
        description=u.description or "",
        sort_order=u.sort_order,
        slide_count=len(u.slides),
        slides=u.slides,
    )


@router.post("/{unit_id}/slides", response_model=SlideOut)
def add_slide(
    unit_id: int,
    req: SlideCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    u = db.query(Unit).filter(Unit.id == unit_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="找不到單元")
    s = Slide(unit_id=unit_id, **req.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/slides/{slide_id}", response_model=SlideOut)
def update_slide(
    slide_id: int,
    req: SlideCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    s = db.query(Slide).filter(Slide.id == slide_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="找不到板書頁面")
    for k, v in req.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/slides/{slide_id}")
def delete_slide(
    slide_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    s = db.query(Slide).filter(Slide.id == slide_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="找不到板書頁面")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.get("/ai-status")
def get_ai_status(current_user: User = Depends(get_current_user)):
    cfg = load_saved_ai_config()
    return {
        "gemini_configured": cfg["gemini_configured"],
        "openai_configured": cfg["openai_configured"],
    }


@router.post("/upload-material", response_model=MaterialUploadResponse)
async def upload_material(
    unit_code: str = Form(...),
    unit_title: str = Form(...),
    grade_term: str = Form("五上"),
    save_to_db: bool = Form(True),
    use_ai: bool = Form(True),
    ai_provider: str = Form("gemini"),
    api_key: Optional[str] = Form(None),
    save_api_key: bool = Form(False),
    target_duration_min: int = Form(180),
    raw_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上傳教材（PDF / TXT / MD 或直接貼上文字），優先透過 AI 視覺模型（直接看懂直式分數與圖形）
    嚴格依 A4 黑白印刷三色粉筆規格自動組版；若未設定 AI 金鑰或關閉 AI 則使用本地規則解析。
    """
    pdf_bytes: Optional[bytes] = None
    text_input: Optional[str] = raw_text

    if file is not None:
        content = await file.read()
        fname = (file.filename or "").lower()
        if fname.endswith(".pdf"):
            pdf_bytes = content
        else:
            text_input = content.decode("utf-8", errors="ignore").strip()

    if not pdf_bytes and not (text_input and text_input.strip()):
        raise HTTPException(status_code=400, detail="請上傳教材檔案（PDF/TXT/MD）或輸入教材文字內容")

    if save_api_key and api_key and api_key.strip():
        save_ai_key(ai_provider, api_key.strip())

    cfg = load_saved_ai_config()
    has_key = bool((api_key and api_key.strip()) or (cfg["gemini_configured"] if ai_provider == "gemini" else cfg["openai_configured"]))

    slide_creates: List[SlideCreate] = []
    if use_ai:
        if not has_key:
            raise HTTPException(
                status_code=400,
                detail=f"尚未設定 {ai_provider.upper()} API Key，請於欄位輸入金鑰（或取消勾選 AI 模式改用基本文字解析）。",
            )
        try:
            slide_creates = await generate_slides_with_ai(
                unit_title=unit_title,
                target_duration_min=target_duration_min,
                provider=ai_provider,
                api_key=api_key,
                pdf_bytes=pdf_bytes,
                raw_text=text_input,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"AI 生成板書失敗：{exc}")
    else:
        sections = extract_text_from_pdf_bytes(pdf_bytes) if pdf_bytes else [(1, text_input.strip())]
        if not sections:
            raise HTTPException(status_code=400, detail="無法從教材中擷取有效文字內容")
        drafts = parse_material_to_slides(sections, unit_title=unit_title)
        slide_creates = [
            SlideCreate(
                sort_order=d.sort_order,
                badge_text=d.badge_text,
                is_prob=d.is_prob,
                page_ref=d.page_ref,
                category=d.category,
                min_difficulty=d.min_difficulty,
                max_difficulty=d.max_difficulty,
                est_minutes=d.est_minutes,
                is_required=d.is_required,
                left_html=d.left_html,
                right_visual_html=d.right_visual_html,
                footer_note_html=d.footer_note_html,
                guide_html=d.guide_html,
                points_list=d.points_list,
                pacing_tip=d.pacing_tip,
            )
            for d in drafts
        ]

    if not slide_creates:
        raise HTTPException(status_code=400, detail="未能產生有效板書頁面")

    created_unit_id: Optional[int] = None
    if save_to_db:
        existing = db.query(Unit).filter(Unit.code == unit_code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"單元代碼 {unit_code} 已存在，請更換代碼")
        max_sort = db.query(Unit).count() + 1
        u = Unit(
            code=unit_code,
            title=unit_title,
            grade_term=grade_term,
            description=f"由{'AI 視覺教研引擎' if use_ai else '規則解析'}自動組版（共 {len(slide_creates)} 頁）",
            sort_order=max_sort,
        )
        db.add(u)
        db.flush()
        for sc in slide_creates:
            db.add(Slide(unit_id=u.id, **sc.model_dump()))
        db.commit()
        db.refresh(u)
        created_unit_id = u.id

    return MaterialUploadResponse(
        unit_id=created_unit_id,
        unit_code=unit_code,
        unit_title=unit_title,
        parsed_count=len(slide_creates),
        slides=slide_creates,
    )

