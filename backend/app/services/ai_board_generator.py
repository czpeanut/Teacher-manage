import base64
import io
import json
import os
import re
from pathlib import Path
from typing import List, Optional
import httpx
import pypdfium2 as pdfium
from app.schemas import SlideCreate

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

SYSTEM_PROMPT = """你是一位資深國小資優數學教研主任與板書設計師。
請將使用者上傳的數學教材頁面（圖片或文字），嚴格依照以下「A4 直式黑白印刷最佳化板書規格」轉換為結構化的 JSON 陣列。

【不可動搖的板書規格】
1. 頁面切分原則：一頁一個核心觀念或一題／一組代表性範例與演練。不要單純走流水帳，請依目標授課時長（2小時約 12~15 頁，3小時約 16~20 頁，若上傳頁數較少則依實際內容精煉產出）規劃清晰架構。
2. 上下雙層結構：
   - left_html（黑板左欄）：
     * 觀念頁必須用：<h1 class="board-title"># 觀念標題</h1> + <div class="board-sub">...</div>（極簡關鍵字與公式，不要長篇大論）。
     * 題目頁不可用 #，必須用：<div class="board-prob-title">P.XX 題號與簡稱</div> + <div class="eq-box">...</div>（精簡題幹條件）。
   - right_visual_html（黑板右欄）：
     * 放置算式推導步驟（<div class="eq-box">...</div>）或簡潔的黑白/雙色 <svg viewBox="0 0 320 115" xmlns="http://www.w3.org/2000/svg">...</svg>（如流程圖、線段圖、面積割補圖，字體清楚不重疊）。
   - footer_note_html（黑板右下角速解）：
     * 簡短一句速解口訣，例如：* 速解：見「剩下的」先畫流程圖，由最後結果往回逆推！
3. 黑白印刷三色粉筆雙重編碼 CSS（務必善用）：
   - 白粉筆（主幹／一般算式）：純黑文字。
   - 黃粉筆（重點字／關鍵步驟）：<span class="cy">重點內容</span>
   - 紅粉筆（最終答案／關鍵標記，不可大量寫字）：<span class="red-mark-box">答案</span> 或 <span class="red-underline">重點</span>
   - 直式分數格式：<span class="frac"><span class="num">分子</span><span class="den">分母</span></span>（嚴禁把分子分母拆成兩行純數字！）。
4. 下方備課區（寫給講師看的教學指引）：
   - guide_html：觀念引導（說明教學切入點、為何這樣教、如何建立直覺）。
   - points_list：字串陣列（1~3 條），補充口訣、學生常見迷思提醒、驗算方式或互動節奏。
   - pacing_tip：單行節奏應變提示（時間緊迫或超前時的取捨建議）。
5. 難度與分類欄位：
   - category 只能是："CONCEPT" | "DRILL" | "ADVANCED" | "GIFTED_A" | "GIFTED_B" | "GIFTED_C"
   - min_difficulty / max_difficulty：1.0 ~ 5.0 浮點數（CONCEPT 通常 1.0~5.0 且 is_required=true；DRILL 1.0~4.2；ADVANCED 2.2~5.0；GIFTED_A 2.8~5.0；GIFTED_B 3.4~5.0；GIFTED_C 4.2~5.0）
   - est_minutes：預估講解分鐘數（通常 6~12）。
   - 務必親自驗算所有數學算式與答案，確保 100% 正確！忽略教材頁首頁尾的書名與出版社雜訊。

【輸出格式要求】
只回傳純 JSON 陣列（不要包含 markdown ```json 標記以外的多餘文字），每個元素格式如下：
{
  "sort_order": 1,
  "badge_text": "觀念 1",
  "is_prob": false,
  "page_ref": "P.6",
  "category": "CONCEPT",
  "min_difficulty": 1.0,
  "max_difficulty": 5.0,
  "est_minutes": 10,
  "is_required": true,
  "left_html": "...",
  "right_visual_html": "...",
  "footer_note_html": "* 速解：...",
  "guide_html": "...",
  "points_list": ["...", "..."],
  "pacing_tip": "..."
}
"""


def load_saved_ai_config() -> dict:
    """從 .env 或環境變數讀取已設定的 AI 金鑰資訊（遮罩回傳）。"""
    env_vars = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

    gemini_key = os.environ.get("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY") or env_vars.get("OPENAI_API_KEY", "")
    return {
        "gemini_configured": bool(gemini_key),
        "openai_configured": bool(openai_key),
        "gemini_key": gemini_key,
        "openai_key": openai_key,
    }


def save_ai_key(provider: str, api_key: str) -> None:
    key_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
    lines = []
    if ENV_FILE.exists():
        lines = [
            ln for ln in ENV_FILE.read_text(encoding="utf-8").splitlines()
            if not ln.strip().startswith(f"{key_name}=")
        ]
    if api_key.strip():
        lines.append(f"{key_name}={api_key.strip()}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pdf_bytes_to_png_base64_list(pdf_bytes: bytes, max_pages: int = 20) -> List[str]:
    """將 PDF 每頁渲染為清晰 PNG base64，讓視覺模型直接看懂直式分數與圖形。"""
    doc = pdfium.PdfDocument(pdf_bytes)
    images_b64: List[str] = []
    try:
        total = min(len(doc), max_pages)
        for i in range(total):
            page = doc[i]
            bitmap = page.render(scale=1.8)
            pil_img = bitmap.to_pil()
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG", optimize=True)
            images_b64.append(base64.b64encode(buf.getvalue()).decode("ascii"))
            page.close()
    finally:
        doc.close()
    return images_b64


def _extract_json_array(raw_text: str) -> list:
    cleaned = raw_text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*\])\s*```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1)
    else:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


async def generate_slides_with_ai(
    unit_title: str,
    target_duration_min: int = 180,
    provider: str = "gemini",
    api_key: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None,
) -> List[SlideCreate]:
    cfg = load_saved_ai_config()
    effective_key = (api_key or "").strip()
    if not effective_key:
        effective_key = cfg["gemini_key"] if provider == "gemini" else cfg["openai_key"]

    if not effective_key:
        raise ValueError(f"尚未設定 {provider.upper()} API Key")

    images_b64: List[str] = []
    if pdf_bytes:
        images_b64 = pdf_bytes_to_png_base64_list(pdf_bytes)

    user_prompt = (
        f"單元名稱：{unit_title}\n"
        f"目標授課時長：{target_duration_min} 分鐘\n"
        f"請將附上的教材內容轉換成高品質的 A4 黑白印刷板書備課 JSON 陣列。"
    )
    if raw_text and raw_text.strip():
        user_prompt += f"\n\n教材文字內容如下：\n{raw_text.strip()}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        if provider == "gemini":
            parts: list = [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt}]
            for b64 in images_b64:
                parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})

            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.5-flash:generateContent?key={effective_key}"
            )
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            }
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API 錯誤 ({resp.status_code}): {resp.text[:300]}")
            data = resp.json()
            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
        elif provider == "openai":
            content_list: list = [{"type": "text", "text": user_prompt}]
            for b64 in images_b64:
                content_list.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}}
                )
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {effective_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": content_list},
                    ],
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API 錯誤 ({resp.status_code}): {resp.text[:300]}")
            data = resp.json()
            text_out = data["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"不支援的 AI 供應商: {provider}")

    items = _extract_json_array(text_out)
    slides: List[SlideCreate] = []
    for idx, item in enumerate(items, start=1):
        slides.append(
            SlideCreate(
                sort_order=int(item.get("sort_order", idx)),
                badge_text=str(item.get("badge_text", f"頁 {idx}"))[:60],
                is_prob=bool(item.get("is_prob", False)),
                page_ref=str(item.get("page_ref", ""))[:60],
                category=str(item.get("category", "CONCEPT")),
                min_difficulty=float(item.get("min_difficulty", 1.0)),
                max_difficulty=float(item.get("max_difficulty", 5.0)),
                est_minutes=int(item.get("est_minutes", 10)),
                is_required=bool(item.get("is_required", False)),
                left_html=str(item.get("left_html", "")),
                right_visual_html=str(item.get("right_visual_html", "")),
                footer_note_html=str(item.get("footer_note_html", "")),
                guide_html=str(item.get("guide_html", "")),
                points_list=[str(p) for p in item.get("points_list", [])],
                pacing_tip=str(item.get("pacing_tip", ""))[:250],
            )
        )
    return slides
