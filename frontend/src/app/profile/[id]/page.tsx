"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { api } from "@/lib/api";
import type { ProfileSnapshot, DimensionCoverage } from "@shared/types/index";

const DIM_LABELS: Record<string, string> = {
  presenting: "核心诉求",
  predisposing: "易感因素",
  precipitating: "诱发因素",
  perpetuating: "维持因素",
  protective: "保护因素",
  impact: "功能影响",
};

const TRAIT_LABELS: Record<string, string> = {
  o: "开放性",
  c: "尽责性",
  e: "外向性",
  a: "宜人性",
  n: "神经质",
};

const DIMENSION_KEYS = [
  "presenting",
  "predisposing",
  "precipitating",
  "perpetuating",
  "protective",
  "impact",
] as const;

export default function ProfilePage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [profile, setProfile] = useState<ProfileSnapshot | null>(null);
  const [coverage, setCoverage] = useState<DimensionCoverage | null>(null);
  const [skillMd, setSkillMd] = useState<string | null>(null);
  const [skillStatus, setSkillStatus] = useState<"pending" | "ready" | "error">("pending");
  const [loading, setLoading] = useState(true);
  const [showSkill, setShowSkill] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getProfile(sessionId).catch(() => null),
      api.getCoverage(sessionId).catch(() => null),
      api.getSkillMd(sessionId).catch(() => undefined),
    ]).then(([profileData, coverageData, skillData]) => {
      if (profileData) setProfile(profileData);
      if (coverageData) setCoverage(coverageData);
      if (typeof skillData === "string") {
        setSkillMd(skillData);
        setSkillStatus("ready");
      } else if (skillData === null) {
        setSkillStatus("pending");
      } else {
        setSkillStatus("error");
      }
      setLoading(false);
    });
  }, [sessionId]);

  const handleDownload = () => {
    if (!skillMd) return;
    setDownloading(true);
    const blob = new Blob([skillMd], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SKILL_${sessionId.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    setTimeout(() => setDownloading(false), 500);
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 sm:p-6 max-w-3xl mx-auto space-y-8">
      {/* Header with back button */}
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <Link
          href={`/interview/${sessionId}`}
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        >
          <span>&larr;</span>
          <span>返回访谈</span>
        </Link>
        {skillMd && (
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="px-4 py-2 rounded-xl bg-black text-white text-sm font-medium hover:bg-[#1a1a1a] transition-all disabled:opacity-50"
          >
            {downloading ? "导出中..." : "下载 SKILL.md"}
          </button>
        )}
      </header>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">你的数字人格画像</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          认知模式和沟通风格的快照
        </p>
      </div>

      {/* Dimension Coverage */}
      {coverage && (
        <section className="p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-lg font-semibold mb-5">维度覆盖度</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {DIMENSION_KEYS.map((key) => (
              <div key={key} className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-medium">{DIM_LABELS[key]}</span>
                  <span className="text-[var(--color-text-muted)] font-mono">
                    {Math.round((coverage[key] ?? 0) * 100)}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--color-bg)]">
                  <div
                    className="h-full rounded-full bg-black transition-all duration-700"
                    style={{ width: `${(coverage[key] ?? 0) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* OCEAN Scores */}
      {profile?.ocean_scores && Object.keys(profile.ocean_scores).length > 0 && (
        <section className="p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-lg font-semibold mb-5">大五人格 (OCEAN)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {Object.entries(profile.ocean_scores).map(([trait, value]) => (
              <div key={trait} className="text-center space-y-1.5">
                <div className="text-2xl font-bold font-mono">
                  {typeof value === "number" ? value.toFixed(2) : "—"}
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {TRAIT_LABELS[trait] || trait}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* PPPPPI Slots */}
      {profile?.pppppi_slots && Object.keys(profile.pppppi_slots).length > 0 && (
        <section className="p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-lg font-semibold mb-5">PPPPPI 心理画像</h2>
          <div className="space-y-4">
            {Object.entries(profile.pppppi_slots).map(([dim, slot]) => (
              <div key={dim} className="pb-4 border-b border-[var(--color-border)] last:border-0 last:pb-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-sm">
                    {DIM_LABELS[dim] || dim}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)] font-mono">
                    {(slot.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <ul className="text-sm text-[var(--color-text-muted)] space-y-1">
                  {slot.evidence.slice(0, 3).map((e, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-[var(--color-border)] shrink-0">&mdash;</span>
                      <span>{e}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* SKILL.md */}
      {skillMd ? (
        <section className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
          <button
            onClick={() => setShowSkill(!showSkill)}
            className="w-full p-6 flex items-center justify-between hover:bg-[var(--color-bg)] transition-colors"
          >
            <div className="text-left">
              <h2 className="text-lg font-semibold">SKILL.md 预览</h2>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                {showSkill ? "点击收起" : "点击展开查看完整内容"}
              </p>
            </div>
            <span
              className={`text-lg text-[var(--color-text-muted)] transition-transform duration-300 ${
                showSkill ? "rotate-180" : ""
              }`}
            >
              &#9660;
            </span>
          </button>
          {showSkill && (
            <div className="px-6 pb-6 border-t border-[var(--color-border)]">
              <div className="mt-4 p-6 rounded-xl bg-[var(--color-bg)] prose-skill text-sm max-h-[60vh] overflow-y-auto">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {skillMd}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </section>
      ) : (
        <section className="p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] space-y-2">
          <h2 className="text-lg font-semibold">SKILL.md</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            {skillStatus === "error"
              ? "SKILL.md 状态读取失败，请稍后刷新重试。"
              : "SKILL.md 尚未生成。完成访谈后会在这里提供预览与下载。"}
          </p>
        </section>
      )}

      {/* Empty state */}
      {!profile && (
        <div className="text-center py-16">
          <p className="text-[var(--color-text-muted)] text-sm">
            完成访谈后即可查看你的数字人格画像
          </p>
          <Link
            href="/interview/new"
            className="inline-block mt-4 px-5 py-2.5 rounded-xl bg-black text-white text-sm font-medium hover:bg-[#1a1a1a] transition-all"
          >
            开始访谈
          </Link>
        </div>
      )}

      {/* Bottom padding */}
      <div className="pb-8" />
    </div>
  );
}
