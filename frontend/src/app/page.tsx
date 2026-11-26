"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, KeyRound, Loader2, ShieldCheck, UserCheck } from "lucide-react";
import { apiFetch, getToken, setToken, User } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("teacher_lin");
  const [password, setPassword] = useState("teacher123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiFetch<User>("/api/auth/me")
      .then((u) => {
        router.replace(u.role === "ADMIN" ? "/admin" : "/instructor");
      })
      .catch(() => setToken(null));
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await apiFetch<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setToken(access_token);
      const user = await apiFetch<User>("/api/auth/me");
      router.push(user.role === "ADMIN" ? "/admin" : "/instructor");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "登入失敗");
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
        <div className="bg-slate-900 text-white p-6">
          <div className="flex items-center gap-2.5 text-amber-400 text-sm font-bold mb-1">
            <BookOpen className="w-4 h-4" />
            TEACHER-MANAGE SYSTEM
          </div>
          <h1 className="text-xl font-extrabold tracking-tight">板書備課與難度評分系統</h1>
          <p className="text-slate-400 text-xs mt-1">
            依講師授課進度與課後評分，自動產出 A4 黑白印刷最佳化備課 PDF
          </p>
        </div>

        <form onSubmit={handleLogin} className="p-6 space-y-4">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">帳號</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">密碼</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-60"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
            登入系統
          </button>

          <div className="pt-4 border-t border-slate-100">
            <div className="text-xs font-semibold text-slate-500 mb-2">快速切換測試帳號：</div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => quickFill("teacher_lin", "teacher123")}
                className="flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-md border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium cursor-pointer"
              >
                <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                林老師
              </button>
              <button
                type="button"
                onClick={() => quickFill("teacher_chen", "teacher123")}
                className="flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-md border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium cursor-pointer"
              >
                <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                陳老師
              </button>
              <button
                type="button"
                onClick={() => quickFill("admin", "admin123")}
                className="flex items-center justify-center gap-1 text-xs py-1.5 px-2 rounded-md border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-900 font-semibold cursor-pointer"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                管理員
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
