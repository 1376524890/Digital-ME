"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-[var(--color-text-muted)]">
            Preparing your interview...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-red-500">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="text-primary-600 hover:underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between">
        <h1 className="text-lg font-semibold">Digital Me Interview</h1>
        <button
          onClick={() => router.push(`/profile/${sessionId || interviewId}`)}
          className="text-sm text-primary-600 hover:underline"
        >
          View Profile
        </button>
      </header>
      <main className="flex-1 max-w-4xl w-full mx-auto">
        <ChatInterface
          sessionId={sessionId || interviewId}
          initialGreeting={greeting || undefined}
        />
      </main>
    </div>
  );
}
