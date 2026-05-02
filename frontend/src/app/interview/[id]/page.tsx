"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import ChatInterface, { type CoverageData } from "@/components/chat/ChatInterface";
import DimensionCoverage from "@/components/interview/DimensionCoverage";
import { useInterview } from "@/hooks/useInterview";

export default function InterviewPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.id as string;
  const { sessionId, greeting, messages, isStarting, error, startInterview, resumeInterview } =
    useInterview();
  const [ready, setReady] = useState(false);
  const [coverage, setCoverage] = useState<CoverageData | null>(null);

  useEffect(() => {
    if (ready) return;

    if (interviewId === "new") {
      startInterview().then((id) => {
        if (id) {
          router.replace(`/interview/${id}`);
          setReady(true);
        }
      });
    } else {
      resumeInterview(interviewId).then((data) => {
        if (data) {
          setReady(true);
          // Set initial coverage from resume data
          if (data.coverage) {
            setCoverage(data.coverage);
          }
        }
      });
    }
  }, [interviewId, ready, startInterview, resumeInterview, router]);

  const handleCoverageUpdate = useCallback((cov: CoverageData) => {
    setCoverage(cov);
  }, []);

  if (!ready || isStarting) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-[var(--color-text-muted)] text-sm">
            {interviewId === "new" ? "正在准备访谈..." : "正在加载会话..."}
          </p>
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

  const activeSessionId = sessionId || interviewId;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0 gap-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors shrink-0"
        >
          <span>&larr;</span>
          <span>返回</span>
        </Link>

        {/* Progress bar in center */}
        <div className="flex-1 flex justify-center">
          <DimensionCoverage coverage={coverage} />
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            href={`/profile/${activeSessionId}`}
            className="text-sm px-3 py-1.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] hover:border-[#d0d0d0] transition-all"
          >
            查看画像
          </Link>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          sessionId={activeSessionId}
          initialGreeting={greeting || undefined}
          initialMessages={messages.length > 0 ? messages : undefined}
          initialCoverage={coverage}
          onCoverageUpdate={handleCoverageUpdate}
        />
      </main>
    </div>
  );
}
