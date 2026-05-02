import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Digital Me",
  description: "Create your AI digital twin through reflective conversation",
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
