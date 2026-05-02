"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { streamChat } from "@/lib/sse";
import { api } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface CoverageData {
  presenting: number;
  predisposing: number;
  precipitating: number;
  perpetuating: number;
  protective: number;
  impact: number;
  overall: number;
}

interface Props {
  sessionId: string;
  initialGreeting?: string;
  initialMessages?: Message[];
  initialCoverage?: CoverageData | null;
  onCoverageUpdate?: (coverage: CoverageData) => void;
  onComplete?: () => void;
}

export default function ChatInterface({
  sessionId,
  initialGreeting,
  initialMessages,
  initialCoverage,
  onCoverageUpdate,
  onComplete,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const historyLoaded = useRef(false);

  // Load initial greeting (new session) or history (existing session)
  useEffect(() => {
    if (historyLoaded.current) return;

    if (initialMessages && initialMessages.length > 0) {
      setMessages(initialMessages);
      historyLoaded.current = true;
    } else if (initialGreeting) {
      setMessages([
        { id: "greeting", role: "assistant", content: initialGreeting },
      ]);
      historyLoaded.current = true;
    }
  }, [initialGreeting, initialMessages]);

  // Notify parent of initial coverage
  useEffect(() => {
    if (initialCoverage && onCoverageUpdate) {
      onCoverageUpdate(initialCoverage);
    }
  }, [initialCoverage]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  const handleSend = useCallback(
    async (text: string) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setStreamingContent("");

      let fullContent = "";
      let finalCoverage: CoverageData | null = null;
      try {
        for await (const event of streamChat(sessionId, text)) {
          if (event.type === "token" && event.content) {
            fullContent += event.content;
            setStreamingContent(fullContent);
          } else if (event.type === "done") {
            setMessages((prev) => [
              ...prev,
              {
                id: event.ply_id || crypto.randomUUID(),
                role: "assistant",
                content: fullContent,
              },
            ]);
            setStreamingContent("");
            // Coverage comes from the non-streaming endpoint, so poll it
          }
        }
      } catch (err) {
        console.error("Stream error:", err);
        // Fallback: use non-streaming endpoint
        try {
          const res = await api.sendMessage(sessionId, text);
          if (res) {
            setMessages((prev) => [
              ...prev,
              { id: res.ply_id, role: "assistant", content: res.response },
            ]);
            if (res.coverage) finalCoverage = res.coverage as CoverageData;
          }
        } catch (_) {}
      } finally {
        setIsStreaming(false);
      }

      // Fetch coverage after message
      try {
        const cov = await api.getCoverage(sessionId);
        if (cov && onCoverageUpdate) {
          onCoverageUpdate({ ...cov, overall: cov.overall ?? 0 });
        }
      } catch (_) {}
    },
    [sessionId, onCoverageUpdate]
  );

  return (
    <div className="h-full flex flex-col max-w-3xl mx-auto">
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scroll-smooth"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full text-[var(--color-text-muted)] text-sm">
            <p>AI 正在准备...</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        {isStreaming && streamingContent && (
          <MessageBubble
            role="assistant"
            content={streamingContent}
            isStreaming
          />
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="max-w-3xl mx-auto">
          <MessageInput onSend={handleSend} disabled={isStreaming} />
        </div>
      </div>
    </div>
  );
}
