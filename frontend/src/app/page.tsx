import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-5xl font-bold tracking-tight">
          Digital <span className="text-primary-600">Me</span>
        </h1>
        <p className="text-xl text-[var(--color-text-muted)]">
          Through reflective AI conversation, distill your personality into a
          digital twin that thinks, speaks, and responds like you.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/interview/new"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            Start Your Interview
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-6 mt-12 text-left">
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">Deep Profiling</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              Multi-dimensional psychological mapping of your personality
            </p>
          </div>
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">Memory Distillation</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              11x structured compression while preserving your unique voice
            </p>
          </div>
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">Digital Twin</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              A mountable SKILL.md that mirrors your cognitive patterns
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
