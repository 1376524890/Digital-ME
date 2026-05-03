"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

function FlowingDigits() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const chars = "01010111001001110010101011100101001110001010101001";
    const fontSize = 14;
    const columns = Math.floor(canvas.width / fontSize);
    const drops: number[] = Array(columns).fill(0).map(() =>
      Math.random() * canvas.height
    );
    const speeds: number[] = Array(columns).fill(0).map(() =>
      0.3 + Math.random() * 0.7
    );

    let frame = 0;
    let animId: number;

    const draw = () => {
      ctx.fillStyle = "rgba(255, 255, 255, 0.03)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "rgba(0, 0, 0, 0.06)";
      ctx.font = `${fontSize}px "JetBrains Mono", monospace`;

      for (let i = 0; i < drops.length; i++) {
        if (frame % Math.ceil(1 / speeds[i]) !== 0) continue;
        const char = chars[Math.floor(Math.random() * chars.length)];
        const x = i * fontSize;
        const y = drops[i];
        ctx.fillText(char, x, y);
        drops[i] += fontSize * speeds[i];
        if (drops[i] > canvas.height && Math.random() > 0.98) {
          drops[i] = -fontSize;
        }
      }
      frame++;
      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 sm:p-8 relative">
      <FlowingDigits />

      <div className="max-w-2xl text-center space-y-8 relative" style={{ zIndex: 1 }}>
        {/* Hero */}
        <div className="space-y-4 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--color-border)] text-xs text-[var(--color-text-muted)] tracking-widest uppercase mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
            Digital Twin Distillation
          </div>
          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight">
            数字<span className="text-[var(--color-text-muted)]">人格</span>
          </h1>
          <p className="text-base sm:text-lg text-[var(--color-text-muted)] max-w-md mx-auto leading-relaxed">
            通过反思性 AI 对话，将你的个性蒸馏为数字孪生
            <br />
            像你一样思考、表达和回应
          </p>
        </div>

        {/* CTA */}
        <div
          className="flex gap-4 justify-center animate-fade-in-up"
          style={{ animationDelay: "0.2s" }}
        >
          <Link
            href="/interview/new"
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-black text-white font-medium hover:bg-[#1a1a1a] transition-all duration-300 hover:shadow-lg hover:shadow-black/10"
          >
            <span>开始访谈</span>
            <span className="transition-transform duration-300 group-hover:translate-x-0.5">
              &rarr;
            </span>
          </Link>
        </div>

        {/* Feature cards */}
        <div
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-12 sm:mt-16 text-left animate-fade-in-up"
          style={{ animationDelay: "0.4s" }}
        >
          {[
            {
              num: "01",
              title: "深度心理画像",
              desc: "多维度心理学框架映射你的个性特质、认知模式和沟通风格",
            },
            {
              num: "02",
              title: "11x 记忆蒸馏",
              desc: "结构化压缩算法保留你的独特用语，实现极致信息密度",
            },
            {
              num: "03",
              title: "数字孪生导出",
              desc: "生成可挂载的 SKILL.md，让 AI 准确模拟你的思维和行为模式",
            },
          ].map((card) => (
            <div
              key={card.num}
              className="group p-5 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[#d0d0d0] transition-all duration-300"
            >
              <div className="text-xs text-[var(--color-text-muted)] mb-3 font-mono tracking-widest">
                {card.num}
              </div>
              <h3 className="font-semibold mb-2 text-sm">{card.title}</h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
                {card.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <p
          className="text-xs text-[var(--color-text-muted)] pt-8 animate-fade-in-up"
          style={{ animationDelay: "0.6s" }}
        >
          黑白极简 &middot; 数字人格
        </p>
      </div>
    </main>
  );
}
