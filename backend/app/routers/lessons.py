from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import ClassGroup, DifficultyHistory, GeneratedDoc, LessonLog, Slide, Unit, User
from app.schemas import (
    GeneratedDocOut,
    GeneratePdfRequest,
    LessonLogCreate,
    LessonLogOut,
    PlannedSlideItem,
    PreviewPlanRequest,
    PreviewPlanResponse,
    RangeGeneratePdfRequest,
    RangePlanRequest,
)
from app.services.assembler import build_lesson_plan, build_range_lesson_plan
from app.services.difficulty import evaluate_next_difficulty, get_difficulty_label
from app.services.pdf_renderer import build_full_document_html, render_html_to_pdf

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def _verify_class_access(c: ClassGroup, user: User):
    if user.role != "ADMIN" and c.instructor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="無權操作此班級")


def _get_last_lesson_notes(class_id: int, db: Session) -> str:
    last_log = (
        db.query(LessonLog)
        .filter(LessonLog.class_id == class_id)
        .order_by(LessonLog.taught_at.desc())
        .first()
    )
    return last_log.notes if last_log and last_log.notes else ""


@router.post("/preview-plan", response_model=PreviewPlanResponse)
def preview_plan(
    req: PreviewPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _verify_class_access(c, current_user)

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="找不到單元")

    target_diff = req.target_difficulty if req.target_difficulty is not None else c.current_difficulty
    start_order = (
        req.start_from_slide_order
        if req.start_from_slide_order is not None
        else (c.last_completed_slide_order if c.current_unit_id == unit.id else 0)
    )

    plan_items = build_lesson_plan(
        slides=unit.slides,
        target_difficulty=target_diff,
        duration_min=req.duration_min,
        start_from_slide_order=start_order,
        explicit_selected_ids=req.selected_slide_ids,
    )

    selected_items = [p for p in plan_items if p["selected"]]
    total_est = sum(p["allocated_minutes"] for p in selected_items)

    return PreviewPlanResponse(
        class_id=c.id,
        class_name=c.name,
        unit_id=unit.id,
        unit_title=unit.title,
        target_difficulty=round(target_diff, 1),
        difficulty_label=get_difficulty_label(target_diff),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        total_selected_pages=len(selected_items) + (1 if req.include_cover else 0),
        total_estimated_minutes=total_est,
        admin_note=c.admin_note or "",
        last_lesson_notes=_get_last_lesson_notes(c.id, db),
        items=[
            PlannedSlideItem(
                slide=p["slide"],
                selected=p["selected"],
                time_slot=p["time_slot"],
                allocated_minutes=p["allocated_minutes"],
                is_break_after=p["is_break_after"],
                break_label=p["break_label"],
            )
            for p in plan_items
        ],
    )


@router.post("/generate-pdf", response_model=GeneratedDocOut)
def generate_pdf(
    req: GeneratePdfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _verify_class_access(c, current_user)

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="找不到單元")

    if not req.selected_slide_ids:
        raise HTTPException(status_code=400, detail="請至少選擇一頁板書")

    target_diff = req.target_difficulty if req.target_difficulty is not None else c.current_difficulty

    plan_items = build_lesson_plan(
        slides=unit.slides,
        target_difficulty=target_diff,
        duration_min=req.duration_min,
        start_from_slide_order=0,
        explicit_selected_ids=req.selected_slide_ids,
    )
    selected_items = [p for p in plan_items if p["selected"]]
    if not selected_items:
        raise HTTPException(status_code=400, detail="選擇的板書頁面無效")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_class = "".join(ch for ch in c.name if ch.isalnum() or ch in "-_") or f"class{c.id}"
    safe_code = "".join(ch for ch in unit.code if ch.isalnum() or ch in "-_") or f"unit{unit.id}"
    filename = f"{safe_class}_{safe_code}_D{target_diff:.1f}_{timestamp}.pdf"
    output_path = settings.GENERATED_PDF_DIR / filename

    full_html = build_full_document_html(
        doc_title=f"{c.name} - {unit.title} 備課板書",
        class_name=c.name,
        instructor_name=c.instructor.name if c.instructor else current_user.name,
        unit_title=unit.title,
        target_difficulty=target_diff,
        difficulty_label=get_difficulty_label(target_diff),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        admin_note=c.admin_note or "",
        last_lesson_notes=_get_last_lesson_notes(c.id, db),
        selected_items=selected_items,
    )

    page_count = render_html_to_pdf(full_html, output_path)

    doc_record = GeneratedDoc(
        class_id=c.id,
        unit_id=unit.id,
        created_by=current_user.id,
        target_difficulty=round(target_diff, 1),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        selected_slide_ids=[p["slide"].id for p in selected_items],
        pdf_filename=filename,
        page_count=page_count,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    return GeneratedDocOut(
        id=doc_record.id,
        class_id=doc_record.class_id,
        unit_id=doc_record.unit_id,
        unit_title=unit.title,
        target_difficulty=doc_record.target_difficulty,
        duration_min=doc_record.duration_min,
        include_cover=doc_record.include_cover,
        selected_slide_ids=doc_record.selected_slide_ids,
        pdf_filename=doc_record.pdf_filename,
        download_url=f"/api/lessons/docs/{doc_record.id}/download",
        page_count=doc_record.page_count,
        created_at=doc_record.created_at,
    )


@router.get("/docs/{doc_id}/download")
def download_pdf(
    doc_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(GeneratedDoc).filter(GeneratedDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="找不到 PDF 檔案紀錄")
    file_path = settings.GENERATED_PDF_DIR / doc.pdf_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF 檔案不存在")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.pdf_filename,
    )


@router.post("/logs", response_model=LessonLogOut)
def submit_lesson_log(
    req: LessonLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _verify_class_access(c, current_user)

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="找不到單元")

    eval_res = evaluate_next_difficulty(
        current_difficulty=c.current_difficulty,
        score_comprehension=req.score_comprehension,
        score_accuracy=req.score_accuracy,
        score_completion=req.score_completion,
        score_engagement=req.score_engagement,
        instructor_suggestion=req.instructor_suggestion,
        previous_delta=c.last_delta,
    )

    log = LessonLog(
        class_id=c.id,
        unit_id=unit.id,
        instructor_id=current_user.id,
        score_comprehension=req.score_comprehension,
        score_accuracy=req.score_accuracy,
        score_completion=req.score_completion,
        score_engagement=req.score_engagement,
        instructor_suggestion=req.instructor_suggestion,
        completed_slide_order=req.completed_slide_order,
        notes=req.notes,
        calc_composite_score=eval_res.composite_score,
        calc_difficulty_before=eval_res.old_difficulty,
        calc_difficulty_after=eval_res.new_difficulty,
        calc_reason=eval_res.reason,
    )
    db.add(log)

    # 更新班級進度與難度係數
    c.current_unit_id = unit.id
    c.last_completed_slide_order = req.completed_slide_order
    c.last_delta = eval_res.delta
    c.current_difficulty = eval_res.new_difficulty

    db.add(
        DifficultyHistory(
            class_id=c.id,
            old_value=eval_res.old_difficulty,
            new_value=eval_res.new_difficulty,
            source="SYSTEM_CALC",
            changed_by=current_user.id,
            reason=eval_res.reason,
        )
    )

    db.commit()
    db.refresh(log)

    return LessonLogOut(
        id=log.id,
        class_id=log.class_id,
        unit_id=log.unit_id,
        unit_title=unit.title,
        instructor_id=log.instructor_id,
        instructor_name=current_user.name,
        taught_at=log.taught_at,
        score_comprehension=log.score_comprehension,
        score_accuracy=log.score_accuracy,
        score_completion=log.score_completion,
        score_engagement=log.score_engagement,
        instructor_suggestion=log.instructor_suggestion,
        completed_slide_order=log.completed_slide_order,
        notes=log.notes or "",
        calc_composite_score=log.calc_composite_score,
        calc_difficulty_before=log.calc_difficulty_before,
        calc_difficulty_after=log.calc_difficulty_after,
        calc_reason=log.calc_reason,
    )


@router.post("/range-preview", response_model=PreviewPlanResponse)
def range_preview(
    req: RangePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _verify_class_access(c, current_user)

    units = db.query(Unit).filter(Unit.id.in_(req.unit_ids)).order_by(Unit.sort_order.asc()).all()
    if not units:
        raise HTTPException(status_code=404, detail="找不到指定單元")

    all_slides = []
    for u in units:
        all_slides.extend(u.slides)

    target_diff = req.target_difficulty if req.target_difficulty is not None else c.current_difficulty
    plan_items = build_range_lesson_plan(
        slides=all_slides,
        target_difficulty=target_diff,
        duration_min=req.duration_min,
        page_start=req.page_start,
        page_end=req.page_end,
        categories=req.categories,
        explicit_selected_ids=req.selected_slide_ids,
    )

    selected_items = [p for p in plan_items if p["selected"]]
    total_est = sum(p["allocated_minutes"] for p in selected_items)
    range_desc = " + ".join(u.title for u in units)
    if req.page_start or req.page_end:
        range_desc += f"（P.{req.page_start or 1}~P.{req.page_end or '末'}）"

    return PreviewPlanResponse(
        class_id=c.id,
        class_name=c.name,
        unit_id=units[0].id,
        unit_title=range_desc,
        target_difficulty=round(target_diff, 1),
        difficulty_label=get_difficulty_label(target_diff),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        total_selected_pages=len(selected_items) + (1 if req.include_cover else 0),
        total_estimated_minutes=total_est,
        admin_note=c.admin_note or "",
        last_lesson_notes=_get_last_lesson_notes(c.id, db),
        items=[
            PlannedSlideItem(
                slide=p["slide"],
                selected=p["selected"],
                time_slot=p["time_slot"],
                allocated_minutes=p["allocated_minutes"],
                is_break_after=p["is_break_after"],
                break_label=p["break_label"],
            )
            for p in plan_items
        ],
    )


@router.post("/generate-range-pdf", response_model=GeneratedDocOut)
def generate_range_pdf(
    req: RangeGeneratePdfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _verify_class_access(c, current_user)

    units = db.query(Unit).filter(Unit.id.in_(req.unit_ids)).order_by(Unit.sort_order.asc()).all()
    if not units:
        raise HTTPException(status_code=404, detail="找不到指定單元")

    all_slides = []
    for u in units:
        all_slides.extend(u.slides)

    target_diff = req.target_difficulty if req.target_difficulty is not None else c.current_difficulty
    plan_items = build_range_lesson_plan(
        slides=all_slides,
        target_difficulty=target_diff,
        duration_min=req.duration_min,
        explicit_selected_ids=req.selected_slide_ids,
    )
    selected_items = [p for p in plan_items if p["selected"]]
    if not selected_items:
        raise HTTPException(status_code=400, detail="請至少選擇一頁板書")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_class = "".join(ch for ch in c.name if ch.isalnum() or ch in "-_") or f"class{c.id}"
    filename = f"{safe_class}_RANGE_D{target_diff:.1f}_{timestamp}.pdf"
    output_path = settings.GENERATED_PDF_DIR / filename

    full_html = build_full_document_html(
        doc_title=f"{c.name} - {req.range_title} 備課板書",
        class_name=c.name,
        instructor_name=c.instructor.name if c.instructor else current_user.name,
        unit_title=req.range_title,
        target_difficulty=target_diff,
        difficulty_label=get_difficulty_label(target_diff),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        admin_note=c.admin_note or "",
        last_lesson_notes=_get_last_lesson_notes(c.id, db),
        selected_items=selected_items,
    )

    page_count = render_html_to_pdf(full_html, output_path)

    doc_record = GeneratedDoc(
        class_id=c.id,
        unit_id=units[0].id,
        created_by=current_user.id,
        target_difficulty=round(target_diff, 1),
        duration_min=req.duration_min,
        include_cover=req.include_cover,
        selected_slide_ids=[p["slide"].id for p in selected_items],
        pdf_filename=filename,
        page_count=page_count,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    return GeneratedDocOut(
        id=doc_record.id,
        class_id=doc_record.class_id,
        unit_id=doc_record.unit_id,
        unit_title=req.range_title,
        target_difficulty=doc_record.target_difficulty,
        duration_min=doc_record.duration_min,
        include_cover=doc_record.include_cover,
        selected_slide_ids=doc_record.selected_slide_ids,
        pdf_filename=doc_record.pdf_filename,
        download_url=f"/api/lessons/docs/{doc_record.id}/download",
        page_count=doc_record.page_count,
        created_at=doc_record.created_at,
    )

