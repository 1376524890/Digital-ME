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
  [key: string]: number;
}

interface Props {
  sessionId: string;
  initialGreeting?: string;
  initialMessages?: Message[];
  initialCoverage?: CoverageData | null;
  onCoverageUpdate?: (coverage: CoverageData) => void;
  onStreamingChange?: (isStreaming: boolean) => void;
  onComplete?: () => void;
  disabled?: boolean;
}

export default function ChatInterface({
  sessionId,
  initialGreeting,
  initialMessages,
  initialCoverage,
  onCoverageUpdate,
  onStreamingChange,
  onComplete,
  disabled,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const historyLoaded = useRef(false);

  const applySessionState = useCallback(
    async (stateSessionId: string) => {
      const data = await api.getInterviewState(stateSessionId);
      const restoredMessages =
        data.messages.length > 0
          ? data.messages.map((message) => ({
              id: message.id,
              role: message.role,
              content: message.content,
            }))
          : data.greeting
            ? [{ id: "greeting", role: "assistant" as const, content: data.greeting }]
            : [];
      setMessages(restoredMessages);
      if (data.coverage && onCoverageUpdate) {
        onCoverageUpdate({ ...data.coverage, overall: data.coverage.overall ?? 0 });
      }
    },
    [onCoverageUpdate]
  );

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
  }, [initialCoverage, onCoverageUpdate]);

  useEffect(() => {
    onStreamingChange?.(isStreaming);
  }, [isStreaming, onStreamingChange]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  const handleSend = useCallback(
    async (text: string) => {
      setStreamError(null);
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setStreamingContent("");

      let fullContent = "";
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
            if (event.coverage && onCoverageUpdate) {
              onCoverageUpdate(event.coverage);
            }
            setStreamingContent("");
          }
        }
      } catch (err) {
        console.error("Stream error:", err);
        try {
          await applySessionState(sessionId);
        } catch {
          setStreamError("这条消息同步失败，请重试。");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [applySessionState, onCoverageUpdate, sessionId]
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
        {streamError && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {streamError}
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
          <MessageInput onSend={handleSend} disabled={isStreaming || disabled} />
        </div>
      </div>
    </div>
  );
}
