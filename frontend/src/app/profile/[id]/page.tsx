"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

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

export default function ProfilePage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [profile, setProfile] = useState<ProfileSnapshot | null>(null);
  const [coverage, setCoverage] = useState<DimensionCoverage | null>(null);
  const [skillMd, setSkillMd] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getProfile(sessionId).catch(() => null),
      api.getCoverage(sessionId).catch(() => null),
      api.getSkillMd(sessionId).catch(() => null),
    ]).then(([profileData, coverageData, skillData]) => {
      if (profileData) setProfile(profileData);
      if (coverageData) setCoverage(coverageData);
      if (skillData) setSkillMd(skillData);
      setLoading(false);
    });
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-bold">你的数字人格画像</h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          认知模式和沟通风格的快照
        </p>
      </header>

      {coverage && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold mb-4">维度覆盖度</h2>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(coverage).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{DIM_LABELS[key] || key}</span>
                  <span className="text-[var(--color-text-muted)]">
                    {Math.round(value * 100)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-[var(--color-bg)]">
                  <div
                    className="h-full rounded-full bg-primary-600 transition-all"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {profile?.ocean_scores && Object.keys(profile.ocean_scores).length > 0 && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold mb-4">大五人格 (OCEAN)</h2>
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(profile.ocean_scores).map(([trait, value]) => (
              <div key={trait} className="text-center space-y-1">
                <div className="text-2xl font-bold text-primary-600">
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

      {profile?.pppppi_slots && Object.keys(profile.pppppi_slots).length > 0 && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold mb-4">PPPPPI 心理画像</h2>
          <div className="space-y-3">
            {Object.entries(profile.pppppi_slots).map(([dim, slot]) => (
              <div key={dim}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm">
                    {DIM_LABELS[dim] || dim}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    置信度 {(slot.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <ul className="text-sm text-[var(--color-text-muted)] list-disc list-inside">
                  {slot.evidence.slice(0, 3).map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {skillMd && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">SKILL.md 预览</h2>
            <button
              onClick={() => {
                const blob = new Blob([skillMd], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `SKILL_${sessionId}.md`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              下载 SKILL.md
            </button>
          </div>
          <pre className="p-4 rounded-lg bg-[var(--color-bg)] text-sm overflow-x-auto max-h-96">
            {skillMd}
          </pre>
        </section>
      )}

      {!profile && (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          <p>完成访谈后即可查看你的数字人格画像。</p>
        </div>
      )}
    </div>
  );
}
