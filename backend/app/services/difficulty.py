from dataclasses import dataclass


@dataclass
class DifficultyEvalResult:
    composite_score: float
    old_difficulty: float
    new_difficulty: float
    delta: float
    reason: str
    level_label: str


def get_difficulty_label(difficulty: float) -> str:
    if difficulty < 1.8:
        return "Lv.1 基礎穩固"
    if difficulty < 2.6:
        return "Lv.2 標準入門"
    if difficulty < 3.5:
        return "Lv.3 標準進階"
    if difficulty < 4.3:
        return "Lv.4 深度挑戰"
    return "Lv.5 資優壓軸"


def evaluate_next_difficulty(
    current_difficulty: float,
    score_comprehension: int,
    score_accuracy: int,
    score_completion: int,
    score_engagement: int,
    instructor_suggestion: str = "KEEP",
    previous_delta: float = 0.0,
) -> DifficultyEvalResult:
    """
    計算下一堂課建議難度係數：
    1. 綜合表現分數 S = 0.35*理解 + 0.25*正確率 + 0.25*進度完成 + 0.15*課堂節奏
    2. 基礎調整量 delta_raw = clamp(0.45 * (S - 3.0), -0.6, +0.6)
    3. 講師主觀建議微調：UP (+0.15) / DOWN (-0.15) / KEEP (0)
    4. 防震盪遲滯機制：
       - |delta| < 0.2 -> 維持現狀 (0.0)
       - 若與上次調整方向相反，衰減 30% 幅度
    5. 限制於 [1.0, 5.0]，四捨五入至小數點後 1 位
    """
    composite = (
        0.35 * score_comprehension
        + 0.25 * score_accuracy
        + 0.25 * score_completion
        + 0.15 * score_engagement
    )
    composite = round(composite, 2)

    raw_delta = max(-0.6, min(0.6, 0.45 * (composite - 3.0)))

    if instructor_suggestion == "UP":
        raw_delta += 0.15
    elif instructor_suggestion == "DOWN":
        raw_delta -= 0.15

    # 防震盪：反向調整衰減 30%
    if previous_delta != 0.0 and (raw_delta * previous_delta) < 0:
        raw_delta *= 0.7

    # 遲滯門檻：微小波動不調整
    if abs(raw_delta) < 0.2:
        final_delta = 0.0
    else:
        final_delta = round(raw_delta, 1)
        if final_delta == 0.0:
            final_delta = 0.2 if raw_delta > 0 else -0.2

    new_difficulty = round(max(1.0, min(5.0, current_difficulty + final_delta)), 1)
    actual_delta = round(new_difficulty - current_difficulty, 1)

    level_label = get_difficulty_label(new_difficulty)

    sug_map = {"UP": "講師建議升難度", "KEEP": "講師建議維持", "DOWN": "講師建議降難度"}
    sug_text = sug_map.get(instructor_suggestion, "講師建議維持")

    if actual_delta > 0:
        action_desc = f"建議難度由 {current_difficulty:.1f} 調升至 {new_difficulty:.1f}（+{actual_delta:.1f}），下堂將增加進階／資優題型比例。"
    elif actual_delta < 0:
        action_desc = f"建議難度由 {current_difficulty:.1f} 調降至 {new_difficulty:.1f}（{actual_delta:.1f}），下堂將加強基礎觀念與核心演練。"
    else:
        action_desc = f"表現落於穩定區間，維持難度係數 {new_difficulty:.1f} 不變。"

    reason = f"本堂綜合表現 {composite:.2f}/5.0（{sug_text}）。{action_desc}"

    return DifficultyEvalResult(
        composite_score=composite,
        old_difficulty=round(current_difficulty, 1),
        new_difficulty=new_difficulty,
        delta=actual_delta,
        reason=reason,
        level_label=level_label,
    )
