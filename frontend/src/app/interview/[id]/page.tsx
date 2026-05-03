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
  const { sessionId, status, greeting, messages, isStarting, error, startInterview, resumeInterview, abandonInterview } =
    useInterview();
  const [ready, setReady] = useState(false);
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [showConfirmRestart, setShowConfirmRestart] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [restartError, setRestartError] = useState<string | null>(null);
  const [isChatStreaming, setIsChatStreaming] = useState(false);

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
            setCoverage({ ...data.coverage, overall: data.coverage.overall ?? 0 });
          }
        }
      });
    }
  }, [interviewId, ready, startInterview, resumeInterview, router]);

  const handleCoverageUpdate = useCallback((cov: CoverageData) => {
    setCoverage(cov);
  }, []);

  const handleRestart = useCallback(async () => {
    setRestarting(true);
    setRestartError(null);
    try {
      await abandonInterview();
      setShowConfirmRestart(false);
      setRestarting(false);
      setReady(false);
      setCoverage(null);
      router.push("/interview/new");
      return;
    } catch (err) {
      setRestartError(err instanceof Error ? err.message : "放弃当前访谈失败");
    }
    setRestarting(false);
  }, [abandonInterview, router]);

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

  const activeSessionId = sessionId || interviewId;
  const isCompleted = status === "completed";

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="px-4 sm:px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex flex-col sm:flex-row items-stretch sm:items-center justify-between shrink-0 gap-3 sm:gap-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors shrink-0"
        >
          <span>&larr;</span>
          <span>返回</span>
        </Link>

        {/* Progress bar in center */}
        <div className="flex-1 flex justify-center sm:justify-center">
          <DimensionCoverage coverage={coverage} />
        </div>

        <div className="flex flex-col items-stretch sm:items-end gap-2 shrink-0">
          <div className="flex flex-wrap items-center justify-start sm:justify-end gap-2 sm:gap-3">
            <Link
              href={`/profile/${activeSessionId}`}
              className="text-sm px-3 py-1.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] hover:border-[#d0d0d0] transition-all"
            >
              查看画像
            </Link>
            {isCompleted ? (
              <Link
                href="/interview/new"
                className="text-sm px-3 py-1.5 rounded-lg bg-black text-white hover:bg-[#1a1a1a] transition-colors"
              >
                开始新访谈
              </Link>
            ) : showConfirmRestart ? (
              <>
                <button
                  onClick={handleRestart}
                  disabled={restarting || isChatStreaming}
                  className="text-xs px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {restarting ? "处理中..." : "确认放弃"}
                </button>
                <button
                  onClick={() => {
                    setShowConfirmRestart(false);
                    setRestartError(null);
                  }}
                  disabled={restarting}
                  className="text-xs px-3 py-1.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] disabled:opacity-50 transition-all"
                >
                  取消
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowConfirmRestart(true)}
                disabled={isChatStreaming}
                className="text-sm px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 disabled:opacity-50 transition-all"
              >
                放弃并重开
              </button>
            )}
          </div>
          {showConfirmRestart && !isCompleted && (
            <p className="text-xs text-[var(--color-text-muted)]">
              放弃当前访谈会删除本轮进度，然后重新开始。
            </p>
          )}
          {restartError && (
            <p className="text-xs text-red-600">{restartError}</p>
          )}
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        {isCompleted && (
          <div className="mx-auto max-w-3xl px-4 sm:px-6 pt-4">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm text-[var(--color-text-muted)]">
              当前访谈已完成，聊天记录以只读方式保留。你可以查看画像，或开始新的访谈。
            </div>
          </div>
        )}
        <ChatInterface
          sessionId={activeSessionId}
          initialGreeting={greeting || undefined}
          initialMessages={messages.length > 0 ? messages : undefined}
          initialCoverage={coverage}
          onCoverageUpdate={handleCoverageUpdate}
          onStreamingChange={setIsChatStreaming}
          disabled={isCompleted || restarting}
        />
      </main>
    </div>
  );
}
