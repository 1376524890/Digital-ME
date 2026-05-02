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
}

export interface CoverageResponse {
  presenting: number;
  predisposing: number;
  precipitating: number;
  perpetuating: number;
  protective: number;
  impact: number;
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

  getCoverage: (sessionId: string) =>
    request<CoverageResponse>(`/profile/${sessionId}/coverage`),

  getProfile: (sessionId: string) =>
    request<any>(`/profile/${sessionId}`),

  getSkillMd: (sessionId: string) =>
    fetch(`${API_BASE}/export/${sessionId}/skill.md`).then((r) => r.text()),
};
