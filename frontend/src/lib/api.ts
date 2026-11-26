export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export interface User {
  id: number;
  username: string;
  name: string;
  role: "ADMIN" | "INSTRUCTOR";
}

export interface ClassGroup {
  id: number;
  name: string;
  grade_term: string;
  instructor_id: number;
  instructor_name: string;
  current_unit_id: number | null;
  current_unit_title: string;
  last_completed_slide_order: number;
  total_unit_slides: number;
  current_difficulty: number;
  difficulty_label: string;
  last_delta: number;
  default_duration_min: number;
  admin_note: string;
  updated_at?: string;
}

export interface Unit {
  id: number;
  code: string;
  title: string;
  grade_term: string;
  description: string;
  sort_order: number;
  slide_count: number;
}

export interface UnitDetail extends Unit {
  slides: Slide[];
}

export interface Slide {
  id: number;
  unit_id: number;
  sort_order: number;
  badge_text: string;
  is_prob: boolean;
  page_ref: string;
  category: string;
  min_difficulty: number;
  max_difficulty: number;
  est_minutes: number;
  is_required: boolean;
  left_html: string;
  right_visual_html: string;
  footer_note_html: string;
  guide_html: string;
  points_list: string[];
  pacing_tip: string;
}

export interface PlannedSlideItem {
  slide: Slide;
  selected: boolean;
  time_slot: string;
  allocated_minutes: number;
  is_break_after: boolean;
  break_label: string;
}

export interface PreviewPlanResponse {
  class_id: number;
  class_name: string;
  unit_id: number;
  unit_title: string;
  target_difficulty: number;
  difficulty_label: string;
  duration_min: number;
  include_cover: boolean;
  total_selected_pages: number;
  total_estimated_minutes: number;
  admin_note: string;
  last_lesson_notes: string;
  items: PlannedSlideItem[];
}

export interface GeneratedDoc {
  id: number;
  class_id: number;
  unit_id: number;
  unit_title: string;
  target_difficulty: number;
  duration_min: number;
  include_cover: boolean;
  selected_slide_ids: number[];
  pdf_filename: string;
  download_url: string;
  page_count: number;
  created_at: string;
}

export interface LessonLog {
  id: number;
  class_id: number;
  unit_id: number;
  unit_title: string;
  instructor_id: number;
  instructor_name: string;
  taught_at: string;
  score_comprehension: number;
  score_accuracy: number;
  score_completion: number;
  score_engagement: number;
  instructor_suggestion: "UP" | "KEEP" | "DOWN";
  completed_slide_order: number;
  notes: string;
  calc_composite_score: number;
  calc_difficulty_before: number;
  calc_difficulty_after: number;
  calc_reason: string;
}

export interface DifficultyHistory {
  id: number;
  class_id: number;
  old_value: number;
  new_value: number;
  source: "SYSTEM_CALC" | "ADMIN_OVERRIDE";
  changed_by: number;
  operator_name: string;
  reason: string;
  created_at: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tm_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("tm_token", token);
  else localStorage.removeItem("tm_token");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) detail = err.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}
