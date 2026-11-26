from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class SlideBase(BaseModel):
    sort_order: int
    badge_text: str
    is_prob: bool = False
    page_ref: str = ""
    category: str = "CONCEPT"
    min_difficulty: float = 1.0
    max_difficulty: float = 5.0
    est_minutes: int = 10
    is_required: bool = False
    left_html: str
    right_visual_html: str
    footer_note_html: str = ""
    guide_html: str
    points_list: List[str] = Field(default_factory=list)
    pacing_tip: str = ""


class SlideCreate(SlideBase):
    pass


class SlideOut(SlideBase):
    id: int
    unit_id: int

    class Config:
        from_attributes = True


class UnitBase(BaseModel):
    code: str
    title: str
    grade_term: str = "五上"
    description: str = ""
    sort_order: int = 1


class UnitCreate(UnitBase):
    slides: List[SlideCreate] = Field(default_factory=list)


class UnitOut(UnitBase):
    id: int
    slide_count: int = 0

    class Config:
        from_attributes = True


class UnitDetailOut(UnitOut):
    slides: List[SlideOut] = Field(default_factory=list)


class DifficultyHistoryOut(BaseModel):
    id: int
    class_id: int
    old_value: float
    new_value: float
    source: str
    changed_by: int
    operator_name: str = ""
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class LessonLogCreate(BaseModel):
    class_id: int
    unit_id: int
    score_comprehension: int = Field(ge=1, le=5)
    score_accuracy: int = Field(ge=1, le=5)
    score_completion: int = Field(ge=1, le=5)
    score_engagement: int = Field(ge=1, le=5)
    instructor_suggestion: str = Field(pattern="^(UP|KEEP|DOWN)$", default="KEEP")
    completed_slide_order: int = Field(ge=0, default=0)
    notes: str = ""


class LessonLogOut(BaseModel):
    id: int
    class_id: int
    unit_id: int
    unit_title: str = ""
    instructor_id: int
    instructor_name: str = ""
    taught_at: datetime
    score_comprehension: int
    score_accuracy: int
    score_completion: int
    score_engagement: int
    instructor_suggestion: str
    completed_slide_order: int
    notes: str
    calc_composite_score: float
    calc_difficulty_before: float
    calc_difficulty_after: float
    calc_reason: str

    class Config:
        from_attributes = True


class GeneratedDocOut(BaseModel):
    id: int
    class_id: int
    unit_id: int
    unit_title: str = ""
    target_difficulty: float
    duration_min: int
    include_cover: bool
    selected_slide_ids: List[int]
    pdf_filename: str
    download_url: str = ""
    page_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClassGroupOut(BaseModel):
    id: int
    name: str
    grade_term: str
    instructor_id: int
    instructor_name: str = ""
    current_unit_id: Optional[int]
    current_unit_title: str = ""
    last_completed_slide_order: int
    total_unit_slides: int = 0
    current_difficulty: float
    difficulty_label: str = ""
    last_delta: float
    default_duration_min: int
    admin_note: str
    updated_at: Optional[datetime] = None


class ClassCreateRequest(BaseModel):
    name: str
    grade_term: str = "五上"
    instructor_id: int
    current_unit_id: Optional[int] = None
    current_difficulty: float = Field(ge=1.0, le=5.0, default=3.0)
    default_duration_min: int = 180


class AdminOverrideRequest(BaseModel):
    current_unit_id: Optional[int] = None
    last_completed_slide_order: Optional[int] = Field(default=None, ge=0)
    new_difficulty: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    default_duration_min: Optional[int] = Field(default=None, ge=60, le=300)
    admin_note: Optional[str] = None
    reason: str = "管理員手動調整"


class PreviewPlanRequest(BaseModel):
    class_id: int
    unit_id: int
    duration_min: int = Field(ge=60, le=300, default=180)
    target_difficulty: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    start_from_slide_order: Optional[int] = Field(default=None, ge=0)
    include_cover: bool = True
    selected_slide_ids: Optional[List[int]] = None


class PlannedSlideItem(BaseModel):
    slide: SlideOut
    selected: bool
    time_slot: str
    allocated_minutes: int
    is_break_after: bool = False
    break_label: str = ""


class PreviewPlanResponse(BaseModel):
    class_id: int
    class_name: str
    unit_id: int
    unit_title: str
    target_difficulty: float
    difficulty_label: str
    duration_min: int
    include_cover: bool
    total_selected_pages: int
    total_estimated_minutes: int
    admin_note: str
    last_lesson_notes: str
    items: List[PlannedSlideItem]


class GeneratePdfRequest(BaseModel):
    class_id: int
    unit_id: int
    duration_min: int = Field(ge=60, le=300, default=180)
    target_difficulty: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    include_cover: bool = True
    selected_slide_ids: List[int]


class RangePlanRequest(BaseModel):
    class_id: int
    unit_ids: List[int] = Field(min_length=1)
    page_start: Optional[int] = Field(default=None, ge=1)
    page_end: Optional[int] = Field(default=None, ge=1)
    categories: Optional[List[str]] = None
    duration_min: int = Field(ge=60, le=300, default=180)
    target_difficulty: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    include_cover: bool = True
    selected_slide_ids: Optional[List[int]] = None


class RangeGeneratePdfRequest(BaseModel):
    class_id: int
    unit_ids: List[int] = Field(min_length=1)
    range_title: str = "跨範圍自動組裝備課"
    duration_min: int = Field(ge=60, le=300, default=180)
    target_difficulty: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    include_cover: bool = True
    selected_slide_ids: List[int]


class MaterialUploadResponse(BaseModel):
    unit_id: Optional[int] = None
    unit_code: str
    unit_title: str
    parsed_count: int
    slides: List[SlideCreate]

