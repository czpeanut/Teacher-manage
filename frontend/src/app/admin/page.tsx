"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  BookOpen,
  FileUp,
  History,
  Layers,
  Loader2,
  Plus,
  Save,
  SlidersHorizontal,
  Users,
  X,
} from "lucide-react";
import DifficultyBadge from "@/components/DifficultyBadge";
import MaterialUploaderModal from "@/components/MaterialUploaderModal";
import Navbar from "@/components/Navbar";
import {
  apiFetch,
  ClassGroup,
  DifficultyHistory,
  Slide,
  Unit,
  UnitDetail,
  User,
} from "@/lib/api";

interface OverviewData {
  instructors_count: number;
  classes_count: number;
  units_count: number;
  logs_count: number;
  docs_count: number;
  avg_difficulty: number;
  alert_classes: { id: number; name: string; difficulty: number; last_delta: number }[];
}

export default function AdminDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [instructors, setInstructors] = useState<User[]>([]);
  const [tab, setTab] = useState<"classes" | "units">("classes");

  // 調整進度與評分抽屜狀態
  const [editingClass, setEditingClass] = useState<ClassGroup | null>(null);
  const [ovUnitId, setOvUnitId] = useState<number>(1);
  const [ovSlideOrder, setOvSlideOrder] = useState<number>(0);
  const [ovDifficulty, setOvDifficulty] = useState<number>(3.0);
  const [ovDuration, setOvDuration] = useState<number>(180);
  const [ovNote, setOvNote] = useState<string>("");
  const [ovReason, setOvReason] = useState<string>("管理員審核後調整");
  const [savingOverride, setSavingOverride] = useState(false);
  const [historyList, setHistoryList] = useState<DifficultyHistory[]>([]);

  // 教材庫檢視
  const [selectedUnitDetail, setSelectedUnitDetail] = useState<UnitDetail | null>(null);
  const [showUploader, setShowUploader] = useState(false);
  const [showNewClassModal, setShowNewClassModal] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassInstructorId, setNewClassInstructorId] = useState<number>(0);
  const [newClassUnitId, setNewClassUnitId] = useState<number>(0);
  const [newClassDiff, setNewClassDiff] = useState<number>(3.0);

  const loadAll = useCallback(async () => {
    try {
      const me = await apiFetch<User>("/api/auth/me");
      if (me.role !== "ADMIN") {
        router.replace("/instructor");
        return;
      }
      setUser(me);
      const [ov, cls, unt, inst] = await Promise.all([
        apiFetch<OverviewData>("/api/admin/overview"),
        apiFetch<ClassGroup[]>("/api/classes"),
        apiFetch<Unit[]>("/api/units"),
        apiFetch<User[]>("/api/admin/instructors"),
      ]);
      setOverview(ov);
      setClasses(cls);
      setUnits(unt);
      setInstructors(inst);
      if (inst.length > 0 && newClassInstructorId === 0) setNewClassInstructorId(inst[0].id);
      if (unt.length > 0 && newClassUnitId === 0) setNewClassUnitId(unt[0].id);
    } catch {
      router.replace("/");
    }
  }, [router, newClassInstructorId, newClassUnitId]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const openEditDrawer = async (c: ClassGroup) => {
    setEditingClass(c);
    setOvUnitId(c.current_unit_id || (units[0]?.id ?? 1));
    setOvSlideOrder(c.last_completed_slide_order);
    setOvDifficulty(c.current_difficulty);
    setOvDuration(c.default_duration_min);
    setOvNote(c.admin_note || "");
    setOvReason("管理員檢視進度後手動調整");
    const hist = await apiFetch<DifficultyHistory[]>(`/api/classes/${c.id}/difficulty-history`);
    setHistoryList(hist);
  };

  const handleSaveOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingClass) return;
    setSavingOverride(true);
    try {
      await apiFetch(`/api/classes/${editingClass.id}/override`, {
        method: "POST",
        body: JSON.stringify({
          current_unit_id: ovUnitId,
          last_completed_slide_order: ovSlideOrder,
          new_difficulty: ovDifficulty,
          default_duration_min: ovDuration,
          admin_note: ovNote,
          reason: ovReason,
        }),
      });
      await loadAll();
      const hist = await apiFetch<DifficultyHistory[]>(`/api/classes/${editingClass.id}/difficulty-history`);
      setHistoryList(hist);
      setEditingClass(null);
    } finally {
      setSavingOverride(false);
    }
  };

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClassName.trim()) return;
    await apiFetch("/api/admin/classes", {
      method: "POST",
      body: JSON.stringify({
        name: newClassName.trim(),
        grade_term: "五上",
        instructor_id: newClassInstructorId,
        current_unit_id: newClassUnitId,
        current_difficulty: newClassDiff,
        default_duration_min: 180,
      }),
    });
    setNewClassName("");
    setShowNewClassModal(false);
    await loadAll();
  };

  const loadUnitDetail = async (unitId: number) => {
    const detail = await apiFetch<UnitDetail>(`/api/units/${unitId}`);
    setSelectedUnitDetail(detail);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        載入中...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Navbar user={user} activeTab="admin" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* KPI 總覽卡片 */}
        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" /> 活躍講師 / 班級
              </div>
              <div className="text-2xl font-extrabold mt-1">
                {overview.instructors_count} <span className="text-sm font-semibold text-slate-400">/ {overview.classes_count} 班</span>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-500">全體平均難度</div>
              <div className="text-2xl font-extrabold mt-1 text-slate-900">
                {overview.avg_difficulty.toFixed(1)} <span className="text-sm font-normal text-slate-400">/ 5.0</span>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-500">教材單元數</div>
              <div className="text-2xl font-extrabold mt-1">{overview.units_count}</div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-slate-500">累計回報 / 已產 PDF</div>
              <div className="text-2xl font-extrabold mt-1">
                {overview.logs_count} <span className="text-sm font-semibold text-slate-400">/ {overview.docs_count} 份</span>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-xs font-semibold text-amber-700 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> 難度低檔 / 下降預警
              </div>
              <div className="text-2xl font-extrabold mt-1 text-amber-700">
                {overview.alert_classes.length} 班
              </div>
            </div>
          </div>
        )}

        {/* 分頁控制 */}
        <div className="flex items-center justify-between">
          <div className="flex bg-slate-200/70 p-1 rounded-lg">
            <button
              onClick={() => setTab("classes")}
              className={`px-4 py-1.5 rounded-md text-sm font-bold flex items-center gap-1.5 cursor-pointer ${
                tab === "classes" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              <SlidersHorizontal className="w-4 h-4" />
              全講師進度與評分調控
            </button>
            <button
              onClick={() => {
                setTab("units");
                if (units.length > 0 && !selectedUnitDetail) loadUnitDetail(units[0].id);
              }}
              className={`px-4 py-1.5 rounded-md text-sm font-bold flex items-center gap-1.5 cursor-pointer ${
                tab === "units" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              <Layers className="w-4 h-4" />
              教材庫與板書難度設定
            </button>
          </div>

          {tab === "classes" ? (
            <button
              onClick={() => setShowNewClassModal(true)}
              className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3.5 py-2 rounded-lg flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              新增班級
            </button>
          ) : (
            <button
              onClick={() => setShowUploader(true)}
              className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3.5 py-2 rounded-lg flex items-center gap-1.5 cursor-pointer"
            >
              <FileUp className="w-4 h-4 text-amber-400" />
              上傳教材自動組版
            </button>
          )}
        </div>

        {/* 全講師班級進度矩陣 */}
        {tab === "classes" && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-100 text-slate-600 text-xs uppercase border-b border-slate-200">
                    <th className="py-3 px-4 font-bold">班級名稱</th>
                    <th className="py-3 px-4 font-bold">授課講師</th>
                    <th className="py-3 px-4 font-bold">目前單元與進度</th>
                    <th className="py-3 px-4 font-bold">當前難度係數</th>
                    <th className="py-3 px-4 font-bold">管理員教學批示</th>
                    <th className="py-3 px-4 font-bold text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {classes.map((c) => {
                    const pct =
                      c.total_unit_slides > 0
                        ? Math.min(100, Math.round((c.last_completed_slide_order / c.total_unit_slides) * 100))
                        : 0;
                    return (
                      <tr key={c.id} className="hover:bg-slate-50/70">
                        <td className="py-3.5 px-4 font-bold text-slate-900">{c.name}</td>
                        <td className="py-3.5 px-4 text-slate-700">{c.instructor_name}</td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-800 text-xs">{c.current_unit_title}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="w-28 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-slate-800 h-full rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                            <span className="text-[11px] text-slate-500">
                              {c.last_completed_slide_order}/{c.total_unit_slides} 頁
                            </span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <DifficultyBadge
                            value={c.current_difficulty}
                            label={c.difficulty_label}
                            delta={c.last_delta}
                          />
                        </td>
                        <td className="py-3.5 px-4 max-w-xs">
                          <div className="text-xs text-slate-600 truncate">{c.admin_note || "—"}</div>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => openEditDrawer(c)}
                            className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg cursor-pointer"
                          >
                            調整進度 / 評分
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 教材庫檢視 */}
        {tab === "units" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-4 space-y-2.5">
              {units.map((u) => (
                <button
                  key={u.id}
                  onClick={() => loadUnitDetail(u.id)}
                  className={`w-full text-left p-4 rounded-xl border transition cursor-pointer ${
                    selectedUnitDetail?.id === u.id
                      ? "bg-white border-slate-900 ring-2 ring-slate-900/10"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {u.code}
                    </span>
                    <span className="text-xs text-slate-500">{u.slide_count} 頁板書</span>
                  </div>
                  <div className="font-bold text-sm mt-1.5">{u.title}</div>
                  <div className="text-xs text-slate-500 mt-1 line-clamp-2">{u.description}</div>
                </button>
              ))}
            </div>

            <div className="lg:col-span-8 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              {selectedUnitDetail ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h3 className="font-extrabold text-base flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-slate-700" />
                        {selectedUnitDetail.title}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">{selectedUnitDetail.description}</p>
                    </div>
                  </div>
                  <div className="space-y-2 max-h-[540px] overflow-y-auto">
                    {selectedUnitDetail.slides.map((s: Slide) => (
                      <div
                        key={s.id}
                        className="p-3 rounded-lg border border-slate-200 flex items-center justify-between gap-3 text-xs"
                      >
                        <div>
                          <span className="font-bold text-slate-900 mr-2">#{s.sort_order}</span>
                          <span className="px-2 py-0.5 rounded bg-slate-900 text-white font-bold mr-2">
                            {s.badge_text}
                          </span>
                          <span className="text-slate-700 font-medium">{s.page_ref}</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-500 shrink-0">
                          <span>層級：{s.category}</span>
                          <span>
                            適用難度：{s.min_difficulty.toFixed(1)} ~ {s.max_difficulty.toFixed(1)}
                          </span>
                          <span>{s.est_minutes} 分</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400 py-10 text-center">請選擇左側單元檢視板書清單</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 管理員調整進度與評分抽屜 */}
      {editingClass && (
        <div className="fixed inset-0 bg-slate-950/40 z-50 flex justify-end">
          <div className="bg-white w-full max-w-lg h-full overflow-y-auto p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900">{editingClass.name}</h2>
                <p className="text-xs text-slate-500">講師：{editingClass.instructor_name}</p>
              </div>
              <button
                onClick={() => setEditingClass(null)}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">指定授課單元</label>
                <select
                  value={ovUnitId}
                  onChange={(e) => setOvUnitId(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                >
                  {units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.title} ({u.slide_count}頁)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">已完成頁數進度</label>
                  <input
                    type="number"
                    min={0}
                    value={ovSlideOrder}
                    onChange={(e) => setOvSlideOrder(Number(e.target.value))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">預設課堂時長 (分)</label>
                  <select
                    value={ovDuration}
                    onChange={(e) => setOvDuration(Number(e.target.value))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value={120}>120 分鐘 (2小時)</option>
                    <option value={180}>180 分鐘 (3小時)</option>
                  </select>
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex justify-between text-xs font-bold text-slate-700">
                  <span>直接評分／覆寫難度係數</span>
                  <span className="text-base text-slate-900">{ovDifficulty.toFixed(1)} / 5.0</span>
                </div>
                <input
                  type="range"
                  min={1.0}
                  max={5.0}
                  step={0.1}
                  value={ovDifficulty}
                  onChange={(e) => setOvDifficulty(Number(e.target.value))}
                  className="w-full accent-slate-900"
                />
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>1.0 基礎穩固</span>
                  <span>3.0 標準進階</span>
                  <span>5.0 資優壓軸</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">調整原因（寫入審計紀錄）</label>
                <input
                  type="text"
                  value={ovReason}
                  onChange={(e) => setOvReason(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  給講師的備課指示（將顯示於備課封面頁）
                </label>
                <textarea
                  rows={3}
                  value={ovNote}
                  onChange={(e) => setOvNote(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>

              <button
                type="submit"
                disabled={savingOverride}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 cursor-pointer"
              >
                {savingOverride ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                儲存調整與評分
              </button>
            </form>

            <div className="pt-4 border-t border-slate-200 space-y-2.5">
              <h3 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5">
                <History className="w-3.5 h-3.5" /> 難度係數異動審計紀錄
              </h3>
              {historyList.length === 0 ? (
                <p className="text-xs text-slate-400">尚無異動紀錄</p>
              ) : (
                <div className="space-y-2">
                  {historyList.map((h) => (
                    <div key={h.id} className="p-2.5 rounded-lg border border-slate-200 text-xs space-y-1">
                      <div className="flex justify-between font-bold">
                        <span
                          className={
                            h.source === "ADMIN_OVERRIDE" ? "text-amber-700" : "text-blue-700"
                          }
                        >
                          {h.source === "ADMIN_OVERRIDE" ? "管理員覆寫" : "系統自動評分"}（{h.operator_name}）
                        </span>
                        <span>
                          {h.old_value.toFixed(1)} → {h.new_value.toFixed(1)}
                        </span>
                      </div>
                      <div className="text-slate-600">{h.reason}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 新增班級 Modal */}
      {showNewClassModal && (
        <div className="fixed inset-0 bg-slate-950/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-base">新增班級</h3>
              <button onClick={() => setShowNewClassModal(false)} className="text-slate-400 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateClass} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">班級名稱</label>
                <input
                  type="text"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                  placeholder="例：五上週六資優班"
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">指派講師</label>
                <select
                  value={newClassInstructorId}
                  onChange={(e) => setNewClassInstructorId(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                >
                  {instructors.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.username})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">起始單元</label>
                <select
                  value={newClassUnitId}
                  onChange={(e) => setNewClassUnitId(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                >
                  {units.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  初始難度係數：{newClassDiff.toFixed(1)}
                </label>
                <input
                  type="range"
                  min={1.0}
                  max={5.0}
                  step={0.1}
                  value={newClassDiff}
                  onChange={(e) => setNewClassDiff(Number(e.target.value))}
                  className="w-full accent-slate-900"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-slate-900 text-white font-bold py-2 rounded-lg text-sm cursor-pointer"
              >
                建立班級
              </button>
            </form>
          </div>
        </div>
      )}
      {showUploader && (
        <MaterialUploaderModal
          onClose={() => setShowUploader(false)}
          onSuccess={async (unitId) => {
            await loadAll();
            await loadUnitDetail(unitId);
          }}
        />
      )}
    </div>
  );
}
