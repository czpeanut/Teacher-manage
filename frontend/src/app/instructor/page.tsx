"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckSquare,
  ClipboardCheck,
  Download,
  FileText,
  FileUp,
  History,
  Layers,
  Loader2,
  Sliders,
  Sparkles,
  Square,
} from "lucide-react";
import ChalkboardPreview from "@/components/ChalkboardPreview";
import DifficultyBadge from "@/components/DifficultyBadge";
import MaterialUploaderModal from "@/components/MaterialUploaderModal";
import Navbar from "@/components/Navbar";
import {
  API_BASE,
  apiFetch,
  ClassGroup,
  GeneratedDoc,
  LessonLog,
  PreviewPlanResponse,
  Unit,
  User,
} from "@/lib/api";

export default function InstructorWorkspace() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"prep" | "range" | "report" | "history">("prep");
  const [showUploader, setShowUploader] = useState(false);

  // 範圍自動組卷狀態
  const [rangeUnitIds, setRangeUnitIds] = useState<number[]>([]);
  const [rangePageStart, setRangePageStart] = useState<string>("");
  const [rangePageEnd, setRangePageEnd] = useState<string>("");
  const [rangeCategories, setRangeCategories] = useState<string[]>([
    "CONCEPT",
    "DRILL",
    "ADVANCED",
    "GIFTED_A",
    "GIFTED_B",
    "GIFTED_C",
  ]);
  const [rangePlan, setRangePlan] = useState<PreviewPlanResponse | null>(null);
  const [rangeSelectedIds, setRangeSelectedIds] = useState<number[]>([]);
  const [loadingRange, setLoadingRange] = useState(false);
  const [generatingRangePdf, setGeneratingRangePdf] = useState(false);

  // 備課產生器狀態
  const [selectedUnitId, setSelectedUnitId] = useState<number | null>(null);
  const [durationMin, setDurationMin] = useState<number>(180);
  const [targetDifficulty, setTargetDifficulty] = useState<number>(3.0);
  const [includeCover, setIncludeCover] = useState<boolean>(true);
  const [plan, setPlan] = useState<PreviewPlanResponse | null>(null);
  const [selectedSlideIds, setSelectedSlideIds] = useState<number[]>([]);
  const [activePreviewIdx, setActivePreviewIdx] = useState<number>(0);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [latestDoc, setLatestDoc] = useState<GeneratedDoc | null>(null);

  // 課後回報狀態
  const [scoreComp, setScoreComp] = useState(4);
  const [scoreAcc, setScoreAcc] = useState(4);
  const [scoreDone, setScoreDone] = useState(4);
  const [scoreEng, setScoreEng] = useState(4);
  const [suggestion, setSuggestion] = useState<"UP" | "KEEP" | "DOWN">("KEEP");
  const [completedSlideOrder, setCompletedSlideOrder] = useState(0);
  const [reportNotes, setReportNotes] = useState("");
  const [submittingLog, setSubmittingLog] = useState(false);
  const [logResult, setLogResult] = useState<LessonLog | null>(null);

  // 歷史紀錄
  const [logs, setLogs] = useState<LessonLog[]>([]);
  const [docs, setDocs] = useState<GeneratedDoc[]>([]);

  const selectedClass = classes.find((c) => c.id === selectedClassId) || null;

  const loadInitial = useCallback(async () => {
    try {
      const me = await apiFetch<User>("/api/auth/me");
      setUser(me);
      const [clsList, unitList] = await Promise.all([
        apiFetch<ClassGroup[]>("/api/classes"),
        apiFetch<Unit[]>("/api/units"),
      ]);
      setClasses(clsList);
      setUnits(unitList);
      if (clsList.length > 0) {
        const first = clsList[0];
        setSelectedClassId(first.id);
        setSelectedUnitId(first.current_unit_id || (unitList[0]?.id ?? null));
        if (first.current_unit_id) setRangeUnitIds([first.current_unit_id]);
        else if (unitList.length > 0) setRangeUnitIds([unitList[0].id]);
        setDurationMin(first.default_duration_min);
        setTargetDifficulty(first.current_difficulty);
        setCompletedSlideOrder(first.last_completed_slide_order);
      }
    } catch {
      router.replace("/");
    }
  }, [router]);

  const handleRangePreview = async (explicitIds?: number[]) => {
    if (!selectedClassId || rangeUnitIds.length === 0) return;
    setLoadingRange(true);
    try {
      const res = await apiFetch<PreviewPlanResponse>("/api/lessons/range-preview", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClassId,
          unit_ids: rangeUnitIds,
          page_start: rangePageStart ? Number(rangePageStart) : null,
          page_end: rangePageEnd ? Number(rangePageEnd) : null,
          categories: rangeCategories.length > 0 ? rangeCategories : null,
          duration_min: durationMin,
          target_difficulty: targetDifficulty,
          include_cover: includeCover,
          selected_slide_ids: explicitIds ?? null,
        }),
      });
      setRangePlan(res);
      setRangeSelectedIds(res.items.filter((i) => i.selected).map((i) => i.slide.id));
    } finally {
      setLoadingRange(false);
    }
  };

  const handleGenerateRangePdf = async () => {
    if (!selectedClassId || rangeUnitIds.length === 0 || rangeSelectedIds.length === 0) return;
    setGeneratingRangePdf(true);
    try {
      const doc = await apiFetch<GeneratedDoc>("/api/lessons/generate-range-pdf", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClassId,
          unit_ids: rangeUnitIds,
          range_title: rangePlan?.unit_title || "跨範圍自動組裝備課",
          duration_min: durationMin,
          target_difficulty: targetDifficulty,
          include_cover: includeCover,
          selected_slide_ids: rangeSelectedIds,
        }),
      });
      setLatestDoc(doc);
      await loadHistory(selectedClassId);
    } finally {
      setGeneratingRangePdf(false);
    }
  };

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  const fetchPreviewPlan = useCallback(
    async (
      cId: number,
      uId: number,
      dur: number,
      diff: number,
      cover: boolean,
      explicitIds?: number[]
    ) => {
      setLoadingPlan(true);
      try {
        const res = await apiFetch<PreviewPlanResponse>("/api/lessons/preview-plan", {
          method: "POST",
          body: JSON.stringify({
            class_id: cId,
            unit_id: uId,
            duration_min: dur,
            target_difficulty: diff,
            include_cover: cover,
            selected_slide_ids: explicitIds ?? null,
          }),
        });
        setPlan(res);
        const selIds = res.items.filter((i) => i.selected).map((i) => i.slide.id);
        setSelectedSlideIds(selIds);
        setActivePreviewIdx(0);
      } finally {
        setLoadingPlan(false);
      }
    },
    []
  );

  const loadHistory = useCallback(async (cId: number) => {
    const [l, d] = await Promise.all([
      apiFetch<LessonLog[]>(`/api/classes/${cId}/logs`),
      apiFetch<GeneratedDoc[]>(`/api/classes/${cId}/docs`),
    ]);
    setLogs(l);
    setDocs(d);
  }, []);

  useEffect(() => {
    if (selectedClassId && selectedUnitId) {
      fetchPreviewPlan(selectedClassId, selectedUnitId, durationMin, targetDifficulty, includeCover);
      loadHistory(selectedClassId);
    }
  }, [selectedClassId, selectedUnitId, durationMin, targetDifficulty, includeCover, fetchPreviewPlan, loadHistory]);

  const handleSelectClass = (c: ClassGroup) => {
    setSelectedClassId(c.id);
    setSelectedUnitId(c.current_unit_id || (units[0]?.id ?? null));
    setDurationMin(c.default_duration_min);
    setTargetDifficulty(c.current_difficulty);
    setCompletedSlideOrder(c.last_completed_slide_order);
    setLatestDoc(null);
    setLogResult(null);
  };

  const toggleSlide = (slideId: number) => {
    const next = selectedSlideIds.includes(slideId)
      ? selectedSlideIds.filter((id) => id !== slideId)
      : [...selectedSlideIds, slideId];
    setSelectedSlideIds(next);
    if (selectedClassId && selectedUnitId) {
      fetchPreviewPlan(selectedClassId, selectedUnitId, durationMin, targetDifficulty, includeCover, next);
    }
  };

  const handleGeneratePdf = async () => {
    if (!selectedClassId || !selectedUnitId || selectedSlideIds.length === 0) return;
    setGeneratingPdf(true);
    try {
      const doc = await apiFetch<GeneratedDoc>("/api/lessons/generate-pdf", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClassId,
          unit_id: selectedUnitId,
          duration_min: durationMin,
          target_difficulty: targetDifficulty,
          include_cover: includeCover,
          selected_slide_ids: selectedSlideIds,
        }),
      });
      setLatestDoc(doc);
      await loadHistory(selectedClassId);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handleSubmitLog = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !selectedUnitId) return;
    setSubmittingLog(true);
    try {
      const res = await apiFetch<LessonLog>("/api/lessons/logs", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClassId,
          unit_id: selectedUnitId,
          score_comprehension: scoreComp,
          score_accuracy: scoreAcc,
          score_completion: scoreDone,
          score_engagement: scoreEng,
          instructor_suggestion: suggestion,
          completed_slide_order: completedSlideOrder,
          notes: reportNotes,
        }),
      });
      setLogResult(res);
      setReportNotes("");
      const updatedClasses = await apiFetch<ClassGroup[]>("/api/classes");
      setClasses(updatedClasses);
      const updatedTarget = updatedClasses.find((c) => c.id === selectedClassId);
      if (updatedTarget) {
        setTargetDifficulty(updatedTarget.current_difficulty);
      }
      await loadHistory(selectedClassId);
    } finally {
      setSubmittingLog(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        載入中...
      </div>
    );
  }

  const selectedPlanItems = plan?.items.filter((i) => i.selected) || [];
  const activeItem = selectedPlanItems[activePreviewIdx] || plan?.items[0] || null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Navbar user={user} activeTab="instructor" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左側：我的班級列表 */}
        <aside className="lg:col-span-3 space-y-3">
          <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider px-1">
            負責班級 ({classes.length})
          </h2>
          <div className="space-y-2.5">
            {classes.map((c) => {
              const active = c.id === selectedClassId;
              const pct =
                c.total_unit_slides > 0
                  ? Math.min(100, Math.round((c.last_completed_slide_order / c.total_unit_slides) * 100))
                  : 0;
              return (
                <button
                  key={c.id}
                  onClick={() => handleSelectClass(c)}
                  className={`w-full text-left p-3.5 rounded-xl border transition cursor-pointer ${
                    active
                      ? "bg-white border-slate-900 ring-2 ring-slate-900/10 shadow-sm"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-slate-900">{c.name}</span>
                    <span className="text-[11px] font-semibold text-slate-500">{c.default_duration_min}分</span>
                  </div>
                  <div className="text-xs text-slate-600 mb-2 truncate">{c.current_unit_title || "尚未指定單元"}</div>
                  <DifficultyBadge value={c.current_difficulty} delta={c.last_delta} />
                  <div className="mt-2.5">
                    <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                      <span>單元進度</span>
                      <span>
                        {c.last_completed_slide_order} / {c.total_unit_slides} 頁 ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-slate-800 h-full rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* 右側：主工作區 */}
        <main className="lg:col-span-9 space-y-5">
          {selectedClass && (
            <>
              {/* 班級狀態與管理員批示橫幅 */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <h1 className="text-lg font-extrabold text-slate-900">{selectedClass.name}</h1>
                    <DifficultyBadge
                      value={selectedClass.current_difficulty}
                      label={selectedClass.difficulty_label}
                      delta={selectedClass.last_delta}
                    />
                  </div>
                  {selectedClass.admin_note && (
                    <div className="mt-2 text-xs bg-amber-50 border border-amber-200 text-amber-900 px-3 py-1.5 rounded-lg">
                      <span className="font-bold">管理員教學指示：</span>
                      {selectedClass.admin_note}
                    </div>
                  )}
                </div>

                {/* 分頁切換 */}
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  <button
                    onClick={() => setShowUploader(true)}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 flex items-center gap-1.5 cursor-pointer"
                  >
                    <FileUp className="w-3.5 h-3.5" />
                    上傳教材自動組版
                  </button>
                  <div className="flex bg-slate-100 p-1 rounded-lg">
                    <button
                      onClick={() => setActiveTab("prep")}
                      className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 cursor-pointer transition ${
                        activeTab === "prep" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5" />
                      單單元備課
                    </button>
                    <button
                      onClick={() => {
                        setActiveTab("range");
                        if (!rangePlan) handleRangePreview();
                      }}
                      className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 cursor-pointer transition ${
                        activeTab === "range" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      範圍自動組卷
                    </button>
                    <button
                      onClick={() => setActiveTab("report")}
                      className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 cursor-pointer transition ${
                        activeTab === "report" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      <ClipboardCheck className="w-3.5 h-3.5" />
                      課後回報評分
                    </button>
                    <button
                      onClick={() => setActiveTab("history")}
                      className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 cursor-pointer transition ${
                        activeTab === "history" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      <History className="w-3.5 h-3.5" />
                      歷史與下載
                    </button>
                  </div>
                </div>
              </div>

              {/* 分頁 1：備課進度確認與 PDF 產出 */}
              {activeTab === "prep" && (
                <div className="space-y-4">
                  {/* 參數控制列 */}
                  <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1">授課單元</label>
                      <select
                        value={selectedUnitId ?? ""}
                        onChange={(e) => setSelectedUnitId(Number(e.target.value))}
                        className="w-full border border-slate-300 rounded-lg px-2.5 py-2 text-sm bg-white"
                      >
                        {units.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.title} ({u.slide_count}頁)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1">授課時長</label>
                      <select
                        value={durationMin}
                        onChange={(e) => setDurationMin(Number(e.target.value))}
                        className="w-full border border-slate-300 rounded-lg px-2.5 py-2 text-sm bg-white"
                      >
                        <option value={120}>2 小時（120 分鐘）</option>
                        <option value={180}>3 小時（180 分鐘）</option>
                        <option value={90}>1.5 小時（90 分鐘）</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1">
                        目標難度係數：<span className="text-slate-900">{targetDifficulty.toFixed(1)}</span>
                      </label>
                      <input
                        type="range"
                        min={1.0}
                        max={5.0}
                        step={0.1}
                        value={targetDifficulty}
                        onChange={(e) => setTargetDifficulty(Number(e.target.value))}
                        className="w-full accent-slate-900"
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={includeCover}
                          onChange={(e) => setIncludeCover(e.target.checked)}
                          className="rounded accent-slate-900"
                        />
                        含「封面備課總覽頁」
                      </label>
                      <button
                        onClick={handleGeneratePdf}
                        disabled={generatingPdf || selectedSlideIds.length === 0}
                        className="bg-slate-900 hover:bg-slate-800 text-white font-bold py-2 px-4 rounded-lg text-sm flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
                      >
                        {generatingPdf ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            編譯 PDF 中...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 text-amber-400" />
                            產出備課 PDF ({plan?.total_selected_pages ?? 0} 頁)
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* PDF 產出成功下載列 */}
                  {latestDoc && (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between">
                      <div className="text-sm text-emerald-900">
                        <span className="font-bold">備課 PDF 產出完成！</span>
                        <span className="ml-2 text-xs">
                          檔案：{latestDoc.pdf_filename}（共 {latestDoc.page_count} 頁 A4）
                        </span>
                      </div>
                      <a
                        href={`${API_BASE}${latestDoc.download_url}`}
                        target="_blank"
                        rel="noreferrer"
                        className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold px-3.5 py-2 rounded-lg flex items-center gap-1.5"
                      >
                        <Download className="w-4 h-4" />
                        下載 PDF
                      </a>
                    </div>
                  )}

                  {/* 左側勾選清單 + 右側即時板書預覽 */}
                  <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
                    <div className="xl:col-span-4 bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm max-h-[680px] overflow-y-auto space-y-2">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                        <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                          <Sliders className="w-3.5 h-3.5" />
                          自動選頁與時段 ({selectedSlideIds.length}/{plan?.items.length ?? 0})
                        </span>
                        {loadingPlan && <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-400" />}
                      </div>

                      {plan?.items.map((item) => {
                        const selIdx = selectedPlanItems.findIndex((s) => s.slide.id === item.slide.id);
                        const isViewing = activeItem?.slide.id === item.slide.id;
                        return (
                          <div
                            key={item.slide.id}
                            className={`p-2.5 rounded-lg border text-xs transition flex items-start gap-2 ${
                              isViewing
                                ? "border-slate-900 bg-slate-50"
                                : item.selected
                                ? "border-slate-200 bg-white hover:border-slate-300"
                                : "border-slate-100 bg-slate-50/50 opacity-60"
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => toggleSlide(item.slide.id)}
                              className="mt-0.5 text-slate-700 cursor-pointer shrink-0"
                            >
                              {item.selected ? (
                                <CheckSquare className="w-4 h-4 text-slate-900" />
                              ) : (
                                <Square className="w-4 h-4 text-slate-400" />
                              )}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                if (selIdx >= 0) setActivePreviewIdx(selIdx);
                              }}
                              className="flex-1 text-left cursor-pointer"
                            >
                              <div className="flex items-center justify-between gap-1">
                                <span className="font-bold text-slate-900">{item.slide.badge_text}</span>
                                <span className="text-[11px] font-mono text-slate-500">{item.time_slot}</span>
                              </div>
                              <div className="text-slate-600 mt-0.5 truncate">
                                {item.slide.page_ref || "核心板書"} · 難度 {item.slide.min_difficulty}~
                                {item.slide.max_difficulty}
                              </div>
                            </button>
                          </div>
                        );
                      })}
                    </div>

                    <div className="xl:col-span-8">
                      {activeItem ? (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
                            <span>即時 A4 黑白板書預覽（與輸出 PDF 一致）</span>
                            <span>
                              預覽頁 {activePreviewIdx + 1} / {Math.max(1, selectedPlanItems.length)}
                            </span>
                          </div>
                          <ChalkboardPreview item={activeItem} unitTitle={plan?.unit_title || ""} />
                        </div>
                      ) : (
                        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400 text-sm">
                          請在左側勾選至少一頁板書以進行預覽
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* 分頁 2：課後授課狀況回報 */}
              {activeTab === "report" && (
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">課後授課狀況回報與難度自動評分</h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      系統將依四維課堂表現與您的建議，透過防震盪評分公式計算下一堂建議難度係數。
                    </p>
                  </div>

                  {logResult && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-1">
                      <div className="text-sm font-bold text-blue-900">
                        回報已送出！綜合表現：{logResult.calc_composite_score.toFixed(2)} / 5.0
                      </div>
                      <div className="text-xs text-blue-800">{logResult.calc_reason}</div>
                    </div>
                  )}

                  <form onSubmit={handleSubmitLog} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {[
                        { label: "1. 學生理解與吸收度", val: scoreComp, set: setScoreComp },
                        { label: "2. 課堂練習獨立正確率", val: scoreAcc, set: setScoreAcc },
                        { label: "3. 預定進度完成度", val: scoreDone, set: setScoreDone },
                        { label: "4. 課堂節奏與互動專注度", val: scoreEng, set: setScoreEng },
                      ].map((metric) => (
                        <div key={metric.label} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
                          <div className="flex justify-between text-xs font-bold text-slate-700 mb-2">
                            <span>{metric.label}</span>
                            <span className="text-slate-900">{metric.val} / 5 分</span>
                          </div>
                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((n) => (
                              <button
                                key={n}
                                type="button"
                                onClick={() => metric.set(n)}
                                className={`flex-1 py-1.5 rounded text-xs font-bold border cursor-pointer transition ${
                                  metric.val === n
                                    ? "bg-slate-900 text-white border-slate-900"
                                    : "bg-white text-slate-600 border-slate-300 hover:bg-slate-100"
                                }`}
                              >
                                {n}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">
                          本堂實際完成至第幾頁（共 {selectedClass.total_unit_slides} 頁）
                        </label>
                        <input
                          type="number"
                          min={0}
                          max={selectedClass.total_unit_slides}
                          value={completedSlideOrder}
                          onChange={(e) => setCompletedSlideOrder(Number(e.target.value))}
                          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">講師主觀難度建議</label>
                        <div className="grid grid-cols-3 gap-2">
                          {(
                            [
                              { k: "DOWN", label: "建議降難度" },
                              { k: "KEEP", label: "維持現狀" },
                              { k: "UP", label: "建議升難度" },
                            ] as const
                          ).map((opt) => (
                            <button
                              key={opt.k}
                              type="button"
                              onClick={() => setSuggestion(opt.k)}
                              className={`py-2 rounded-lg text-xs font-bold border cursor-pointer ${
                                suggestion === opt.k
                                  ? "bg-slate-900 text-white border-slate-900"
                                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                              }`}
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        課堂狀況備註（學生卡關點、需補強觀念，將同步顯示於下堂備課封面）
                      </label>
                      <textarea
                        rows={3}
                        value={reportNotes}
                        onChange={(e) => setReportNotes(e.target.value)}
                        placeholder="例：演練 4 的隱形 ×1 較多同學忘記，下次上課前先口頭複習 3 分鐘。"
                        className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={submittingLog}
                      className="bg-slate-900 hover:bg-slate-800 text-white font-bold px-5 py-2.5 rounded-lg text-sm flex items-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      {submittingLog && <Loader2 className="w-4 h-4 animate-spin" />}
                      送出回報並計算下堂難度
                    </button>
                  </form>
                </div>
              )}

              {/* 分頁 1.5：跨單元／頁碼範圍自動組卷 */}
              {activeTab === "range" && (
                <div className="space-y-4">
                  <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-base font-bold text-slate-900">依範圍自動產生備課教材</h2>
                        <p className="text-xs text-slate-500">
                          可複選多個單元、限定教材頁碼起訖與題型層級，系統將依難度係數（{targetDifficulty.toFixed(1)}）與授課時長自動組裝 PDF。
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleRangePreview()}
                          disabled={loadingRange || rangeUnitIds.length === 0}
                          className="px-3.5 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-bold cursor-pointer"
                        >
                          {loadingRange ? "組裝中..." : "重新篩選組卷"}
                        </button>
                        <button
                          type="button"
                          onClick={handleGenerateRangePdf}
                          disabled={generatingRangePdf || rangeSelectedIds.length === 0}
                          className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                        >
                          {generatingRangePdf ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                          )}
                          產出範圍教材 PDF ({rangeSelectedIds.length + (includeCover ? 1 : 0)} 頁)
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-100">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1.5">1. 選擇包含單元（可複選）</label>
                        <div className="space-y-1.5 max-h-32 overflow-y-auto border border-slate-200 rounded-lg p-2">
                          {units.map((u) => {
                            const checked = rangeUnitIds.includes(u.id);
                            return (
                              <label key={u.id} className="flex items-center gap-2 text-xs cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={() => {
                                    setRangeUnitIds((prev) =>
                                      checked ? prev.filter((id) => id !== u.id) : [...prev, u.id]
                                    );
                                  }}
                                  className="rounded accent-slate-900"
                                />
                                <span className="font-medium text-slate-800">{u.title}</span>
                              </label>
                            );
                          })}
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1.5">2. 教材頁碼範圍（選填）</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            placeholder="起始頁 (如 70)"
                            value={rangePageStart}
                            onChange={(e) => setRangePageStart(e.target.value)}
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs"
                          />
                          <span className="text-slate-400">~</span>
                          <input
                            type="number"
                            placeholder="結束頁 (如 82)"
                            value={rangePageEnd}
                            onChange={(e) => setRangePageEnd(e.target.value)}
                            className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs"
                          />
                        </div>
                        <div className="mt-2">
                          <label className="block text-xs font-bold text-slate-700 mb-1">
                            難度係數：{targetDifficulty.toFixed(1)} · 時長：{durationMin} 分
                          </label>
                          <input
                            type="range"
                            min={1.0}
                            max={5.0}
                            step={0.1}
                            value={targetDifficulty}
                            onChange={(e) => setTargetDifficulty(Number(e.target.value))}
                            className="w-full accent-slate-900"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1.5">3. 題型層級篩選</label>
                        <div className="grid grid-cols-2 gap-1.5 text-xs">
                          {[
                            { k: "CONCEPT", label: "核心觀念" },
                            { k: "DRILL", label: "基礎演練" },
                            { k: "ADVANCED", label: "進階挑戰" },
                            { k: "GIFTED_A", label: "資優 A" },
                            { k: "GIFTED_B", label: "資優 B" },
                            { k: "GIFTED_C", label: "資優壓軸" },
                          ].map((cat) => {
                            const checked = rangeCategories.includes(cat.k);
                            return (
                              <label key={cat.k} className="flex items-center gap-1.5 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={() =>
                                    setRangeCategories((prev) =>
                                      checked ? prev.filter((x) => x !== cat.k) : [...prev, cat.k]
                                    )
                                  }
                                  className="rounded accent-slate-900"
                                />
                                <span>{cat.label}</span>
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {latestDoc && (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between">
                      <div className="text-sm text-emerald-900">
                        <span className="font-bold">範圍教材 PDF 產出完成！</span>
                        <span className="ml-2 text-xs">
                          {latestDoc.pdf_filename}（共 {latestDoc.page_count} 頁）
                        </span>
                      </div>
                      <a
                        href={`${API_BASE}${latestDoc.download_url}`}
                        target="_blank"
                        rel="noreferrer"
                        className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold px-3.5 py-2 rounded-lg flex items-center gap-1.5"
                      >
                        <Download className="w-4 h-4" />
                        下載 PDF
                      </a>
                    </div>
                  )}

                  {rangePlan && (
                    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
                      <div className="text-xs font-bold text-slate-700">
                        篩選結果：{rangePlan.unit_title}（已自動選入 {rangeSelectedIds.length} / {rangePlan.items.length} 頁）
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {rangePlan.items.map((item) => (
                          <label
                            key={item.slide.id}
                            className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 cursor-pointer ${
                              item.selected ? "border-slate-900 bg-slate-50" : "border-slate-200 opacity-60"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={rangeSelectedIds.includes(item.slide.id)}
                              onChange={() => {
                                const next = rangeSelectedIds.includes(item.slide.id)
                                  ? rangeSelectedIds.filter((id) => id !== item.slide.id)
                                  : [...rangeSelectedIds, item.slide.id];
                                setRangeSelectedIds(next);
                                handleRangePreview(next);
                              }}
                              className="mt-0.5 rounded accent-slate-900"
                            />
                            <div className="min-w-0 flex-1">
                              <div className="flex justify-between font-bold text-slate-900">
                                <span>{item.slide.badge_text}</span>
                                <span className="font-mono text-slate-500">{item.time_slot}</span>
                              </div>
                              <div className="text-slate-600 truncate">{item.slide.page_ref}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 分頁 3：歷史紀錄與已產 PDF */}
              {activeTab === "history" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
                    <h3 className="text-sm font-bold text-slate-900">已產出的備課 PDF ({docs.length})</h3>
                    {docs.length === 0 ? (
                      <p className="text-xs text-slate-400">尚無產出紀錄</p>
                    ) : (
                      <div className="space-y-2">
                        {docs.map((d) => (
                          <div
                            key={d.id}
                            className="p-3 rounded-lg border border-slate-200 flex items-center justify-between gap-2 text-xs"
                          >
                            <div className="min-w-0">
                              <div className="font-bold text-slate-900 truncate">{d.unit_title}</div>
                              <div className="text-slate-500 mt-0.5">
                                難度 {d.target_difficulty.toFixed(1)} · {d.duration_min}分 · {d.page_count}頁
                              </div>
                            </div>
                            <a
                              href={`${API_BASE}${d.download_url}`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-2.5 py-1.5 bg-slate-900 text-white rounded-md font-bold flex items-center gap-1 shrink-0"
                            >
                              <Download className="w-3.5 h-3.5" />
                              下載
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
                    <h3 className="text-sm font-bold text-slate-900">課後回報與評分紀錄 ({logs.length})</h3>
                    {logs.length === 0 ? (
                      <p className="text-xs text-slate-400">尚無課後回報紀錄</p>
                    ) : (
                      <div className="space-y-2">
                        {logs.map((l) => (
                          <div key={l.id} className="p-3 rounded-lg border border-slate-200 text-xs space-y-1">
                            <div className="flex justify-between font-bold text-slate-900">
                              <span>{l.unit_title}</span>
                              <span>
                                難度 {l.calc_difficulty_before.toFixed(1)} → {l.calc_difficulty_after.toFixed(1)}
                              </span>
                            </div>
                            <div className="text-slate-600">{l.calc_reason}</div>
                            {l.notes && <div className="text-slate-500 italic">備註：{l.notes}</div>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {showUploader && (
        <MaterialUploaderModal
          onClose={() => setShowUploader(false)}
          onSuccess={async (unitId) => {
            const unitList = await apiFetch<Unit[]>("/api/units");
            setUnits(unitList);
            setSelectedUnitId(unitId);
            setRangeUnitIds((prev) => Array.from(new Set([...prev, unitId])));
          }}
        />
      )}
    </div>
  );
}
