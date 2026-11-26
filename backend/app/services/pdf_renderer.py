import html
from datetime import datetime
from pathlib import Path
from typing import List
from playwright.sync_api import sync_playwright
import pypdfium2 as pdfium
from app.config import settings

# 嚴格保留原 chalkboard_kit_bw.py 黑白印刷三色粉筆雙重編碼規格，並加入 6 項工程與樣式改進
CHALKBOARD_CSS = r"""
    :root {
      --cw: #111827;       /* 白粉筆 -> 純黑實字實線 (主幹/數字/算式) */
      --cy: #B45309;       /* 黃粉筆 -> 淺灰網底 + 虛線底線 (黑白列印清楚區分) */
      --cr: #DC2626;       /* 紅粉筆 -> 雙線框/雙底線/實心點 (僅作標記，不大量寫字) */
      --board-border: #111827;
    }

    @page {
      size: A4 portrait;
      margin: 14mm 16mm 15mm 16mm;
      background: #FFFFFF;
    }

    *, *::before, *::after { box-sizing: border-box; }

    html, body {
      margin: 0;
      padding: 0;
      background: #FFFFFF;
      font-family: 'Noto Sans CJK TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
      font-size: 11.5pt;
      line-height: 1.6;
      color: var(--cw);
      font-variant-numeric: tabular-nums;
    }

    main.document-flow { width: 100%; margin: 0; padding: 0; }

    .slide {
      width: 100%;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      gap: 15px;
      page-break-after: always;
      break-after: page;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .slide:last-child { page-break-after: auto; break-after: auto; }

    /* 封面備課總覽頁 */
    .cover-header {
      border-bottom: 3px solid #111827;
      padding-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .cover-title {
      font-size: 21pt;
      font-weight: 800;
      margin: 0;
      line-height: 1.25;
    }
    .cover-sub {
      font-size: 10.5pt;
      color: #475569;
      font-weight: 700;
    }
    .cover-meta-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }
    .cover-card {
      border: 2px solid #111827;
      border-radius: 8px;
      padding: 8px 10px;
      background: #F8FAFC;
    }
    .cover-card-label {
      font-size: 8.5pt;
      color: #475569;
      font-weight: 700;
    }
    .cover-card-val {
      font-size: 12.5pt;
      font-weight: 800;
      color: #111827;
      margin-top: 2px;
    }
    .cover-box {
      border: 1.5px solid #334155;
      border-left: 5px solid #111827;
      border-radius: 8px;
      padding: 10px 14px;
      background: #FFFFFF;
      font-size: 10.5pt;
    }
    .cover-box-title {
      font-weight: 800;
      font-size: 11pt;
      margin-bottom: 4px;
      color: #0F172A;
    }
    .schedule-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 9.8pt;
    }
    .schedule-table th, .schedule-table td {
      border: 1px solid #94A3B8;
      padding: 4px 8px;
      text-align: left;
    }
    .schedule-table th {
      background: #E2E8F0;
      font-weight: 800;
    }
    .schedule-break-row td {
      background: #F1F5F9;
      font-weight: 800;
      text-align: center;
      border-top: 1.5px dashed #475569;
      border-bottom: 1.5px dashed #475569;
    }

    /* 改良版頁眉：緊湊防擁擠 + 難度標籤 */
    .page-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 9pt;
      white-space: nowrap;
      color: #334155;
      border-bottom: 1.5px solid #94A3B8;
      padding-bottom: 6px;
      gap: 8px;
    }
    .meta-left {
      display: flex;
      align-items: center;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .meta-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .meta-badge {
      background: #111827;
      color: #FFFFFF;
      font-weight: 700;
      padding: 2px 9px;
      border-radius: 4px;
      margin-right: 8px;
    }
    .meta-badge-prob {
      background: #FFFFFF;
      color: #111827;
      border: 2px solid #111827;
      font-weight: 800;
      padding: 1px 8px;
      border-radius: 4px;
      margin-right: 8px;
    }
    .diff-pill {
      border: 1.5px solid #334155;
      border-radius: 4px;
      padding: 1px 6px;
      font-size: 8.5pt;
      font-weight: 800;
      background: #F8FAFC;
      color: #111827;
    }
    .legend {
      display: flex;
      gap: 6px;
      font-weight: 700;
      font-size: 8.5pt;
      white-space: nowrap;
      align-items: center;
    }

    .blackboard {
      border: 4px solid var(--board-border);
      border-bottom: 7px solid #334155;
      border-radius: 16px;
      background: #FFFFFF;
      padding: 20px 26px 24px 26px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    }

    .board-grid {
      display: grid;
      grid-template-columns: 44% 53%;
      gap: 3%;
      align-items: stretch;
    }

    .board-title {
      font-size: 20pt;
      font-weight: 800;
      color: var(--cw);
      margin: 0 0 14px 0;
      letter-spacing: 0.02em;
      line-height: 1.25;
    }
    .board-prob-title {
      font-size: 15.5pt;
      font-weight: 800;
      color: var(--cw);
      margin: 0 0 12px 0;
      letter-spacing: 0.02em;
    }

    .board-sub {
      font-size: 13pt;
      font-weight: 700;
      line-height: 1.85;
    }
    .board-sub div { margin-bottom: 6px; }

    .cy {
      color: var(--cy);
      background: #F1F5F9;
      padding: 0 4px;
      border-radius: 3px;
      border-bottom: 2px dashed var(--cy);
      font-weight: 800;
    }
    .red-mark-box {
      color: #111827;
      border: 3px double var(--cr);
      border-radius: 6px;
      padding: 1px 8px;
      display: inline-block;
      font-weight: 800;
    }
    .red-underline {
      border-bottom: 3.5px double var(--cr);
      padding-bottom: 1px;
    }
    .red-star { color: var(--cr); font-weight: 800; }

    .board-right {
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 12px;
      height: 100%;
    }
    .board-dashed-hr {
      border: none;
      border-top: 2px dashed #475569;
      margin: 2px 0 8px 0;
    }
    .board-footer-note {
      text-align: center;
      font-size: 12pt;
      font-weight: 800;
      color: var(--cy);
      background: #F8FAFC;
      border: 1.5px dashed #64748B;
      border-radius: 6px;
      padding: 5px 10px;
      line-height: 1.45;
    }

    .eq-box {
      font-size: 13.5pt;
      font-weight: 700;
      line-height: 1.9;
    }

    .frac {
      display: inline-flex;
      flex-direction: column;
      vertical-align: middle;
      text-align: center;
      font-size: 0.84em;
      line-height: 1.05;
      margin: 0 3px;
      position: relative;
      top: -2px;
    }
    .frac > span.num {
      border-bottom: 1.6px solid currentColor;
      padding: 0 4px 1px 4px;
      display: block;
    }
    .frac > span.den {
      padding: 1px 4px 0 4px;
      display: block;
    }

    .teaching-notes {
      background: #F8FAFC;
      border: 1.5px solid #CBD5E1;
      border-left: 5px solid #1E293B;
      border-radius: 10px;
      padding: 14px 20px;
      font-size: 11pt;
      line-height: 1.65;
      color: #1E293B;
    }
    .note-block { margin-bottom: 10px; }
    .note-block:last-child { margin-bottom: 0; }
    .note-label {
      font-weight: 800;
      color: #0F172A;
      font-size: 12pt;
      margin-bottom: 4px;
      display: inline-block;
      border-bottom: 2px solid #94A3B8;
      padding-bottom: 1px;
    }
    .note-list { margin: 4px 0 0 0; padding-left: 20px; }
    .note-list li { margin-bottom: 4px; }

    .pacing-tip-bar {
      margin-top: 8px;
      padding-top: 6px;
      border-top: 1px dashed #94A3B8;
      font-size: 10pt;
      font-weight: 700;
      color: #334155;
    }

    .break-banner {
      border: 2px dashed #111827;
      border-radius: 8px;
      background: #F1F5F9;
      padding: 7px 14px;
      text-align: center;
      font-weight: 800;
      font-size: 11pt;
      color: #111827;
      letter-spacing: 0.03em;
    }

    .mini-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11pt;
      font-weight: 700;
      text-align: center;
    }
    .mini-table th, .mini-table td {
      border: 1.5px solid #334155;
      padding: 4px 6px;
    }
    .mini-table th {
      background: #E2E8F0;
      color: #111827;
    }

    svg { display: block; width: 100%; height: auto; }
"""

COMPACT_LEGEND_HTML = """
      <div class="legend">
        <span>■白粉筆</span>
        <span style="color:#B45309; background:#F1F5F9; padding:0 3px; border-bottom:2px dashed #B45309;">▲黃(重點)</span>
        <span style="color:#DC2626; border:2px double #DC2626; padding:0 3px; border-radius:4px;">●紅(標記)</span>
      </div>
"""

CATEGORY_BADGE = {
    "CONCEPT": "核心觀念",
    "DRILL": "基礎演練",
    "ADVANCED": "進階挑戰",
    "GIFTED_A": "資優 A",
    "GIFTED_B": "資優 B",
    "GIFTED_C": "資優壓軸",
}


def build_cover_slide_html(
    class_name: str,
    instructor_name: str,
    unit_title: str,
    target_difficulty: float,
    difficulty_label: str,
    duration_min: int,
    admin_note: str,
    last_lesson_notes: str,
    selected_items: List[dict],
) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    rows_html = []
    for idx, item in enumerate(selected_items, start=1):
        s = item["slide"]
        cat_label = CATEGORY_BADGE.get(s.category, s.category)
        rows_html.append(
            f"<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(item['time_slot'])}</td>"
            f"<td><strong>{html.escape(s.badge_text)}</strong></td>"
            f"<td>{html.escape(s.page_ref or '-')}</td>"
            f"<td>{html.escape(cat_label)}</td>"
            f"<td>{item['allocated_minutes']} 分</td>"
            f"</tr>"
        )
        if item.get("is_break_after") and item.get("break_label"):
            rows_html.append(
                f'<tr class="schedule-break-row"><td colspan="6">☕ {html.escape(item["break_label"])}</td></tr>'
            )

    notes_blocks = []
    if admin_note:
        notes_blocks.append(
            f'<div class="cover-box"><div class="cover-box-title">📌 管理員教學指示</div><div>{html.escape(admin_note)}</div></div>'
        )
    if last_lesson_notes:
        notes_blocks.append(
            f'<div class="cover-box"><div class="cover-box-title">📝 上堂課後回報備註</div><div>{html.escape(last_lesson_notes)}</div></div>'
        )
    if not notes_blocks:
        notes_blocks.append(
            '<div class="cover-box"><div class="cover-box-title">📌 備課檢核提醒</div><div>請依頁眉時段控管節奏，板書保持極簡留白，速解法統一書寫於黑板右下角。</div></div>'
        )

    return f"""
  <div class="slide">
    <div class="cover-header">
      <div>
        <div class="cover-sub">A4 黑白印刷最佳化｜教師備課總覽頁</div>
        <h1 class="cover-title">{html.escape(unit_title)}</h1>
      </div>
      <div class="cover-sub">產出日期：{today_str}</div>
    </div>

    <div class="cover-meta-grid">
      <div class="cover-card">
        <div class="cover-card-label">授課班級 / 講師</div>
        <div class="cover-card-val">{html.escape(class_name)}（{html.escape(instructor_name)}）</div>
      </div>
      <div class="cover-card">
        <div class="cover-card-label">目標難度係數</div>
        <div class="cover-card-val">{target_difficulty:.1f} / 5.0（{html.escape(difficulty_label)}）</div>
      </div>
      <div class="cover-card">
        <div class="cover-card-label">課程總時長</div>
        <div class="cover-card-val">{duration_min} 分鐘</div>
      </div>
      <div class="cover-card">
        <div class="cover-card-label">本份板書頁數</div>
        <div class="cover-card-val">共 {len(selected_items)} 頁</div>
      </div>
    </div>

    {''.join(notes_blocks)}

    <div>
      <div class="cover-box-title" style="margin-bottom:6px;">⏱ 本堂課堂時段與板書目錄</div>
      <table class="schedule-table">
        <thead>
          <tr>
            <th style="width:42px;">頁序</th>
            <th style="width:105px;">建議時段</th>
            <th style="width:110px;">板書徽章</th>
            <th>教材頁碼 / 主題</th>
            <th style="width:82px;">題型層級</th>
            <th style="width:62px;">預估</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
  </div>
"""


def build_slide_html(item: dict, unit_title: str) -> str:
    s = item["slide"]
    badge_cls = "meta-badge-prob" if s.is_prob else "meta-badge"
    cat_label = CATEGORY_BADGE.get(s.category, s.category)
    header_text = f"{unit_title}（{s.page_ref}）｜{item['time_slot']}" if s.page_ref else f"{unit_title}｜{item['time_slot']}"

    footer_block = ""
    if s.footer_note_html:
        footer_block = f"""
          <hr class="board-dashed-hr">
          <div class="board-footer-note">{s.footer_note_html}</div>"""

    pts_li = "\n".join(f"          <li>{p}</li>" for p in (s.points_list or []))
    pacing_block = ""
    if s.pacing_tip:
        pacing_block = f'<div class="pacing-tip-bar">⚡ 節奏應變提示：{html.escape(s.pacing_tip)}</div>'

    break_banner = ""
    if item.get("is_break_after") and item.get("break_label"):
        break_banner = f'<div class="break-banner">☕ {html.escape(item["break_label"])}</div>'

    return f"""
  <div class="slide">
    <div class="page-meta">
      <div class="meta-left"><span class="{badge_cls}">{html.escape(s.badge_text)}</span><span>{html.escape(header_text)}</span></div>
      <div class="meta-right">
        <span class="diff-pill">{html.escape(cat_label)}</span>
        {COMPACT_LEGEND_HTML}
      </div>
    </div>

    <div class="blackboard">
      <div class="board-grid">
        <div>
          {s.left_html}
        </div>
        <div class="board-right">
          {s.right_visual_html}{footer_block}
        </div>
      </div>
    </div>

    <div class="teaching-notes">
      <div class="note-block">
        <div class="note-label">觀念引導</div>
        <div>{s.guide_html}</div>
      </div>
      <div class="note-block">
        <div class="note-label">講解重點</div>
        <ul class="note-list">
{pts_li}
        </ul>
      </div>
      {pacing_block}
    </div>
    {break_banner}
  </div>
"""


def build_full_document_html(
    doc_title: str,
    class_name: str,
    instructor_name: str,
    unit_title: str,
    target_difficulty: float,
    difficulty_label: str,
    duration_min: int,
    include_cover: bool,
    admin_note: str,
    last_lesson_notes: str,
    selected_items: List[dict],
) -> str:
    slides_html = []
    if include_cover:
        slides_html.append(
            build_cover_slide_html(
                class_name=class_name,
                instructor_name=instructor_name,
                unit_title=unit_title,
                target_difficulty=target_difficulty,
                difficulty_label=difficulty_label,
                duration_min=duration_min,
                admin_note=admin_note,
                last_lesson_notes=last_lesson_notes,
                selected_items=selected_items,
            )
        )
    for item in selected_items:
        slides_html.append(build_slide_html(item, unit_title))

    body = "\n".join(slides_html)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>{html.escape(doc_title)}</title>
  <style>{CHALKBOARD_CSS}</style>
</head>
<body>
<main class="document-flow">
{body}
</main>
</body>
</html>
"""


def render_html_to_pdf(full_html: str, output_pdf_path: Path) -> int:
    """
    使用 Playwright + 系統 Google Chrome 進行併發安全的 A4 PDF 渲染，
    並透過 display_header_footer 確保精準頁碼 (第 X / N 頁)。
    回傳實際 PDF 頁數。
    """
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    footer_template = (
        '<div style="width:100%; font-size:9px; color:#475569; '
        'font-family:\'Noto Sans CJK TC\',sans-serif; text-align:right; padding-right:16mm;">'
        '第 <span class="pageNumber"></span> / <span class="totalPages"></span> 頁'
        '</div>'
    )
    header_template = '<div></div>'

    with sync_playwright() as p:
        executable = settings.CHROME_EXECUTABLE_PATH if Path(settings.CHROME_EXECUTABLE_PATH).exists() else None
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        }
        if executable:
            launch_kwargs["executable_path"] = executable

        browser = p.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page()
            page.set_content(full_html, wait_until="load")
            page.pdf(
                path=str(output_pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=header_template,
                footer_template=footer_template,
                margin={
                    "top": "14mm",
                    "right": "16mm",
                    "bottom": "15mm",
                    "left": "16mm",
                },
            )
        finally:
            browser.close()

    doc = pdfium.PdfDocument(str(output_pdf_path))
    page_count = len(doc)
    doc.close()
    return page_count
