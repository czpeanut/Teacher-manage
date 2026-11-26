import html
import re
from dataclasses import dataclass
from typing import List, Tuple
import pypdfium2 as pdfium


@dataclass
class ParsedSlideDraft:
    sort_order: int
    badge_text: str
    is_prob: bool
    page_ref: str
    category: str
    min_difficulty: float
    max_difficulty: float
    est_minutes: int
    is_required: bool
    left_html: str
    right_visual_html: str
    footer_note_html: str
    guide_html: str
    points_list: List[str]
    pacing_tip: str


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """使用 pypdfium2 逐頁擷取 PDF 文字內容，回傳 [(頁碼, 文字), ...]。"""
    doc = pdfium.PdfDocument(pdf_bytes)
    pages: List[Tuple[int, str]] = []
    try:
        for idx in range(len(doc)):
            page = doc[idx]
            textpage = page.get_textpage()
            text = textpage.get_text_range() or ""
            textpage.close()
            page.close()
            if text.strip():
                pages.append((idx + 1, text.strip()))
    finally:
        doc.close()
    return pages


def _detect_category_and_diff(header: str, body: str) -> Tuple[str, bool, float, float, bool]:
    combined = f"{header} {body}"
    if any(k in combined for k in ["壓軸", "C組", "C1", "C2"]):
        return "GIFTED_C", True, 4.2, 5.0, False
    if any(k in combined for k in ["資優B", "B組", "B1", "B2", "B3"]):
        return "GIFTED_B", True, 3.4, 5.0, False
    if any(k in combined for k in ["資優", "A組", "A1", "A2"]):
        return "GIFTED_A", True, 2.8, 5.0, False
    if any(k in combined for k in ["進階", "挑戰"]):
        return "ADVANCED", True, 2.2, 5.0, False
    if any(k in combined for k in ["演練", "練習", "範例", "例題", "題型"]):
        return "DRILL", True, 1.0, 4.5, False
    return "CONCEPT", False, 1.0, 5.0, True


def _extract_page_ref(text: str, fallback_page: int) -> str:
    m = re.search(r"[Pp]\.?\s*(\d+(?:\s*[-~～]\s*\d+)?)", text)
    if m:
        return f"P.{m.group(1).replace(' ', '')}"
    return f"P.{fallback_page}"


def _highlight_keywords(line: str) -> str:
    escaped = html.escape(line.strip())
    # 將常見速解關鍵字或等號後答案加上黑白印刷雙重編碼
    escaped = re.sub(
        r"(關鍵|重點|注意|公式|性質|速解|技巧|倍數|餘數|分配律)",
        r'<span class="cy">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"(＝|=)\s*([0-9]+(?:\.[0-9]+)?)\s*$",
        r'\1 <span class="red-mark-box">\2</span>',
        escaped,
    )
    return escaped


def parse_material_to_slides(
    raw_sections: List[Tuple[int, str]],
    unit_title: str = "",
) -> List[ParsedSlideDraft]:
    """
    將擷取出的教材文字段落，自動切分並套用 A4 黑白印刷三色粉筆規格，
    組成可直接匯入資料庫的板書 Slide 草稿。
    """
    blocks: List[Tuple[int, str]] = []
    section_splitter = re.compile(
        r"(?=(?:^|\n)\s*(?:觀念\s*\d+|重點\s*\d+|例題\s*\d+|題型演練|演練\s*\d+|進階挑戰|資優挑戰|壓軸挑戰))",
        re.MULTILINE,
    )

    for page_no, text in raw_sections:
        parts = [p.strip() for p in section_splitter.split(text) if p.strip()]
        if not parts:
            continue
        for p in parts:
            blocks.append((page_no, p))

    if not blocks:
        return []

    drafts: List[ParsedSlideDraft] = []
    concept_idx = 1
    drill_idx = 1

    for idx, (page_no, block_text) in enumerate(blocks, start=1):
        lines = [ln.strip() for ln in block_text.splitlines() if ln.strip()]
        if not lines:
            continue

        title_line = lines[0][:40]
        body_lines = lines[1:] if len(lines) > 1 else [lines[0]]
        page_ref = _extract_page_ref(block_text, page_no)
        cat, is_prob, min_d, max_d, is_req = _detect_category_and_diff(title_line, block_text)

        if cat == "CONCEPT":
            badge_text = f"觀念 {concept_idx}"
            concept_idx += 1
        elif cat == "DRILL":
            badge_text = f"演練 {page_ref}"
            drill_idx += 1
        elif cat == "ADVANCED":
            badge_text = f"進階 {page_ref}"
        elif cat == "GIFTED_A":
            badge_text = f"資優 A {page_ref}"
        elif cat == "GIFTED_B":
            badge_text = f"資優 B {page_ref}"
        else:
            badge_text = f"壓軸 {page_ref}"

        # 分離題幹／觀念（左欄）與算式／解析（右欄）
        left_lines = []
        right_lines = []
        footer_note = ""
        guide_lines = []

        for ln in body_lines:
            if any(k in ln for k in ["速解", "口訣", "小撇步"]):
                footer_note = f"* {html.escape(ln)}"
            elif any(k in ln for k in ["提醒", "引導", "迷思", "注意"]):
                guide_lines.append(ln)
            elif re.search(r"[=＝÷×+\-−]|答[:：]|解[:：]", ln) and len(right_lines) < 5:
                right_lines.append(ln)
            elif len(left_lines) < 5:
                left_lines.append(ln)
            else:
                right_lines.append(ln)

        if not left_lines:
            left_lines = body_lines[:3]
        if not right_lines:
            right_lines = body_lines[3:6] if len(body_lines) > 3 else ["（課堂板書推導區：請依學生反應現場列式）"]

        if is_prob:
            left_html = (
                f'<div class="board-prob-title">{html.escape(page_ref)} {html.escape(title_line)}</div>\n'
                f'          <div class="eq-box">\n'
                + "\n".join(f"            <div>{html.escape(l)}</div>" for l in left_lines)
                + "\n          </div>"
            )
        else:
            clean_title = title_line.lstrip("# ").strip()
            left_html = (
                f'<h1 class="board-title"># {html.escape(clean_title)}</h1>\n'
                f'          <div class="board-sub">\n'
                + "\n".join(f"            <div>{_highlight_keywords(l)}</div>" for l in left_lines)
                + "\n          </div>"
            )

        right_visual_html = (
            '<div class="eq-box">\n'
            + "\n".join(f"            <div>{_highlight_keywords(l)}</div>" for l in right_lines)
            + "\n          </div>"
        )

        if not footer_note:
            footer_note = "* 速解：先圈出題目關鍵條件，再套用本節核心性質"

        guide_html = (
            html.escape("；".join(guide_lines))
            if guide_lines
            else f"由「{html.escape(title_line)}」切入，先建立直覺再帶入板書例題。"
        )
        points_list = [
            f"核對教材 {page_ref} 重點，確認學生理解核心步驟。",
            "板書採極簡手寫字量，黃粉筆標出關鍵詞、紅粉筆雙框標記最終結論。",
        ]
        est_minutes = 10 if cat in ("CONCEPT", "DRILL") else 8
        pacing_tip = (
            "時間緊迫時可口頭帶過基礎題，保留時間給關鍵例題。"
            if is_prob
            else "基礎班可放慢節奏並多舉一組生活化數字例。"
        )

        drafts.append(
            ParsedSlideDraft(
                sort_order=idx,
                badge_text=badge_text[:60],
                is_prob=is_prob,
                page_ref=page_ref[:60],
                category=cat,
                min_difficulty=min_d,
                max_difficulty=max_d,
                est_minutes=est_minutes,
                is_required=is_req,
                left_html=left_html,
                right_visual_html=right_visual_html,
                footer_note_html=footer_note,
                guide_html=guide_html,
                points_list=points_list,
                pacing_tip=pacing_tip,
            )
        )

    return drafts
