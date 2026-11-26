from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import ClassGroup, DifficultyHistory, GeneratedDoc, LessonLog, Slide, Unit, User
from app.schemas import (
    AdminOverrideRequest,
    ClassGroupOut,
    DifficultyHistoryOut,
    GeneratedDocOut,
    LessonLogOut,
)
from app.services.difficulty import get_difficulty_label

router = APIRouter(prefix="/api/classes", tags=["classes"])


def _to_class_out(c: ClassGroup, db: Session) -> ClassGroupOut:
    total_slides = 0
    unit_title = ""
    if c.current_unit_id:
        unit = db.query(Unit).filter(Unit.id == c.current_unit_id).first()
        if unit:
            unit_title = unit.title
            total_slides = db.query(Slide).filter(Slide.unit_id == unit.id).count()

    return ClassGroupOut(
        id=c.id,
        name=c.name,
        grade_term=c.grade_term,
        instructor_id=c.instructor_id,
        instructor_name=c.instructor.name if c.instructor else "",
        current_unit_id=c.current_unit_id,
        current_unit_title=unit_title,
        last_completed_slide_order=c.last_completed_slide_order,
        total_unit_slides=total_slides,
        current_difficulty=c.current_difficulty,
        difficulty_label=get_difficulty_label(c.current_difficulty),
        last_delta=c.last_delta,
        default_duration_min=c.default_duration_min,
        admin_note=c.admin_note or "",
        updated_at=c.updated_at,
    )


def _check_class_access(c: ClassGroup, user: User):
    if user.role != "ADMIN" and c.instructor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="無權存取此班級")


@router.get("", response_model=List[ClassGroupOut])
def list_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ClassGroup)
    if current_user.role != "ADMIN":
        q = q.filter(ClassGroup.instructor_id == current_user.id)
    classes = q.order_by(ClassGroup.id.asc()).all()
    return [_to_class_out(c, db) for c in classes]


@router.get("/{class_id}", response_model=ClassGroupOut)
def get_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _check_class_access(c, current_user)
    return _to_class_out(c, db)


@router.post("/{class_id}/override", response_model=ClassGroupOut)
def admin_override_class(
    class_id: int,
    req: AdminOverrideRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")

    if req.current_unit_id is not None:
        unit = db.query(Unit).filter(Unit.id == req.current_unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="找不到指定單元")
        c.current_unit_id = req.current_unit_id

    if req.last_completed_slide_order is not None:
        c.last_completed_slide_order = req.last_completed_slide_order

    if req.default_duration_min is not None:
        c.default_duration_min = req.default_duration_min

    if req.admin_note is not None:
        c.admin_note = req.admin_note

    if req.new_difficulty is not None:
        old_val = c.current_difficulty
        new_val = round(req.new_difficulty, 1)
        c.last_delta = round(new_val - old_val, 1)
        c.current_difficulty = new_val
        db.add(
            DifficultyHistory(
                class_id=c.id,
                old_value=old_val,
                new_value=new_val,
                source="ADMIN_OVERRIDE",
                changed_by=admin_user.id,
                reason=req.reason or "管理員手動調整難度",
            )
        )

    db.commit()
    db.refresh(c)
    return _to_class_out(c, db)


@router.get("/{class_id}/difficulty-history", response_model=List[DifficultyHistoryOut])
def get_difficulty_history(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _check_class_access(c, current_user)

    items = (
        db.query(DifficultyHistory)
        .filter(DifficultyHistory.class_id == class_id)
        .order_by(DifficultyHistory.created_at.desc())
        .all()
    )
    return [
        DifficultyHistoryOut(
            id=h.id,
            class_id=h.class_id,
            old_value=h.old_value,
            new_value=h.new_value,
            source=h.source,
            changed_by=h.changed_by,
            operator_name=h.operator.name if h.operator else "",
            reason=h.reason,
            created_at=h.created_at,
        )
        for h in items
    ]


@router.get("/{class_id}/logs", response_model=List[LessonLogOut])
def get_class_logs(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _check_class_access(c, current_user)

    logs = (
        db.query(LessonLog)
        .filter(LessonLog.class_id == class_id)
        .order_by(LessonLog.taught_at.desc())
        .all()
    )
    return [
        LessonLogOut(
            id=l.id,
            class_id=l.class_id,
            unit_id=l.unit_id,
            unit_title=l.unit.title if l.unit else "",
            instructor_id=l.instructor_id,
            instructor_name=l.instructor.name if l.instructor else "",
            taught_at=l.taught_at,
            score_comprehension=l.score_comprehension,
            score_accuracy=l.score_accuracy,
            score_completion=l.score_completion,
            score_engagement=l.score_engagement,
            instructor_suggestion=l.instructor_suggestion,
            completed_slide_order=l.completed_slide_order,
            notes=l.notes or "",
            calc_composite_score=l.calc_composite_score,
            calc_difficulty_before=l.calc_difficulty_before,
            calc_difficulty_after=l.calc_difficulty_after,
            calc_reason=l.calc_reason,
        )
        for l in logs
    ]


@router.get("/{class_id}/docs", response_model=List[GeneratedDocOut])
def get_class_docs(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="找不到班級")
    _check_class_access(c, current_user)

    docs = (
        db.query(GeneratedDoc)
        .filter(GeneratedDoc.class_id == class_id)
        .order_by(GeneratedDoc.created_at.desc())
        .all()
    )
    return [
        GeneratedDocOut(
            id=d.id,
            class_id=d.class_id,
            unit_id=d.unit_id,
            unit_title=d.unit.title if d.unit else "",
            target_difficulty=d.target_difficulty,
            duration_min=d.duration_min,
            include_cover=d.include_cover,
            selected_slide_ids=d.selected_slide_ids,
            pdf_filename=d.pdf_filename,
            download_url=f"/api/lessons/docs/{d.id}/download",
            page_count=d.page_count,
            created_at=d.created_at,
        )
        for d in docs
    ]
