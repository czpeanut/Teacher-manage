"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FileUp, KeyRound, Loader2, Sparkles, X } from "lucide-react";
import { API_BASE, apiFetch, getToken, Slide } from "@/lib/api";

interface MaterialUploaderModalProps {
  onClose: () => void;
  onSuccess: (createdUnitId: number) => void;
}

export default function MaterialUploaderModal({ onClose, onSuccess }: MaterialUploaderModalProps) {
  const [unitCode, setUnitCode] = useState("G5-NEW");
  const [unitTitle, setUnitTitle] = useState("五下 分數應用與逆推");
  const [gradeTerm, setGradeTerm] = useState("五下");
  const [targetDuration, setTargetDuration] = useState(180);

  const [useAi, setUseAi] = useState(true);
  const [aiProvider, setAiProvider] = useState<"gemini" | "openai">("gemini");
  const [customModel, setCustomModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saveApiKey, setSaveApiKey] = useState(true);
  const [aiStatus, setAiStatus] = useState<{ gemini_configured: boolean; openai_configured: boolean }>({
    gemini_configured: false,
    openai_configured: false,
  });

  const [file, setFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewSlides, setPreviewSlides] = useState<Omit<Slide, "id" | "unit_id">[] | null>(null);

  useEffect(() => {
    apiFetch<{ gemini_configured: boolean; openai_configured: boolean }>("/api/units/ai-status")
      .then(setAiStatus)
      .catch(() => {});
  }, []);

  const isKeyConfigured =
    aiProvider === "gemini" ? aiStatus.gemini_configured : aiStatus.openai_configured;

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
      formData.append("use_ai", String(useAi));
      formData.append("ai_provider", aiProvider);
      if (customModel.trim()) {
        formData.append("custom_model", customModel.trim());
      }
      formData.append("target_duration_min", String(targetDuration));
      formData.append("save_api_key", String(saveApiKey));
      if (apiKey.trim()) {
        formData.append("api_key", apiKey.trim());
      }

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
        const textBody = await res.text();
        let detail = `HTTP ${res.status}`;
        try {
          const errData = JSON.parse(textBody);
          if (errData.detail) detail = errData.detail;
        } catch {
          if (textBody) detail = `HTTP ${res.status}: ${textBody.slice(0, 200)}`;
        }
        throw new Error(detail);
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
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[92vh] overflow-y-auto shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              上傳教材自動組成備課板書
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              AI 視覺引擎直接讀取 PDF 頁面（含直式分數與圖形），依《五上9》規格產出詳解與 SVG 板書
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

          {/* AI 引擎設定區 */}
          <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs font-extrabold text-slate-900 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAi}
                  onChange={(e) => setUseAi(e.target.checked)}
                  className="rounded accent-slate-900"
                />
                啟用 AI 視覺教研引擎（推薦：完整辨識分數、自動解題、繪製 SVG 與撰寫速解）
              </label>
            </div>

            {useAi && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-[11px] font-bold text-slate-700 mb-1">AI 模型供應商</label>
                  <select
                    value={aiProvider}
                    onChange={(e) => setAiProvider(e.target.value as "gemini" | "openai")}
                    className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white"
                  >
                    <option value="gemini">Google Gemini（自動選用最新可用 Flash 模型）</option>
                    <option value="openai">OpenAI GPT-4o-mini</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-700 mb-1 flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <KeyRound className="w-3 h-3" />
                      API Key
                    </span>
                    {isKeyConfigured && (
                      <span className="text-emerald-700 flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" /> 已記憶於本機
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={isKeyConfigured ? "已設定（留空沿用，或輸入覆蓋）" : "請貼上 API Key"}
                    className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white"
                  />
                  <label className="flex items-center gap-1.5 text-[11px] text-slate-600 mt-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={saveApiKey}
                      onChange={(e) => setSaveApiKey(e.target.checked)}
                      className="rounded accent-slate-900"
                    />
                    記住此金鑰於本機（backend/.env）
                  </label>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-[11px] font-bold text-slate-700 mb-1">
                    指定模型名稱（選填，留空則自動選用帳號最新可用模型）
                  </label>
                  <input
                    type="text"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    placeholder="例如：hydrogen、gemini-3.8-flash、gemini-2.5-pro"
                    className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs bg-white"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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
            <div className="sm:col-span-2">
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
              <label className="block text-xs font-bold text-slate-700 mb-1">目標課時</label>
              <select
                value={targetDuration}
                onChange={(e) => setTargetDuration(Number(e.target.value))}
                className="w-full border border-slate-300 rounded-lg px-2.5 py-2 text-sm bg-white"
              >
                <option value={120}>2 小時</option>
                <option value={180}>3 小時</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-center">
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
            <div className="sm:col-span-3 border-2 border-dashed border-slate-300 rounded-xl p-3.5 bg-slate-50 text-center">
              <label className="cursor-pointer block">
                <FileUp className="w-5 h-5 text-slate-500 mx-auto mb-1" />
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
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              或直接貼上教材文字（若已選擇 PDF 檔案則以此為主）
            </label>
            <textarea
              rows={3}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="貼上題目或觀念文字..."
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono"
            />
          </div>

          {previewSlides && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-900">
              <span className="font-bold">AI 組版並入庫成功！</span>共生成 {previewSlides.length} 頁板書（
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
              {loading ? "AI 解析生成板書中（約 15~30 秒）..." : "自動解析並組成單元"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
