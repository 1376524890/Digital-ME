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
        error: err instanceof Error ? err.message : "Failed to start",
      }));
      return null;
    }
  }, []);

  const endInterview = useCallback(async () => {
    if (!state.sessionId) return;
    await api.endInterview(state.sessionId);
  }, [state.sessionId]);

  return { ...state, startInterview, endInterview };
}
