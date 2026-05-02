const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface SSEEvent {
  type: "token" | "done";
  content?: string;
  ply_id?: string;
  sequence_num?: number;
}

export async function* streamChat(
  sessionId: string,
  text: string
): AsyncGenerator<SSEEvent> {
  const res = await fetch(
    `${API_BASE}/interview/${sessionId}/message/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }
  );

  if (!res.ok) {
    throw new Error(`SSE error ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          yield JSON.parse(data) as SSEEvent;
        } catch {
          // skip malformed events
        }
      }
    }
  }
}
