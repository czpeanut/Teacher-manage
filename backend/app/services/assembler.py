from typing import List, Optional
from app.models import Slide


def _format_mm(total_min: int) -> str:
    h = total_min // 60
    m = total_min % 60
    return f"{h}:{m:02d}"


def build_lesson_plan(
    slides: List[Slide],
    target_difficulty: float,
    duration_min: int = 180,
    start_from_slide_order: int = 0,
    explicit_selected_ids: Optional[List[int]] = None,
) -> List[dict]:
    """
    依據目標難度係數、授課時長與起始進度，自動挑選板書頁面並計算時段控管與中場休息。
    """
    ordered = sorted(slides, key=lambda s: s.sort_order)

    if explicit_selected_ids is not None:
        selected_set = set(explicit_selected_ids)
    else:
        selected_set = set()
        # 1. 優先納入尚未教完的頁面起點之後的內容，並依難度過濾
        candidates = [s for s in ordered if s.sort_order > start_from_slide_order]
        if not candidates:
            # 若已教完該單元最後一頁，則提供整單元完整版（複習/新輪次）
            candidates = ordered

        # 基礎難度 (Lv1~2) 可適度放寬觀念與基礎演練時間 (+15%)
        total_budget = duration_min
        # 預留休息時間：2小時預留 5 分鐘，3小時預留 13 分鐘
        break_reserve = 13 if duration_min >= 150 else 5
        teach_budget = max(45, total_budget - break_reserve)

        accumulated = 0
        for s in candidates:
            in_diff_range = s.min_difficulty <= target_difficulty <= s.max_difficulty
            if s.is_required or in_diff_range:
                if accumulated + s.est_minutes <= teach_budget + 10 or s.is_required:
                    selected_set.add(s.id)
                    accumulated += s.est_minutes

        # 若過濾後太少頁，補齊最接近目標難度的題目直到接近預算
        if accumulated < teach_budget * 0.75:
            remaining = [
                s for s in candidates
                if s.id not in selected_set
            ]
            # 依與 target_difficulty 距離排序
            remaining.sort(
                key=lambda s: min(
                    abs(target_difficulty - s.min_difficulty),
                    abs(target_difficulty - s.max_difficulty),
                )
            )
            for s in remaining:
                if accumulated + s.est_minutes <= teach_budget + 8:
                    selected_set.add(s.id)
                    accumulated += s.est_minutes

    # 計算時間軸（僅針對已勾選的頁面排定時間軸；未勾選的標記為「未選入」）
    selected_slides = [s for s in ordered if s.id in selected_set]
    total_raw_min = sum(s.est_minutes for s in selected_slides) or 1

    # 決定中場休息點
    break_targets = []
    if duration_min >= 150:
        break_targets = [(duration_min // 3, 6), (2 * duration_min // 3, 7)]
    elif duration_min >= 100:
        break_targets = [(duration_min // 2, 5)]

    total_break_min = sum(b[1] for b in break_targets)
    avail_teach_min = max(30, duration_min - total_break_min)
    scale = avail_teach_min / total_raw_min

    # 計算每張已選 slide 的時段
    cursor = 0
    break_idx = 0
    slot_map = {}
    for idx, s in enumerate(selected_slides):
        if idx == len(selected_slides) - 1:
            # 最後一頁補齊剩餘時間（扣除尚未插入的休息）
            rem_breaks = sum(b[1] for b in break_targets[break_idx:])
            alloc = max(3, duration_min - rem_breaks - cursor)
        else:
            alloc = max(4, round(s.est_minutes * scale))
        start_str = _format_mm(cursor)
        cursor += alloc
        end_str = _format_mm(cursor)

        is_break_after = False
        break_label = ""
        if break_idx < len(break_targets):
            target_t, b_len = break_targets[break_idx]
            if cursor >= target_t and idx < len(selected_slides) - 1:
                b_start = _format_mm(cursor)
                cursor += b_len
                b_end = _format_mm(cursor)
                is_break_after = True
                break_label = f"中場休息 {b_len} 分鐘（{b_start}–{b_end}）"
                break_idx += 1

        slot_map[s.id] = {
            "time_slot": f"[{start_str}-{end_str}]",
            "allocated_minutes": alloc,
            "is_break_after": is_break_after,
            "break_label": break_label,
        }

    plan_items = []
    for s in ordered:
        is_sel = s.id in selected_set
        info = slot_map.get(
            s.id,
            {
                "time_slot": "[未排入]",
                "allocated_minutes": s.est_minutes,
                "is_break_after": False,
                "break_label": "",
            },
        )
        plan_items.append(
            {
                "slide": s,
                "selected": is_sel,
                **info,
            }
        )
    return plan_items


def _extract_page_numbers(page_ref: str) -> List[int]:
    import re
    return [int(n) for n in re.findall(r"\d+", page_ref or "")]


def build_range_lesson_plan(
    slides: List[Slide],
    target_difficulty: float,
    duration_min: int = 180,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
    categories: Optional[List[str]] = None,
    explicit_selected_ids: Optional[List[int]] = None,
) -> List[dict]:
    """
    依「跨單元 / 頁碼起訖 / 題型層級 / 目標難度 / 授課時長」範圍自動挑選板書並排定時段。
    """
    ordered = sorted(slides, key=lambda s: (s.unit_id, s.sort_order))

    filtered: List[Slide] = []
    for s in ordered:
        if categories and s.category not in categories:
            continue
        if page_start is not None or page_end is not None:
            nums = _extract_page_numbers(s.page_ref)
            if not nums:
                continue
            lo, hi = min(nums), max(nums)
            if page_start is not None and hi < page_start:
                continue
            if page_end is not None and lo > page_end:
                continue
        filtered.append(s)

    if not filtered:
        return []

    return build_lesson_plan(
        slides=filtered,
        target_difficulty=target_difficulty,
        duration_min=duration_min,
        start_from_slide_order=0,
        explicit_selected_ids=explicit_selected_ids,
    )

