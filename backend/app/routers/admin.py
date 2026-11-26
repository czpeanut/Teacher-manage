from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import require_admin
from app.database import get_db
from app.models import ClassGroup, GeneratedDoc, LessonLog, Unit, User
from app.routers.classes import _to_class_out
from app.schemas import ClassCreateRequest, ClassGroupOut, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def admin_overview(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    instructors_count = db.query(User).filter(User.role == "INSTRUCTOR").count()
    classes = db.query(ClassGroup).all()
    logs_count = db.query(LessonLog).count()
    docs_count = db.query(GeneratedDoc).count()
    units_count = db.query(Unit).count()

    avg_diff = round(sum(c.current_difficulty for c in classes) / len(classes), 2) if classes else 3.0
    alert_classes = [
        {
            "id": c.id,
            "name": c.name,
            "difficulty": c.current_difficulty,
            "last_delta": c.last_delta,
        }
        for c in classes
        if c.current_difficulty <= 1.8 or c.last_delta <= -0.3
    ]

    return {
        "instructors_count": instructors_count,
        "classes_count": len(classes),
        "units_count": units_count,
        "logs_count": logs_count,
        "docs_count": docs_count,
        "avg_difficulty": avg_diff,
        "alert_classes": alert_classes,
    }


@router.get("/instructors", response_model=List[UserOut])
def list_instructors(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(User.role == "INSTRUCTOR").order_by(User.id.asc()).all()


@router.post("/classes", response_model=ClassGroupOut)
def create_class(
    req: ClassCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    instructor = db.query(User).filter(User.id == req.instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="找不到指定講師")

    c = ClassGroup(
        name=req.name,
        grade_term=req.grade_term,
        instructor_id=req.instructor_id,
        current_unit_id=req.current_unit_id,
        current_difficulty=round(req.current_difficulty, 1),
        default_duration_min=req.default_duration_min,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_class_out(c, db)
