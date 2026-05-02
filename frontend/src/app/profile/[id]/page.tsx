"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ProfileSnapshot, DimensionCoverage } from "@shared/types/index";

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
        <h1 className="text-3xl font-bold">Your Digital Profile</h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          A snapshot of your cognitive patterns and communication style
        </p>
      </header>

      {coverage && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold mb-4">Dimension Coverage</h2>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(coverage).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="capitalize">{key}</span>
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

      {profile && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-xl font-semibold mb-4">OCEAN Scores</h2>
          <div className="grid grid-cols-5 gap-4">
            {["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"].map(
              (trait) => (
                <div key={trait} className="text-center space-y-1">
                  <div className="text-2xl font-bold text-primary-600">
                    {profile.ocean_scores?.[trait[0]]?.toFixed(2) || "—"}
                  </div>
                  <div className="text-xs text-[var(--color-text-muted)] capitalize">
                    {trait}
                  </div>
                </div>
              )
            )}
          </div>
        </section>
      )}

      {skillMd && (
        <section className="p-6 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">SKILL.md Preview</h2>
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
              Download SKILL.md
            </button>
          </div>
          <pre className="p-4 rounded-lg bg-[var(--color-bg)] text-sm overflow-x-auto max-h-96">
            {skillMd}
          </pre>
        </section>
      )}

      {!profile && (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          <p>Complete your interview to see your digital profile.</p>
        </div>
      )}
    </div>
  );
}
