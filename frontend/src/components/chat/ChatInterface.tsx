"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { streamChat } from "@/lib/sse";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Props {
  sessionId: string;
  initialGreeting?: string;
  onComplete?: () => void;
}

export default function ChatInterface({
  sessionId,
  initialGreeting,
  onComplete,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialGreeting) {
      setMessages([
        { id: "greeting", role: "assistant", content: initialGreeting },
      ]);
    }
  }, [initialGreeting]);

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
          }
        }
      } catch (err) {
        console.error("Stream error:", err);
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId]
  );

  return (
    <div className="h-full flex flex-col max-w-3xl mx-auto">
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scroll-smooth"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full text-[var(--color-text-muted)] text-sm">
            <p>等待访谈开始...</p>
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
