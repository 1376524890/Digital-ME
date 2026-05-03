"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { generateUserId } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface InterviewState {
  sessionId: string | null;
  status: "active" | "completed" | null;
  greeting: string | null;
  messages: Message[];
  isStarting: boolean;
  error: string | null;
}

export function useInterview() {
  const [state, setState] = useState<InterviewState>({
    sessionId: null,
    status: null,
    greeting: null,
    messages: [],
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
        status: "active",
        greeting: result.greeting,
        messages: [],
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
      const data = await api.getInterviewState(sessionId);

      // Map backend messages to frontend Message format
      const history: Message[] = (data.messages || []).map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        }));

      setState({
        sessionId: data.session_id,
        status: data.status,
        greeting: data.greeting, // null if session already has messages
        messages: history,
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

  const abandonInterview = useCallback(async () => {
    if (!state.sessionId) return;
    await api.abandonInterview(state.sessionId);
  }, [state.sessionId]);

  return { ...state, startInterview, resumeInterview, endInterview, abandonInterview };
}
