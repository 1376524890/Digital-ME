"use client";

import dynamic from "next/dynamic";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const VoicePlayer = dynamic(() => import("@/components/voice/VoiceSettings"), {
  ssr: false,
});

interface Props {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function MessageBubble({ role, content, isStreaming }: Props) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl ${
          isUser
            ? "bg-black text-white rounded-br-md"
            : "bg-[var(--color-surface)] border border-[var(--color-border)] rounded-bl-md shadow-sm"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
        ) : (
          <div className="prose prose-sm max-w-none text-sm leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-0.5 bg-black animate-pulse align-text-bottom" />
            )}
            {!isStreaming && content && (
              <div className="mt-2 flex justify-end border-t border-[var(--color-border)] pt-2">
                <VoicePlayer text={content} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
