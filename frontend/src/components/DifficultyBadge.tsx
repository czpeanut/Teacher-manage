"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

interface DifficultyBadgeProps {
  value: number;
  label?: string;
  delta?: number;
}

export default function DifficultyBadge({ value, label, delta }: DifficultyBadgeProps) {
  let colorClass = "bg-blue-50 text-blue-800 border-blue-200";
  if (value < 1.8) colorClass = "bg-emerald-50 text-emerald-800 border-emerald-200";
  else if (value < 2.6) colorClass = "bg-teal-50 text-teal-800 border-teal-200";
  else if (value >= 4.3) colorClass = "bg-rose-50 text-rose-800 border-rose-200";
  else if (value >= 3.5) colorClass = "bg-amber-50 text-amber-800 border-amber-200";

  return (
    <div className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-bold ${colorClass}`}>
        <span>難度 {value.toFixed(1)}</span>
        {label && <span className="opacity-80 font-semibold">· {label}</span>}
      </span>
      {delta !== undefined && delta !== 0 && (
        <span
          className={`inline-flex items-center text-xs font-bold ${
            delta > 0 ? "text-rose-600" : "text-emerald-600"
          }`}
        >
          {delta > 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
        </span>
      )}
      {delta === 0 && (
        <span className="inline-flex items-center text-xs text-slate-400">
          <Minus className="w-3 h-3" />
        </span>
      )}
    </div>
  );
}
