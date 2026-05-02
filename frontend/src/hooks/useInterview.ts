"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { generateUserId } from "@/lib/utils";

interface InterviewState {
  sessionId: string | null;
  greeting: string | null;
  isStarting: boolean;
  error: string | null;
}

export function useInterview() {
  const [state, setState] = useState<InterviewState>({
    sessionId: null,
    greeting: null,
    isStarting: false,
    error: null,
  });

  const startInterview = useCallback(async (context?: string) => {
    setState((s) => ({ ...s, isStarting: true, error: null }));
    try {
      const userId = generateUserId();
      const result = await api.startInterview(userId, context);
      setState({
        sessionId: result.session_id,
        greeting: result.greeting,
        isStarting: false,
        error: null,
      });
      return result.session_id;
    } catch (err) {
      setState((s) => ({
        ...s,
        isStarting: false,
        error: err instanceof Error ? err.message : "启动失败",
      }));
      return null;
    }
  }, []);

  const resumeInterview = useCallback(async (sessionId: string) => {
    setState((s) => ({ ...s, isStarting: true, error: null }));
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interview/${sessionId}/state`
      );
      if (!res.ok) throw new Error("会话不存在");
      const data = await res.json();
      setState({
        sessionId: data.session_id,
        greeting: data.greeting, // null if session already has messages
        isStarting: false,
        error: null,
      });
      return data;
    } catch (err) {
      setState((s) => ({
        ...s,
        isStarting: false,
        error: err instanceof Error ? err.message : "加载失败",
      }));
      return null;
    }
  }, []);

  const endInterview = useCallback(async () => {
    if (!state.sessionId) return;
    await api.endInterview(state.sessionId);
  }, [state.sessionId]);

  return { ...state, startInterview, resumeInterview, endInterview };
}
