from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default="INSTRUCTOR")  # ADMIN | INSTRUCTOR
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    classes = relationship("ClassGroup", back_populates="instructor")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)  # e.g. G5-U9
    title = Column(String(200), nullable=False)  # e.g. 五上9 多位數乘除技巧
    grade_term = Column(String(32), nullable=False, default="五上")
    description = Column(Text, default="")
    sort_order = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    slides = relationship("Slide", back_populates="unit", order_by="Slide.sort_order", cascade="all, delete-orphan")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False)
    badge_text = Column(String(64), nullable=False)  # e.g. 觀念 1, 演練 P.72
    is_prob = Column(Boolean, default=False)
    page_ref = Column(String(64), default="")  # e.g. P.68, P.69-70 分配律實戰
    category = Column(String(32), nullable=False, default="CONCEPT")
    # CONCEPT | DRILL | ADVANCED | GIFTED_A | GIFTED_B | GIFTED_C
    min_difficulty = Column(Float, nullable=False, default=1.0)
    max_difficulty = Column(Float, nullable=False, default=5.0)
    est_minutes = Column(Integer, nullable=False, default=10)
    is_required = Column(Boolean, default=False)
    left_html = Column(Text, nullable=False)
    right_visual_html = Column(Text, nullable=False)
    footer_note_html = Column(Text, default="")
    guide_html = Column(Text, nullable=False)
    points_list = Column(JSON, nullable=False, default=list)
    pacing_tip = Column(String(255), default="")

    unit = relationship("Unit", back_populates="slides")


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    grade_term = Column(String(32), nullable=False, default="五上")
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    last_completed_slide_order = Column(Integer, default=0)
    current_difficulty = Column(Float, nullable=False, default=3.0)
    last_delta = Column(Float, nullable=False, default=0.0)
    default_duration_min = Column(Integer, nullable=False, default=180)
    admin_note = Column(Text, default="")
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    instructor = relationship("User", back_populates="classes")
    current_unit = relationship("Unit")
    logs = relationship("LessonLog", back_populates="class_group", order_by="LessonLog.taught_at.desc()")
    difficulty_history = relationship(
        "DifficultyHistory", back_populates="class_group", order_by="DifficultyHistory.created_at.desc()"
    )
    generated_docs = relationship(
        "GeneratedDoc", back_populates="class_group", order_by="GeneratedDoc.created_at.desc()"
    )


class LessonLog(Base):
    __tablename__ = "lesson_logs"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    taught_at = Column(DateTime(timezone=True), default=utcnow)

    score_comprehension = Column(Integer, nullable=False)  # 1-5
    score_accuracy = Column(Integer, nullable=False)       # 1-5
    score_completion = Column(Integer, nullable=False)     # 1-5
    score_engagement = Column(Integer, nullable=False)     # 1-5
    instructor_suggestion = Column(String(16), nullable=False, default="KEEP")  # UP | KEEP | DOWN
    completed_slide_order = Column(Integer, nullable=False, default=0)
    notes = Column(Text, default="")

    calc_composite_score = Column(Float, nullable=False)
    calc_difficulty_before = Column(Float, nullable=False)
    calc_difficulty_after = Column(Float, nullable=False)
    calc_reason = Column(Text, nullable=False)

    class_group = relationship("ClassGroup", back_populates="logs")
    unit = relationship("Unit")
    instructor = relationship("User")


class DifficultyHistory(Base):
    __tablename__ = "difficulty_history"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    source = Column(String(32), nullable=False)  # SYSTEM_CALC | ADMIN_OVERRIDE
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    class_group = relationship("ClassGroup", back_populates="difficulty_history")
    operator = relationship("User")


class GeneratedDoc(Base):
    __tablename__ = "generated_docs"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_difficulty = Column(Float, nullable=False)
    duration_min = Column(Integer, nullable=False)
    include_cover = Column(Boolean, default=True)
    selected_slide_ids = Column(JSON, nullable=False, default=list)
    pdf_filename = Column(String(255), nullable=False)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    class_group = relationship("ClassGroup", back_populates="generated_docs")
    unit = relationship("Unit")
    creator = relationship("User")
