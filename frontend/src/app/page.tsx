import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-5xl font-bold tracking-tight">
          数字<span className="text-primary-600">人格</span>
        </h1>
        <p className="text-xl text-[var(--color-text-muted)]">
          通过反思性 AI 对话，将你的个性蒸馏为数字孪生——像你一样思考、表达和回应。
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/interview/new"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            开始访谈
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-6 mt-12 text-left">
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">深度心理画像</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              多维度心理学框架映射你的个性特质、认知模式和沟通风格
            </p>
          </div>
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">11x 记忆蒸馏</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              结构化压缩算法保留你的独特用语，实现极致信息密度
            </p>
          </div>
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <h3 className="font-semibold mb-2">数字孪生导出</h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              生成可挂载的 SKILL.md，让 AI 准确模拟你的思维和行为模式
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
