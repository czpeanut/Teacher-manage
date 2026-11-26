"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, LogOut, ShieldCheck, User as UserIcon } from "lucide-react";
import { setToken, User } from "@/lib/api";

interface NavbarProps {
  user: User;
  activeTab?: "instructor" | "admin";
}

export default function Navbar({ user, activeTab }: NavbarProps) {
  const router = useRouter();

  const handleLogout = () => {
    setToken(null);
    router.push("/");
  };

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 font-bold text-base tracking-tight">
            <BookOpen className="w-5 h-5 text-amber-400" />
            <span>板書備課與難度評分系統</span>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <Link
              href="/instructor"
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === "instructor"
                  ? "bg-slate-700 text-white"
                  : "text-slate-300 hover:text-white hover:bg-slate-800"
              }`}
            >
              講師備課工作台
            </Link>
            {user.role === "ADMIN" && (
              <Link
                href="/admin"
                className={`px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5 ${
                  activeTab === "admin"
                    ? "bg-amber-500 text-slate-950 font-semibold"
                    : "text-amber-300 hover:bg-slate-800"
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                管理員總控台
              </Link>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <UserIcon className="w-4 h-4 text-slate-400" />
            <span className="font-medium text-white">{user.name}</span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              {user.role === "ADMIN" ? "管理員" : "講師"}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-md hover:bg-slate-800 transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            登出
          </button>
        </div>
      </div>
    </header>
  );
}
