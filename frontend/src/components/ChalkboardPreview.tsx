"use client";

import { PlannedSlideItem } from "@/lib/api";

const CATEGORY_MAP: Record<string, string> = {
  CONCEPT: "核心觀念",
  DRILL: "基礎演練",
  ADVANCED: "進階挑戰",
  GIFTED_A: "資優 A",
  GIFTED_B: "資優 B",
  GIFTED_C: "資優壓軸",
};

interface ChalkboardPreviewProps {
  item: PlannedSlideItem;
  unitTitle: string;
}

export default function ChalkboardPreview({ item, unitTitle }: ChalkboardPreviewProps) {
  const s = item.slide;
  const headerText = s.page_ref
    ? `${unitTitle}（${s.page_ref}）｜${item.time_slot}`
    : `${unitTitle}｜${item.time_slot}`;

  return (
    <div className="chalkboard-sheet border border-slate-300 rounded-xl p-5 shadow-sm">
      <div className="page-meta">
        <div className="flex items-center overflow-hidden">
          <span className={s.is_prob ? "meta-badge-prob" : "meta-badge"}>{s.badge_text}</span>
          <span className="truncate font-medium">{headerText}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="border border-slate-400 rounded px-1.5 py-0.5 text-[10px] font-bold bg-slate-50">
            {CATEGORY_MAP[s.category] || s.category}
          </span>
          <span className="text-[10px] text-slate-500">■白 ▲黃(重點) ●紅(標記)</span>
        </div>
      </div>

      <div className="blackboard">
        <div className="board-grid">
          <div dangerouslySetInnerHTML={{ __html: s.left_html }} />
          <div className="board-right">
            <div dangerouslySetInnerHTML={{ __html: s.right_visual_html }} />
            {s.footer_note_html && (
              <>
                <hr className="board-dashed-hr" />
                <div
                  className="board-footer-note"
                  dangerouslySetInnerHTML={{ __html: s.footer_note_html }}
                />
              </>
            )}
          </div>
        </div>
      </div>

      <div className="teaching-notes">
        <div className="mb-2.5">
          <div className="note-label">觀念引導</div>
          <div dangerouslySetInnerHTML={{ __html: s.guide_html }} />
        </div>
        <div>
          <div className="note-label">講解重點</div>
          <ul className="note-list">
            {(s.points_list || []).map((pt, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: pt }} />
            ))}
          </ul>
        </div>
        {s.pacing_tip && (
          <div className="mt-2 pt-1.5 border-t border-dashed border-slate-300 text-xs font-semibold text-slate-600">
            ⚡ 節奏應變提示：{s.pacing_tip}
          </div>
        )}
      </div>

      {item.is_break_after && item.break_label && (
        <div className="mt-3 border-2 border-dashed border-slate-800 rounded-lg bg-slate-100 py-1.5 px-3 text-center text-xs font-extrabold text-slate-900">
          ☕ {item.break_label}
        </div>
      )}
    </div>
  );
}
