"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface Props {
  text: string;
}

export default function VoicePlayer({ text }: Props) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const utteranceRef = useRef<any>(null);

  useEffect(() => {
    setIsSupported(!!(window as any).SpeechSynthesisUtterance);
  }, []);

  const speak = useCallback(() => {
    const SpeechSynthesisUtterance = (window as any).SpeechSynthesisUtterance;
    if (!SpeechSynthesisUtterance || !text) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [text]);

  if (!isSupported || !text) return null;

  return (
    <button
      onClick={speak}
      disabled={isSpeaking}
      className="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      title="Read aloud"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="currentColor"
        className={`w-4 h-4 ${isSpeaking ? "animate-pulse text-primary-600" : ""}`}
      >
        <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 0 0 1.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06Z" />
        <path d="M17.78 6.22a.75.75 0 1 0-1.06 1.06L18.44 9l-1.72 1.72a.75.75 0 1 0 1.06 1.06l1.72-1.72 1.72 1.72a.75.75 0 1 0 1.06-1.06L20.56 9l1.72-1.72a.75.75 0 1 0-1.06-1.06l-1.72 1.72-1.72-1.72Z" />
      </svg>
    </button>
  );
}
