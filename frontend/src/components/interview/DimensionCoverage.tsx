"use client";

import type { CoverageData } from "@/components/chat/ChatInterface";

const DIM_LABELS: Record<string, string> = {
  presenting: "核心诉求",
  predisposing: "易感因素",
  precipitating: "诱发因素",
  perpetuating: "维持因素",
  protective: "保护因素",
  impact: "功能影响",
};

interface Props {
  coverage: CoverageData | null | undefined;
}

export default function DimensionCoverage({ coverage }: Props) {
  if (!coverage) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
        <span className="w-2 h-2 rounded-full bg-[var(--color-border)]" />
        <span>初始化中...</span>
      </div>
    );
  }

  const overall = coverage.overall ?? 0;
  const pct = Math.round(overall * 100);

  return (
    <div className="flex items-center gap-2">
      {/* Overall progress ring */}
      <div className="relative w-7 h-7 shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 32 32">
          <circle
            cx="16" cy="16" r="13"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="3"
          />
          <circle
            cx="16" cy="16" r="13"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${overall * 81.68} 81.68`}
            className="text-black transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-[9px] font-semibold">
          {pct}
        </span>
      </div>

      {/* Dimension bars */}
      <div className="flex gap-1">
        {Object.entries(DIM_LABELS).map(([key, label]) => {
          const val = coverage[key] ?? 0;
          return (
            <div
              key={key}
              className="relative group"
              title={`${label}: ${Math.round(val * 100)}%`}
            >
              <div className="w-1.5 h-6 rounded-full bg-[var(--color-border)] overflow-hidden">
                <div
                  className="w-full rounded-full bg-black transition-all duration-500"
                  style={{
                    height: `${val * 100}%`,
                    marginTop: "auto",
                  }}
                />
              </div>
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-0.5 rounded bg-black text-white text-[10px] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {label}: {Math.round(val * 100)}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
