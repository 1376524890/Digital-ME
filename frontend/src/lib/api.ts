import type { ProfileSnapshot } from "@shared/types/index";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export interface StartResponse {
  session_id: string;
  greeting: string;
}

export interface SendResponse {
  ply_id: string;
  response: string;
  sequence_num: number;
  coverage?: CoverageResponse;
  gaps?: Record<string, number>;
  strategy?: string;
  target_dimension?: string;
}

export interface CoverageResponse {
  presenting: number;
  predisposing: number;
  precipitating: number;
  perpetuating: number;
  protective: number;
  impact: number;
  overall?: number;
}

export interface InterviewStateMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sequence_num: number;
}

export interface InterviewStateResponse {
  session_id: string;
  status: "active" | "completed";
  message_count: number;
  greeting: string | null;
  messages: InterviewStateMessage[];
  coverage: CoverageResponse;
}

export const api = {
  startInterview: (userId: string, context?: string) =>
    request<StartResponse>("/interview/start", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, context }),
    }),

  sendMessage: (sessionId: string, text: string) =>
    request<SendResponse>(`/interview/${sessionId}/message`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  endInterview: (sessionId: string) =>
    request<{ session_id: string; status: string }>(
      `/interview/${sessionId}/end`,
      { method: "POST" }
    ),

  abandonInterview: (sessionId: string) =>
    request<{ session_id: string; status: string }>(
      `/interview/${sessionId}/abandon`,
      { method: "POST" }
    ),

  getInterviewState: (sessionId: string) =>
    request<InterviewStateResponse>(`/interview/${sessionId}/state`),

  getCoverage: (sessionId: string) =>
    request<CoverageResponse>(`/profile/${sessionId}/coverage`),

  getProfile: (sessionId: string) =>
    request<ProfileSnapshot>(`/profile/${sessionId}`),

  getSkillMd: async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/export/${sessionId}/skill.md`);
    if (res.status === 404) return null;
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`API error ${res.status}: ${body}`);
    }
    return res.text();
  },
};
