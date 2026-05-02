"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";

import ChatInterface from "@/components/chat/ChatInterface";
import { useInterview } from "@/hooks/useInterview";

export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.id as string;
  const { sessionId, greeting, isStarting, error, startInterview } =
    useInterview();
  const [started, setStarted] = useState(interviewId !== "new");

  useEffect(() => {
    if (interviewId === "new" && !started) {
      startInterview().then((id) => {
        if (id) {
          router.replace(`/interview/${id}`);
          setStarted(true);
        }
      });
    }
  }, [interviewId, started, startInterview, router]);

  if (interviewId === "new" || isStarting) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-[var(--color-text-muted)] text-sm">正在准备访谈...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-red-500 text-sm">启动失败：{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="text-sm px-4 py-2 rounded-lg bg-black text-white hover:bg-[#1a1a1a] transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        >
          <span>&larr;</span>
          <span>返回</span>
        </Link>
        <h1 className="text-sm font-semibold">数字人格访谈</h1>
        <Link
          href={`/profile/${sessionId || interviewId}`}
          className="text-sm px-3 py-1.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] hover:border-[#d0d0d0] transition-all"
        >
          查看画像
        </Link>
      </header>
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          sessionId={sessionId || interviewId}
          initialGreeting={greeting || undefined}
        />
      </main>
    </div>
  );
}
