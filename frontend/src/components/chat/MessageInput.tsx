"use client";

import { useState } from "react";
import VoiceRecorder from "@/components/voice/VoiceRecorder";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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
      className="flex gap-2 py-3 items-center"
    >
      <VoiceRecorder onTranscript={handleTranscript} disabled={disabled} />
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder="输入你的消息..."
        className="flex-1 px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#b0b0b0] transition-colors disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="px-5 py-2.5 rounded-xl bg-black text-white text-sm font-medium hover:bg-[#1a1a1a] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        发送
      </button>
    </form>
  );
}
