import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Teacher-Manage | 板書備課與難度評分系統",
  description: "依講師授課進度與課後評分，自動產出 A4 黑白印刷最佳化備課 PDF",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hant">
      <body className="antialiased bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
