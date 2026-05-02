import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Digital Me - 数字人格",
  description: "通过反思性对话，用 AI 蒸馏你的数字人格",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
