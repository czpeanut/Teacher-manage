"use client";

import { useState } from "react";
import { FileUp, Loader2, Sparkles, X } from "lucide-react";
import { API_BASE, getToken, Slide } from "@/lib/api";

interface MaterialUploaderModalProps {
  onClose: () => void;
  onSuccess: (createdUnitId: number) => void;
}

export default function MaterialUploaderModal({ onClose, onSuccess }: MaterialUploaderModalProps) {
  const [unitCode, setUnitCode] = useState("G5-U11");
  const [unitTitle, setUnitTitle] = useState("五上11 面積與體積進階");
  const [gradeTerm, setGradeTerm] = useState("五上");
  const [file, setFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewSlides, setPreviewSlides] = useState<Omit<Slide, "id" | "unit_id">[] | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("unit_code", unitCode);
      formData.append("unit_title", unitTitle);
      formData.append("grade_term", gradeTerm);
      formData.append("save_to_db", "true");
      if (file) {
        formData.append("file", file);
      } else if (rawText.trim()) {
        formData.append("raw_text", rawText.trim());
      } else {
        throw new Error("請選擇教材檔案（PDF / TXT / MD）或貼上教材文字");
      }

      const token = getToken();
      const res = await fetch(`${API_BASE}/api/units/upload-material`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setPreviewSlides(data.slides);
      if (data.unit_id) {
        onSuccess(data.unit_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "解析失敗");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              上傳教材自動組成備課板書
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              自動辨識 PDF / 文字中的觀念、演練、進階題型與頁碼，套用黑白三色粉筆規格入庫
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">單元代碼</label>
              <input
                type="text"
                value={unitCode}
                onChange={(e) => setUnitCode(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">單元名稱</label>
              <input
                type="text"
                value={unitTitle}
                onChange={(e) => setUnitTitle(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">年級學期</label>
              <input
                type="text"
                value={gradeTerm}
                onChange={(e) => setGradeTerm(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                required
              />
            </div>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 bg-slate-50 text-center">
            <label className="cursor-pointer block">
              <FileUp className="w-6 h-6 text-slate-500 mx-auto mb-1" />
              <span className="text-xs font-bold text-slate-700">
                {file ? `已選擇：${file.name}` : "點擊選擇教材檔案（支援 .pdf / .txt / .md）"}
              </span>
              <input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              或直接貼上教材文字（系統將自動依「觀念 / 演練 / 進階 / 資優」切分頁面）
            </label>
            <textarea
              rows={5}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder={`觀念 1 平行四邊形面積 (P.90)\n核心公式：底 × 高\n速解：高必須垂直於底邊\n\n演練 1 P.91\n1. 底 12 公分、高 8 公分，面積 = 96`}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono"
            />
          </div>

          {previewSlides && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-900">
              <span className="font-bold">解析並入庫成功！</span>共自動生成 {previewSlides.length} 頁板書（
              {previewSlides.map((s) => s.badge_text).join("、")}）。
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-bold text-slate-700 cursor-pointer"
            >
              關閉
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              自動解析並組成單元
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
