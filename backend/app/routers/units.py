from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Slide, Unit, User
from app.schemas import MaterialUploadResponse, SlideCreate, SlideOut, UnitCreate, UnitDetailOut, UnitOut
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


@router.post("/upload-material", response_model=MaterialUploadResponse)
async def upload_material(
    unit_code: str = Form(...),
    unit_title: str = Form(...),
    grade_term: str = Form("五上"),
    save_to_db: bool = Form(True),
    raw_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上傳教材（PDF / TXT / MD 或直接貼上文字），自動解析觀念、演練、進階與頁碼，
    套用 A4 黑白印刷三色粉筆規格，組成結構化備課板書草稿並可一鍵入庫。
    """
    sections = []
    if file is not None:
        content = await file.read()
        fname = (file.filename or "").lower()
        if fname.endswith(".pdf"):
            sections = extract_text_from_pdf_bytes(content)
        else:
            text_str = content.decode("utf-8", errors="ignore").strip()
            if text_str:
                sections = [(1, text_str)]
    elif raw_text and raw_text.strip():
        sections = [(1, raw_text.strip())]
    else:
        raise HTTPException(status_code=400, detail="請上傳教材檔案（PDF/TXT/MD）或輸入教材文字內容")

    if not sections:
        raise HTTPException(status_code=400, detail="無法從教材中擷取有效文字內容")

    drafts = parse_material_to_slides(sections, unit_title=unit_title)
    if not drafts:
        raise HTTPException(status_code=400, detail="教材內容無法切分出有效板書段落")

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
            description=f"由上傳教材自動解析組版（共 {len(slide_creates)} 頁）",
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

