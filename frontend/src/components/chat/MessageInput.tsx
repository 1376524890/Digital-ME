"use client";

import { useState } from "react";
import VoiceRecorder from "@/components/voice/VoiceRecorder";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  };

  const handleTranscript = (transcript: string) => {
    onSend(transcript);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-3 py-4 items-end"
    >
      <div className="flex-1 flex items-center gap-2 px-2 py-1.5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] focus-within:border-[#b0b0b0] focus-within:ring-4 focus-within:ring-black/5 transition-all shadow-sm">
        <VoiceRecorder onTranscript={handleTranscript} disabled={disabled} />
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
          placeholder="输入你的消息..."
          className="flex-1 py-2.5 bg-transparent text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="mr-1 p-2 rounded-xl bg-black text-white disabled:opacity-20 disabled:grayscale transition-all shrink-0 shadow-sm"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.39 60.39 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.397 60.397 0 0 0 3.478 2.404Z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
