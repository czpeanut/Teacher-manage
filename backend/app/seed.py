from sqlalchemy.orm import Session
from app.auth import get_password_hash
from app.models import ClassGroup, DifficultyHistory, Slide, Unit, User


G5_CH9_SLIDES = [
    {
        "sort_order": 1,
        "badge_text": "觀念 1",
        "is_prob": False,
        "page_ref": "P.68",
        "category": "CONCEPT",
        "min_difficulty": 1.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<h1 class="board-title"># 乘法拆數與分配巧算</h1>
          <div class="board-sub">
            <div><span class="cy">拆數分配</span>：近整十/百/千</div>
            <div>&nbsp;&nbsp;99 → <span class="red-mark-box">100 − 1</span>、102 → <span class="red-mark-box">100 + 2</span></div>
            <div><span class="cy">公因數提取</span>（反向分配）：</div>
            <div>&nbsp;&nbsp;甲×乙 ＋ 甲×丙 ＝ 甲×(乙＋丙)</div>
          </div>""",
        "right_visual_html": """<svg viewBox="0 0 320 115" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="22" width="210" height="54" fill="#F1F5F9" stroke="#111827" stroke-width="2.5"/>
            <rect x="230" y="22" width="38" height="54" fill="none" stroke="#DC2626" stroke-width="2" stroke-dasharray="5,3"/>
            <text x="125" y="45" text-anchor="middle" font-size="13" font-weight="800" fill="#111827">48 × 99</text>
            <text x="125" y="65" text-anchor="middle" font-size="12" font-weight="700" fill="#B45309">= 4800 − 48 = 4752</text>
            <text x="249" y="53" text-anchor="middle" font-size="11" font-weight="800" fill="#DC2626">−48×1</text>
            <text x="160" y="102" text-anchor="middle" font-size="12.5" font-weight="800" fill="#111827">先畫「長 100、寬 48」大長方形，再剪掉寬 1 邊條</text>
          </svg>""",
        "footer_note_html": "* 速解：見 99 / 999 拆成 (整百/千 − 1)；見重複乘數先圈起來",
        "guide_html": "用面積割補圖建立乘法分配律的幾何直覺，學生就不會把 48×99 誤算成 48×100 − 1。",
        "points_list": [
            "口頭帶算 P.68 例題：48×99=4752、35×102=3570、64×37+64×63=6400。",
            "黑白印刷區分提醒：板書上黃粉筆重點字採「灰底＋虛線底線」，紅粉筆標記採「雙線框／雙底線」。",
        ],
        "pacing_tip": "高難度班級可 6 分鐘快速帶過，基礎班級建議多畫一組長方形面積圖。",
    },
    {
        "sort_order": 2,
        "badge_text": "觀念/演練",
        "is_prob": True,
        "page_ref": "P.68-70 分配律實戰",
        "category": "DRILL",
        "min_difficulty": 1.0,
        "max_difficulty": 4.2,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<div class="board-prob-title">P.69-70 演練 1、3、4</div>
          <div class="eq-box">
            <div>1. 999 × 88 = ?</div>
            <div>3. 45 × 10.2 = ?</div>
            <div>4. 57×36 + 57×65 − 57 = ?</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. (<span class="cy">1000 − 1</span>)×88 = 88000 − 88 = <span class="red-mark-box">87912</span></div>
            <div>3. 45×(<span class="cy">10 + 0.2</span>) = 450 + 9 = <span class="red-mark-box">459</span></div>
            <div>4. 57×(36 + 65 − <span class="red-underline">1</span>) = 57×100 = <span class="red-mark-box">5700</span></div>
          </div>""",
        "footer_note_html": "* 速解：單獨一個「− 57」要看成「− 57 × 1」，提出後留 1！",
        "guide_html": "觀念題型 P.68-69（2475, 7272, 3800, 8500）先讓學生搶答暖身，重點講解演練 4 的隱形係數 ×1。",
        "points_list": [
            "90% 學生在演練 4 會把 −57 直接忽略成 0，務必用雙線底線標出 × 1。",
        ],
        "pacing_tip": "進度超前可追問「57×99 + 57 = ?」強化隱形 ×1 概念。",
    },
    {
        "sort_order": 3,
        "badge_text": "觀念 2",
        "is_prob": False,
        "page_ref": "P.70",
        "category": "CONCEPT",
        "min_difficulty": 1.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<h1 class="board-title"># 特別數的乘法速算</h1>
          <div class="board-sub">
            <div>① <span class="cy">× 25</span> ＝ × 100 ÷ 4</div>
            <div>② <span class="cy">× 125</span> ＝ × 1000 ÷ 8</div>
            <div>③ <span class="cy">× 11</span>：兩頭一拉，中間相加</div>
            <div>④ <span class="cy">頭同尾合十</span>：</div>
            <div>&nbsp;&nbsp;&nbsp;頭×(頭+1) 放前，<span class="red-underline">尾×尾</span>放後(兩位)</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>例：68 × 11 = 6 <span class="cy">(6+8=14進1)</span> 8 = <span class="red-mark-box">748</span></div>
            <div style="margin-top:8px;">例：64 × 66（頭同6，4+6=10）</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;前：<span class="cy">6×7 = 42</span>；後：4×6 = 24 → <span class="red-mark-box">4224</span></div>
          </div>""",
        "footer_note_html": "* 速解：尾×尾若只有一位數（如 1×9=9），十位必須「補 0」寫 09！",
        "guide_html": "這四招是小學奧數與國一計算提速核心，特別要注意 ×11 滿十進位以及「頭同尾合十」末兩位補零規則。",
        "points_list": [
            "帶學生檢查 P.71 觀念題型：48×25=1200、72×125=9000、53×11=583、64×66=4224。",
        ],
        "pacing_tip": "可讓學生上台搶答 41×49（檢驗是否補 0 成 2009）。",
    },
    {
        "sort_order": 4,
        "badge_text": "演練 P.72",
        "is_prob": True,
        "page_ref": "P.72 特別數乘法演練",
        "category": "DRILL",
        "min_difficulty": 1.0,
        "max_difficulty": 4.2,
        "est_minutes": 12,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.72 演練 1~4</div>
          <div class="eq-box">
            <div>1. 32 × 125 × 25</div>
            <div>2. 97 × 11 &nbsp;&nbsp; 3. 81 × 89</div>
            <div>4. 24×25 + 36×125</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. (<span class="cy">8×4</span>)×125×25 = (8×125)×(4×25) = <span class="red-mark-box">100000</span></div>
            <div>2. 97×11 = 9 <span class="cy">(16進1)</span> 7 = <span class="red-mark-box">1067</span></div>
            <div>3. 81×89：8×9=72，1×9=<span class="red-underline">09</span> → <span class="red-mark-box">7209</span></div>
            <div>4. 600 + 4500 = <span class="red-mark-box">5100</span></div>
          </div>""",
        "footer_note_html": "* 速解：見 25 拆 4、見 125 拆 8；81×89 末兩位寫 09 不寫 9",
        "guide_html": "演練 4 讓學生體會拆數轉除法的快感：24÷4=6 補兩個 0 得 600；36÷8 除不盡？拆成 9×(4×125) = 9×500 = 4500！",
        "points_list": [
            "點醒 36×125：36 不能整除 8，改拆成 9 × 4 × 125 = 9 × 500 = 4500（靈活拆 4 配 125 得 500）！",
        ],
        "pacing_tip": "高難度班可跳過第 2 題，集中練第 1 與第 4 題。",
    },
    {
        "sort_order": 5,
        "badge_text": "觀念 3",
        "is_prob": False,
        "page_ref": "P.73",
        "category": "CONCEPT",
        "min_difficulty": 1.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<h1 class="board-title"># 商不變性質與連除</h1>
          <div class="board-sub">
            <div><span class="cy">商不變</span>：被除數與除數同乘/除 c（c≠0）</div>
            <div>&nbsp;&nbsp;÷ 25 → <span class="red-mark-box">同乘 4</span>（變 ÷100）</div>
            <div>&nbsp;&nbsp;÷ 125 → <span class="red-mark-box">同乘 8</span>（變 ÷1000）</div>
            <div><span class="cy">連除化乘</span>：甲 ÷ 乙 ÷ 丙 ＝ 甲 ÷ (乙×丙)</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>例 1：450 ÷ 25 = (450<span class="cy">×4</span>) ÷ (25<span class="cy">×4</span>)</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= 1800 ÷ 100 = <span class="red-mark-box">18</span></div>
            <div style="margin-top:6px;">例 2：3500 ÷ 125 = (3500<span class="cy">×8</span>) ÷ 1000 = <span class="red-mark-box">28</span></div>
          </div>""",
        "footer_note_html": "* 速解：除法看到 25 或 125，不要硬列長除法，同乘 4 或 8 湊百千！",
        "guide_html": "解釋原理：除法就是分數，被除數與除數同乘以 4 其實就是「擴分」，數值完全不變。",
        "points_list": [
            "口頭完成 P.73-74 觀念題型：720÷24÷3 = 10（或先 720÷3÷24）、640÷16 = 640÷8÷2 = 40。",
        ],
        "pacing_tip": "強調「有餘數時商不變但餘數會跟著放大」的伏筆（進階 7 會用到）。",
    },
    {
        "sort_order": 6,
        "badge_text": "演練 P.74",
        "is_prob": True,
        "page_ref": "P.74-75 連除簡算",
        "category": "DRILL",
        "min_difficulty": 1.0,
        "max_difficulty": 4.0,
        "est_minutes": 10,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.74-75 演練 1~4</div>
          <div class="eq-box">
            <div>1. 5600 ÷ 25 ÷ 4</div>
            <div>2. 8100 ÷ 18 ÷ 5</div>
            <div>3. 9000 ÷ 125 &nbsp;&nbsp; 4. 1200 ÷ (24×5)</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. 5600 ÷ (<span class="cy">25×4</span>) = 5600 ÷ 100 = <span class="red-mark-box">56</span></div>
            <div>2. 8100 ÷ (<span class="cy">18×5</span>) = 8100 ÷ 90 = <span class="red-mark-box">90</span></div>
            <div>3. (9000<span class="cy">×8</span>) ÷ 1000 = <span class="red-mark-box">72</span>（或 9×8=72）</div>
            <div>4. 1200 ÷ 24 ÷ 5 = 50 ÷ 5 = <span class="red-mark-box">10</span></div>
          </div>""",
        "footer_note_html": "* 速解：18×5=90、25×4=100、1000÷125=8（先記 1000÷125=8 更快）",
        "guide_html": "演練 3 可點出「1000÷125 = 8」，所以 9000÷125 = 9×8 = 72 一秒心算！",
        "points_list": [
            "提醒：連除「只能合併除數相乘」，不能隨便在除號中間亂加括號而不改符號！",
        ],
        "pacing_tip": "第 4 題若時間不足可改口頭提示去括號變連除。",
    },
    {
        "sort_order": 7,
        "badge_text": "觀念 4",
        "is_prob": False,
        "page_ref": "P.75",
        "category": "CONCEPT",
        "min_difficulty": 1.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<h1 class="board-title"># 帶餘除法與週期性</h1>
          <div class="board-sub">
            <div><span class="cy">核心式</span>：被除數 ＝ 除數×商 ＋ 餘數</div>
            <div><span class="cy">餘數限制</span>：0 ≤ 餘數 <span class="red-mark-box">&lt; 除數</span></div>
            <div><span class="cy">倒推整除</span>：被除數 − 餘數 ＝ 除數×商</div>
            <div><span class="cy">週期餘數</span>：總數 ÷ 週期（餘 0 看末項）</div>
          </div>""",
        "right_visual_html": """<svg viewBox="0 0 320 115" xmlns="http://www.w3.org/2000/svg">
            <circle cx="85" cy="55" r="36" fill="none" stroke="#111827" stroke-width="2.5"/>
            <text x="85" y="52" text-anchor="middle" font-size="12" font-weight="800">週期 = 7</text>
            <text x="85" y="68" text-anchor="middle" font-size="11" font-weight="700" fill="#B45309">星期輪轉</text>
            <circle cx="85" cy="19" r="4" fill="#DC2626"/>
            <circle cx="230" cy="55" r="36" fill="none" stroke="#111827" stroke-width="2.5" stroke-dasharray="5,3"/>
            <text x="230" y="52" text-anchor="middle" font-size="12" font-weight="800">週期 = 4</text>
            <text x="230" y="68" text-anchor="middle" font-size="11" font-weight="700" fill="#B45309">紅黃藍綠</text>
            <text x="160" y="108" text-anchor="middle" font-size="12" font-weight="800" fill="#111827">第 45 顆：45 ÷ 4 = 11 … 餘 1 → 紅</text>
          </svg>""",
        "footer_note_html": "* 速解：餘 1 是第一個；整除（餘 0）是循環最後一個！",
        "guide_html": "帶學生口頭快答 P.76 觀念題型 1~4（餘最大6被除90、餘0、紅、8+4=12）。",
        "points_list": [
            "觀念題型 4 餘數可加性：15餘8 + 15餘4 直接把餘數相加得 12（若超過 15 再減 15）。",
        ],
        "pacing_tip": "基礎班級務必確認學生理解「餘 0 等於最後一個」而非第 0 個。",
    },
    {
        "sort_order": 8,
        "badge_text": "演練 P.77(1)",
        "is_prob": True,
        "page_ref": "P.77 題型演練 1, 2",
        "category": "DRILL",
        "min_difficulty": 1.0,
        "max_difficulty": 4.2,
        "est_minutes": 10,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.77 演練 1 &amp; 2</div>
          <div class="eq-box">
            <div>1. 三位數 ÷ 24 餘 18，最小？最大？</div>
            <div>2. 今天星期二，過 100 天？過 365 天？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. <span class="cy">24 的倍數 + 18</span>（三位數 100~999）：</div>
            <div>&nbsp;&nbsp;&nbsp;最小：24×4 + 18 = 96+18 = <span class="red-mark-box">114</span></div>
            <div>&nbsp;&nbsp;&nbsp;最大：(999−18)÷24 = 40…21 → 24×40+18 = <span class="red-mark-box">978</span></div>
            <div style="margin-top:6px;">2. 100÷7 餘 <span class="cy">2</span> → <span class="red-mark-box">四</span>；365÷7 餘 <span class="cy">1</span> → <span class="red-mark-box">三</span></div>
          </div>""",
        "footer_note_html": "* 速解：先算出「倍數範圍」，最後再統一加回餘數 18",
        "guide_html": "演練 1 提醒：先看 100 附近 24 的倍數（24×4=96, 加 18=114；若 24×3+18=90 還是二位數不合！）。",
        "points_list": [
            "演練 2 順便補充：平年 365 天＝52 週餘 1 天，所以今年生日星期幾，明年就會往後跳 1 天！",
        ],
        "pacing_tip": "帶餘數範圍題是段考常考陷阱，基礎班級需放慢驗算。",
    },
    {
        "sort_order": 9,
        "badge_text": "演練 P.77(2)",
        "is_prob": True,
        "page_ref": "P.77 題型演練 3, 4",
        "category": "DRILL",
        "min_difficulty": 1.8,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<div class="board-prob-title">P.77 演練 3 &amp; 4（同差與和倍）</div>
          <div class="eq-box">
            <div>3. ÷6餘4、÷8餘6、÷9餘7，最小整數？</div>
            <div>4. 商 9 餘 4，四數和 157，求被、除數？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>3. 餘數不同，但「<span class="cy">都差 2</span>」（不足 2）！</div>
            <div>&nbsp;&nbsp;&nbsp;[6, 8, 9] = 72 → 72 − 2 = <span class="red-mark-box">70</span></div>
            <div style="margin-top:6px;">4. 被＋除 = 157 − 9 − 4 = <span class="cy">144</span></div>
            <div>&nbsp;&nbsp;&nbsp;除數 = (144 − 4) ÷ (9 + 1) = <span class="red-mark-box">14</span>；被 = <span class="red-mark-box">130</span></div>
          </div>""",
        "footer_note_html": "* 速解：餘數不相同時，檢查「除數 − 餘數」是否一樣（同差）",
        "guide_html": "演練 3 是韓信點兵「同差」經典題；演練 4 結合了第 7 單元的「和倍模型」（被除數是除數的 9 倍多 4）。",
        "points_list": [
            "演練 4 檢查：130 ÷ 14 = 9 … 4，130+14+9+4 = 157 完全正確！",
        ],
        "pacing_tip": "第 4 題建議畫線段圖輔助「被除數＝9份＋4、除數＝1份」。",
    },
    {
        "sort_order": 10,
        "badge_text": "觀念 5",
        "is_prob": False,
        "page_ref": "P.78",
        "category": "CONCEPT",
        "min_difficulty": 1.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": True,
        "left_html": """<h1 class="board-title"># 估算與乘積極值拼盤</h1>
          <div class="board-sub">
            <div><span class="cy">乘積最大</span>：高位大，且<span class="red-mark-box">兩數差盡量小</span></div>
            <div><span class="cy">乘積最小</span>：高位小，且<span class="red-mark-box">兩數差盡量大</span></div>
            <div><span class="cy">估算</span>：除數四捨五入至整十/百</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>例：2, 3, 4, 5 兩位數乘積最大？</div>
            <div>高位放 5, 4 → <span class="cy">52 × 43 = 2236</span> vs 53×42=2226</div>
            <div style="margin-top:6px;">例：1, 2, 3, 4 乘積最小？</div>
            <div>高位放 1, 2 → <span class="cy">13 × 24 = 312</span> vs 14×23=322</div>
          </div>""",
        "footer_note_html": "* 速解：周長固定時，正方形面積最大（兩數越接近，乘積越大）",
        "guide_html": "學生直覺會把 53 × 42 當成最大，其實 52 + 43 = 95、53 + 42 = 95 和相等，誰差小（52−43=9 < 53−42=11）誰就大！",
        "points_list": [
            "口頭帶 P.78-79 估算：398×49 ≈ 400×50 = 20000、8124÷39 ≈ 8000÷40 = 200。",
        ],
        "pacing_tip": "可用「10×10 > 9×11」快速建立和固定差小積大直覺。",
    },
    {
        "sort_order": 11,
        "badge_text": "演練 P.79",
        "is_prob": True,
        "page_ref": "P.79-80 拼盤極值與估算",
        "category": "DRILL",
        "min_difficulty": 1.5,
        "max_difficulty": 4.8,
        "est_minutes": 10,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.79-80 演練 1~4</div>
          <div class="eq-box">
            <div>1. 1,3,5,7,9 排三位×兩位，最大？最小？</div>
            <div>2. 0,2,4,6,8 排三位×兩位，最大？</div>
            <div>3. 兩數和 20，積最大？不相等整數？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. 最大：<span class="red-mark-box">751 × 93 = 69843</span>（非 951×73）</div>
            <div>&nbsp;&nbsp;&nbsp;最小：<span class="red-mark-box">379 × 15 = 5685</span></div>
            <div>2. 最大：<span class="red-mark-box">640 × 82 = 52480</span>（0 放三位個位）</div>
            <div>3. 和 20 最大：10×10=<span class="red-mark-box">100</span>；不等：9×11=<span class="red-mark-box">99</span></div>
          </div>""",
        "footer_note_html": "* 速解：三位×兩位求最大 → 先用前 4 大數字排「大兩位×兩位」，最小數字放三位個位",
        "guide_html": "特別強調：看 75×93=6975 比 95×73=6935 大，所以千百位先比較兩位數乘積！",
        "points_list": [
            "演練 4 估算：48×19.8×98 ≈ 50×20×100 = 100000 元。",
        ],
        "pacing_tip": "含 0 的極值排法可先確定 0 放三位數個位再排其餘四數。",
    },
    {
        "sort_order": 12,
        "badge_text": "進階 P.80",
        "is_prob": True,
        "page_ref": "P.80 進階挑戰 1-3",
        "category": "ADVANCED",
        "min_difficulty": 2.0,
        "max_difficulty": 5.0,
        "est_minutes": 10,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.80 進階 1 &amp; 3</div>
          <div class="eq-box">
            <div>1. 9999×2222 + 3333×3334</div>
            <div style="margin-top:8px;">3. (100+98+…+2) − (99+97+…+1)</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>1. = 3333×<span class="cy">(3×2222)</span> + 3333×3334</div>
            <div>&nbsp;&nbsp;&nbsp;= 3333×(6666 + 3334) = <span class="red-mark-box">33330000</span></div>
            <div style="margin-top:8px;">3. = (100−99) + (98−97) + … + (2−1)</div>
            <div>&nbsp;&nbsp;&nbsp;= 1 × 50 組 = <span class="red-mark-box">50</span></div>
          </div>""",
        "footer_note_html": "* 速解：沒相同因數就「拆倍數湊出 3333」；兩長串相減就「逐項配對」",
        "guide_html": "進階 2（125×25×32 = 100000）口頭帶過；進階 3 示範不用分別算兩個梯形和，兩兩配對差 1 共 50 組秒殺！",
        "points_list": [
            "進階 1 是標準國中資優段考題型，提醒學生看到 9999 與 3333 要立刻起疑心。",
        ],
        "pacing_tip": "若學生未學等差級數，第 3 題的「兩兩配對」是最直覺解法。",
    },
    {
        "sort_order": 13,
        "badge_text": "進階 P.81",
        "is_prob": True,
        "page_ref": "P.81-82 進階 6, 8",
        "category": "ADVANCED",
        "min_difficulty": 2.4,
        "max_difficulty": 5.0,
        "est_minutes": 8,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.81-82 進階 6 &amp; 8</div>
          <div class="eq-box">
            <div>6. 36×45 + 72×27 + 18×2</div>
            <div style="margin-top:8px;">8. 1999 + 999×999</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>6. 全湊 <span class="cy">18</span>：18×90 + 18×108 + 18×2</div>
            <div>&nbsp;&nbsp;&nbsp;= 18×(90 + 108 + 2) = 18×200 = <span class="red-mark-box">3600</span></div>
            <div style="margin-top:8px;">8. = <span class="cy">1000 + 999</span> + 999×999</div>
            <div>&nbsp;&nbsp;&nbsp;= 1000 + 999×(1+999) = <span class="red-mark-box">1000000</span></div>
          </div>""",
        "footer_note_html": "* 速解：1999 拆成 1000 + 999，就能把 999 提出來湊 1000！",
        "guide_html": "進階 6 也可以全湊 36（36×45 + 36×54 + 36×1 = 36×100 = 3600）更快！示範兩種湊法。",
        "points_list": [
            "進階 7（擴大 10 倍，商不變 14、餘數也擴大 10 倍變 60）務必口頭強調！",
        ],
        "pacing_tip": "第 8 題提示「1999 = 1000 + 999」後可讓學生自行完成提出 999。",
    },
    {
        "sort_order": 14,
        "badge_text": "進階 P.82",
        "is_prob": True,
        "page_ref": "P.82 進階 9, 10",
        "category": "ADVANCED",
        "min_difficulty": 2.6,
        "max_difficulty": 5.0,
        "est_minutes": 9,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.82 進階 9 &amp; 10</div>
          <div class="eq-box">
            <div>9. 1×2×…×100 末尾有幾個 0？</div>
            <div>10. 四位數 +3 被 7 整除，−3 被 8 整除，最小？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>9. 一個 0 ＝ 2×5（2 很多，只要<span class="cy">數幾個 5</span>）</div>
            <div>&nbsp;&nbsp;&nbsp;100÷5=<span class="cy">20</span>、100÷25=<span class="cy">4</span> → 20+4 = <span class="red-mark-box">24</span> 個 0</div>
            <div style="margin-top:6px;">10. 7 的倍數 −3 ＝ 8 的倍數 +3</div>
            <div>&nbsp;&nbsp;&nbsp;最小解 <span class="cy">67</span>（67+3=70, 67−3=64）</div>
            <div>&nbsp;&nbsp;&nbsp;67 + 56×17 = <span class="red-mark-box">1019</span></div>
          </div>""",
        "footer_note_html": "* 速解：數 5 的個數＝「÷5 + ÷25 + …」；不同餘先找「最小特解 + 公倍數」",
        "guide_html": "第 9 題提醒學生 25, 50, 75, 100 各多貢獻一個 5；第 10 題示範「先列 8 的倍數+3（11,19,27,35,43,51,59,67）找第一個 +3 被 7 整除的 67」，再累加 56 進入四位數。",
        "points_list": [
            "驗算 1019：1019+3 = 1022 = 7×146；1019−3 = 1016 = 8×127，完全正確！",
        ],
        "pacing_tip": "第 10 題為較難數論題，時間緊迫可只講解「找最小特解 67」步驟。",
    },
    {
        "sort_order": 15,
        "badge_text": "資優 A 組",
        "is_prob": True,
        "page_ref": "P.83 資優挑戰 A1-A4",
        "category": "GIFTED_A",
        "min_difficulty": 2.8,
        "max_difficulty": 5.0,
        "est_minutes": 8,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.83 A 組 1、3、4</div>
          <div class="eq-box">
            <div>A1. 12345 × 99999</div>
            <div>A3. 1~6 排兩三位數，差最小？</div>
            <div>A4. 除數 36 看成 63，商 14 餘 18，正解？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>A1. 12345×(100000−1) = <span class="red-mark-box">1234487655</span></div>
            <div>A3. 百位差 1，大數盡量小、小數盡量大：</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;<span class="red-mark-box">412 − 365 = 47</span></div>
            <div>A4. 被除數 = 63×14+18 = <span class="cy">900</span> → 900÷36 = <span class="red-mark-box">25</span></div>
          </div>""",
        "footer_note_html": "* 速解：三位數差最小 → 百位差 1，剩下放「最小配最大」（12 vs 65）",
        "guide_html": "A2（12×…×25 數 5：15, 20, 25(2個) → 4 個 0）口頭對答案；A3 教學生「412 − 365 = 47」比 512 − 463 = 49 更小！",
        "points_list": [
            "A4 口訣：「將錯就錯先求出不變的被除數」，再除以正確除數。",
        ],
        "pacing_tip": "A 組題型適合 Lv.3 以上班級作為課堂延伸。",
    },
    {
        "sort_order": 16,
        "badge_text": "資優 B 組",
        "is_prob": True,
        "page_ref": "P.84 資優挑戰 B1,2,4",
        "category": "GIFTED_B",
        "min_difficulty": 3.4,
        "max_difficulty": 5.0,
        "est_minutes": 8,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.84 B 組 1、2、4</div>
          <div class="eq-box">
            <div>B1. 2026×20252025 − 2025×20262026</div>
            <div>B2. ÷11, 13, 17 皆餘 5，最小四位數？</div>
            <div>B4. 9 + 99 + 999 + 9999 + 99999</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>B1. 20252025 = 2025×<span class="cy">10001</span> → 兩邊完全一樣 = <span class="red-mark-box">0</span></div>
            <div>B2. [11, 13, 17] = <span class="cy">2431</span> → 2431 + 5 = <span class="red-mark-box">2436</span></div>
            <div>B4. (10+100+…+100000) − 5 = <span class="red-mark-box">111105</span></div>
          </div>""",
        "footer_note_html": "* 速解：疊字數 ABCDABCD ＝ ABCD × 10001！",
        "guide_html": "B1 看到 20252025 立刻拆成 2025 × 10001，左邊變 2026×2025×10001，右邊也是 2025×2026×10001，瞬間相減等於 0！",
        "points_list": [
            "B2 注意 11, 13, 17 兩兩互質，最小公倍數直接三數相乘 2431（已是四位數）。",
        ],
        "pacing_tip": "疊字數拆 10001 是資優班必背技巧，可加碼問 123123 = 123×1001。",
    },
    {
        "sort_order": 17,
        "badge_text": "資優 B3",
        "is_prob": True,
        "page_ref": "P.84 資優挑戰 B3",
        "category": "GIFTED_B",
        "min_difficulty": 3.8,
        "max_difficulty": 5.0,
        "est_minutes": 6,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.84 B3（1~9 整除九位數）</div>
          <div class="eq-box">
            <div>1~9 各用一次，前 k 位被 k 整除</div>
            <div>求這個九位數？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>① 第 5 位必為 <span class="cy">5</span>；偶數位 (2,4,6,8) 皆偶數</div>
            <div>② 第 4 位看末兩位被 4 整除；前 6 位被 3 整除</div>
            <div>③ 第 8 位看末三位被 8 整除 → 唯一解：</div>
            <div>&nbsp;&nbsp;&nbsp;<span class="red-mark-box">381654729</span></div>
          </div>""",
        "footer_note_html": "* 速解：先定「5」與「奇偶交錯」，再卡 4 與 8 的整除尾數",
        "guide_html": "世界經典數學謎題！帶學生一起推理：奇數位只能放 {1,3,7,9}、偶數位放 {2,4,6,8}，再用 3、4、6、8 倍數篩出唯一解。",
        "points_list": [
            "前三位 381(÷3)、前四位 3816(16÷4)、前六位 381654(÷3且偶)、前七位 3816547÷7=545221！",
        ],
        "pacing_tip": "可當作挑戰作業或 5 分鐘互動推理搶答。",
    },
    {
        "sort_order": 18,
        "badge_text": "壓軸 C1",
        "is_prob": True,
        "page_ref": "P.85 壓軸挑戰 C1",
        "category": "GIFTED_C",
        "min_difficulty": 4.2,
        "max_difficulty": 5.0,
        "est_minutes": 5,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.85 C1（階乘末尾 0 反推）</div>
          <div class="eq-box">
            <div>(1) 1×2×…×50 末尾幾個 0？</div>
            <div>(2) 1×2×…×□ 剛好 15 個 0，□ 最大、最小？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>(1) 50÷5 + 50÷25 = 10 + 2 = <span class="red-mark-box">12</span> 個 0</div>
            <div>(2) 推算 5 的個數到 15 個：</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;到 60：12+2=14 個；到 <span class="cy">65</span>：13+2 = 15 個！</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;70 會變 16 個 → 最小 <span class="red-mark-box">65</span>、最大 <span class="red-mark-box">69</span></div>
          </div>""",
        "footer_note_html": "* 速解：5 的倍數才會增加 0，所以剛好在 65~69 之間都維持 15 個 0",
        "guide_html": "從正向數 0 升級到逆向鎖定區間，關鍵是想到「66, 67, 68, 69 不含因數 5，所以不會多出新的 0」。",
        "points_list": [
            "65 = 5×13（貢獻 1 個 5），加上 25, 50 多貢獻的 2 個，剛好 13+2 = 15。",
        ],
        "pacing_tip": "Lv.5 資優壓軸專屬，強調區間範圍概念。",
    },
    {
        "sort_order": 19,
        "badge_text": "壓軸 C2",
        "is_prob": True,
        "page_ref": "P.85 壓軸挑戰 C2",
        "category": "GIFTED_C",
        "min_difficulty": 4.2,
        "max_difficulty": 5.0,
        "est_minutes": 5,
        "is_required": False,
        "left_html": """<div class="board-prob-title">P.85 C2（最大公因數與乘積）</div>
          <div class="eq-box">
            <div>兩位數乘積 1188，GCD = 6</div>
            <div>(1) 求此兩數？</div>
            <div>(2) 各加某整數後乘積 2340，求該數？</div>
          </div>""",
        "right_visual_html": """<div class="eq-box">
            <div>(1) 設兩數 <span class="cy">6a, 6b</span>（a,b 互質）→ 36ab = 1188 → ab = <span class="cy">33</span></div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;33 = 3×11（1×33 不合兩位數）→ <span class="red-mark-box">18 與 66</span></div>
            <div>(2) 兩數差不變 = 66−18 = <span class="cy">48</span></div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;2340 = 30×78（差48）→ 加 <span class="red-mark-box">12</span></div>
          </div>""",
        "footer_note_html": "* 速解：兩數同時加上相同整數，「兩數的差」永遠不變！",
        "guide_html": "第 (2) 小題不需解一元二次方程式，直接抓住「差不變＝48」，把 2340 做因數分解找相差 48 的兩因數（30×78）即可秒殺！",
        "points_list": [
            "三小時課程完美收尾，指派課後複習並預告下一堂「五上10 分數加減應用」。",
        ],
        "pacing_tip": "可預告下一單元內容並指派對應回家作業。",
    },
]


def seed_database(db: Session) -> None:
    if db.query(User).first() is not None:
        return

    admin = User(
        username="admin",
        name="教務管理員",
        role="ADMIN",
        password_hash=get_password_hash("admin123"),
    )
    t_lin = User(
        username="teacher_lin",
        name="林志明 老師",
        role="INSTRUCTOR",
        password_hash=get_password_hash("teacher123"),
    )
    t_chen = User(
        username="teacher_chen",
        name="陳雅婷 老師",
        role="INSTRUCTOR",
        password_hash=get_password_hash("teacher123"),
    )
    db.add_all([admin, t_lin, t_chen])
    db.flush()

    unit9 = Unit(
        code="G5-U9",
        title="五上9 多位數乘除技巧",
        grade_term="五上",
        description="包含乘法分配律、特別數速算、商不變與連除、帶餘除法週期、乘積極值拼盤與資優挑戰題。",
        sort_order=9,
    )
    db.add(unit9)
    db.flush()

    for s_data in G5_CH9_SLIDES:
        db.add(Slide(unit_id=unit9.id, **s_data))

    # 新增第二個範例單元（五上10 預告骨架，方便測試單元切換）
    unit10 = Unit(
        code="G5-U10",
        title="五上10 分數加減與應用",
        grade_term="五上",
        description="異分母分數通分技巧、帶分數加減借位與生活應用題。",
        sort_order=10,
    )
    db.add(unit10)
    db.flush()

    db.add(
        Slide(
            unit_id=unit10.id,
            sort_order=1,
            badge_text="觀念 1",
            is_prob=False,
            page_ref="P.86",
            category="CONCEPT",
            min_difficulty=1.0,
            max_difficulty=5.0,
            est_minutes=12,
            is_required=True,
            left_html="""<h1 class="board-title"># 異分母通分與最小公倍數</h1>
          <div class="board-sub">
            <div><span class="cy">核心步驟</span>：先找分母的最小公倍數 [a, b]</div>
            <div>&nbsp;&nbsp;分子分母同乘倍數 → <span class="red-mark-box">擴分</span></div>
          </div>""",
            right_visual_html="""<div class="eq-box">
            <div>例：<span class="frac"><span class="num">2</span><span class="den">3</span></span> + <span class="frac"><span class="num">3</span><span class="den">4</span></span> = <span class="frac"><span class="num">8</span><span class="den">12</span></span> + <span class="frac"><span class="num">9</span><span class="den">12</span></span> = <span class="red-mark-box">1 又 5/12</span></div>
          </div>""",
            footer_note_html="* 速解：兩分母互質時，直接交叉相乘最省時！",
            guide_html="複習擴分與約分觀念，提醒最後答案要化成最簡分數或帶分數。",
            points_list=["口頭演練分母互質與倍數關係的通分速算。"],
            pacing_tip="基礎班可多練兩題通分暖身。",
        )
    )

    c1 = ClassGroup(
        name="五上資優 A 班",
        grade_term="五上",
        instructor_id=t_lin.id,
        current_unit_id=unit9.id,
        last_completed_slide_order=0,
        current_difficulty=3.8,
        last_delta=0.4,
        default_duration_min=180,
        admin_note="本班計算速度快，請多留 15 分鐘討論資優 B 組 B3 與 C 組壓軸題。",
    )
    c2 = ClassGroup(
        name="五上標準 B 班",
        grade_term="五上",
        instructor_id=t_lin.id,
        current_unit_id=unit9.id,
        last_completed_slide_order=6,
        current_difficulty=2.8,
        last_delta=0.0,
        default_duration_min=180,
        admin_note="上次已教完連除簡算（第 6 頁），本堂從「觀念 4 帶餘除法」接續。",
    )
    c3 = ClassGroup(
        name="五上基礎加強班",
        grade_term="五上",
        instructor_id=t_chen.id,
        current_unit_id=unit9.id,
        last_completed_slide_order=0,
        current_difficulty=1.6,
        last_delta=-0.3,
        default_duration_min=120,
        admin_note="上堂學生對分配律進退位較吃力，本堂聚焦核心觀念與基礎演練。",
    )
    db.add_all([c1, c2, c3])
    db.flush()

    db.add_all(
        [
            DifficultyHistory(
                class_id=c1.id,
                old_value=3.4,
                new_value=3.8,
                source="SYSTEM_CALC",
                changed_by=t_lin.id,
                reason="上堂綜合表現 4.40/5.0，系統自動調升難度至 3.8。",
            ),
            DifficultyHistory(
                class_id=c3.id,
                old_value=1.9,
                new_value=1.6,
                source="ADMIN_OVERRIDE",
                changed_by=admin.id,
                reason="管理員檢視上堂回報後手動微調降難度，確保基礎穩固。",
            ),
        ]
    )
    db.commit()
