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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Set initial greeting
  useEffect(() => {
    if (initialGreeting) {
      setMessages([
        { id: "greeting", role: "assistant", content: initialGreeting },
      ]);
    }
  }, [initialGreeting]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
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
      <MessageInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
