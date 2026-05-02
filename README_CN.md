# Digital Me（数字人格）

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 24+](https://img.shields.io/badge/node-24+-green.svg)](https://nodejs.org/)
[![Next.js 15](https://img.shields.io/badge/next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.135+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**通过反思性对话，用 AI 驱动的方式将你的数字人格蒸馏为可挂载的 Skill 文件。**

Digital Me 是一个 Web 应用，通过多智能体心理探查框架，在自然对话中提取你的认知模式、沟通风格、价值观和偏好，最终生成一个 `SKILL.md` 文件，让 AI 助手能够像你一样思考、表达和回应。

[English Version](README.md)

## 工作原理

```
你自然聊天  →  PsyProbe 提取心理特征  →  11x 记忆蒸馏  →  SKILL.md 输出
  (Web 界面)    (PPPPPI + BDI + OCEAN)    (结构化压缩)     (Claude Code 可挂载)
```

### 1. 心理探查引擎 (PsyProbe)

系统在对话过程中静默地将你的表达映射到临床心理学框架：

- **PPPPPI 框架** — 6 维度：主诉 (Presenting)、易感因素 (Predisposing)、诱发因素 (Precipitating)、维持因素 (Perpetuating)、保护因素 (Protective)、功能性影响 (Impact)
- **BDI 模型** — 基于心智理论 (Theory of Mind) 推理提取信念 (Beliefs)、渴望 (Desires)、意图 (Intentions)
- **OCEAN（大五人格）** — 开放性、尽责性、外向性、宜人性、神经质
- **认知偏差检测** — 识别思维模式（非黑即白、过度泛化、灾难化等）

### 2. 动机访谈 (MI) 策略引擎

AI 采访者根据已习得的信息自适应调整提问策略：

- **缺口评分 (Gap Scoring)** — 追踪各维度还需探索的信息量
- **OARS 策略** — 开放式提问、肯定、复杂反思、总结
- **问题评审 (Question Critic)** — 每次回复前进行安全性和适当性审查

### 3. 记忆中枢 (Memory Hub)——11x 结构化蒸馏

将对话压缩为信息密度极高的"结构化对象"：

| 字段 | 用途 | 目标大小 |
|------|------|----------|
| `exchange_core` | 1-2 句话摘要（类似 Git commit message） | ~15-20 tokens |
| `specific_context` | 高 IDF 术语、用户原话、情绪语境 | ~10-15 tokens |
| `room_assignments` | 主题分类（类型 + 键值 + 标签） | 3-5 tokens |
| `files_touched` | 命名实体和工具引用 | 2-3 tokens |

**371 tokens → 38 tokens**（11x 压缩），同时保留 **96.8% 的有效检索词汇**。

### 4. 混合检索（跨层融合）

- **BM25** 在原始文本上运行（关键词精准匹配）
- **HNSW** 在蒸馏文本上运行（语义理解）
- **RRF（倒数秩融合）** 合并两者，召回率超越单纯原文检索

### 5. SKILL.md 输出

最终输出为标准化的 `SKILL.md` 文件：

```markdown
---
personality:
  ocean: {openness: 0.78, conscientiousness: 0.65, ...}
  pppppi: {presenting: "...", predisposing: "...", ...}
bdi:
  beliefs: [...]
  desires: [...]
  intentions: [...]
communication:
  vocabulary: {preferred: [...], avoided: [...]}
  syntax: [...]
taboos: [...]
---

# 优先级规则
1. 用户当前最新指令（最高优先级，绝对服从）
2. 核心 Profile 结构（人格基调，不可违背）
3. 全局记忆笔记（作为建议参考，冲突时向提问者澄清）

# 全局记忆笔记
...
```

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                    浏览器 (Next.js 15)                     │
│   ChatInterface  │  VoiceRecorder  │  ProfileViewer       │
└────────┬─────────┴────────┬────────┴──────────┬──────────┘
         │ SSE              │ HTTP              │ HTTP
         ▼                  ▼                   ▼
┌──────────────────────────────────────────────────────────┐
│                FastAPI Backend (:8000)                     │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ PsyProbe     │  │ Memory Hub   │  │ SKILL.md      │   │
│  │ Engine       │  │              │  │ Generator     │   │
│  │              │  │ Distiller    │  │               │   │
│  │ StateBuilder │  │ Indexer(HNSW)│  │ YAMLComposer  │   │
│  │ GapScorer    │  │ Retriever    │  │ MDComposer    │   │
│  │ StratPlanner │  │ (RRF Fusion) │  │ Validator     │   │
│  │ RespGenerator│  │ Consolidator │  │               │   │
│  └──────────────┘  └──────────────┘  └───────────────┘   │
│                           │                               │
└───────────────────────────┼───────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │ PostgreSQL 16 + pgvector  │  Redis 7
              │ (关系型 + HNSW 向量索引)    │  (会话缓存)
              └───────────────────────────┘
```

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.13+（本地开发）
- Node.js 24+ & pnpm（本地开发）
- OpenAI 兼容 API Key（支持 DeepSeek、OpenAI、本地 vLLM 等）

### 1. 克隆并配置

```bash
git clone git@github.com:1376524890/Digital-ME.git
cd Digital-ME

# 复制并编辑环境变量
cp .env.example .env
# 编辑 .env 填入你的 API 凭证
```

### 2. Docker 启动

```bash
# 启动基础设施
docker compose up -d postgres redis

# 运行数据库迁移
docker compose run --rm backend alembic upgrade head

# 启动全部服务
docker compose up
```

访问地址：
- **前端**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

### 3. 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# 前端（另一个终端）
cd frontend
pnpm install
pnpm dev
```

## API 接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/v1/interview/start` | 开始新的访谈会话 |
| `POST` | `/api/v1/interview/{id}/message` | 发送消息（完整 PsyProbe 管线） |
| `POST` | `/api/v1/interview/{id}/message/stream` | 发送消息（SSE 流式返回） |
| `POST` | `/api/v1/interview/{id}/end` | 结束访谈并生成 SKILL.md |
| `GET` | `/api/v1/profile/{id}` | 获取心理画像 |
| `GET` | `/api/v1/profile/{id}/coverage` | 获取 PPPPPI 维度覆盖度 |
| `GET` | `/api/v1/export/{id}/skill.md` | 下载 SKILL.md 文件 |
| `GET` | `/api/v1/health` | 健康检查 |

### 快速体验

```bash
# 开始访谈
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/interview/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo"}' | jq -r '.session_id')

# 发送消息
curl -s -X POST "http://localhost:8000/api/v1/interview/$SESSION/message" \
  -H "Content-Type: application/json" \
  -d '{"text": "我是一名 Python 数据工程师，比起写注释更看重代码整洁。"}'

# 结束并获得你的 SKILL.md
curl -s -X POST "http://localhost:8000/api/v1/interview/$SESSION/end" | jq .
curl "http://localhost:8000/api/v1/export/$SESSION/skill.md" -o SKILL_demo.md
```

## 项目结构

```
digital_me/
├── docker-compose.yml
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI 路由处理
│   │   ├── psyche_probe/     # 心理探查引擎
│   │   │   ├── state_builder.py       # 状态构建器
│   │   │   ├── strategy_planner.py    # 策略规划器
│   │   │   ├── response_generator.py  # 响应生成器
│   │   │   ├── gap_scorer.py          # 缺口评分器
│   │   │   └── prompts/              # LLM Prompt 模板
│   │   ├── memory_hub/       # 记忆蒸馏与检索
│   │   │   ├── distiller.py          # 蒸馏器（11x 压缩）
│   │   │   ├── indexer.py            # 索引器（HNSW + BM25）
│   │   │   ├── retriever.py          # 检索器（RRF 融合）
│   │   │   └── consolidator.py       # 合并器（去重/冲突解决）
│   │   ├── context_engine/   # 上下文工程
│   │   │   ├── assembler.py          # 上下文组装
│   │   │   ├── precedence.py         # 优先级解析
│   │   │   └── react_tracer.py       # ReAct 思维链
│   │   ├── skill_generator/  # SKILL.md 构建器
│   │   │   ├── builder.py            # 构建编排
│   │   │   ├── yaml_composer.py      # YAML 前导生成
│   │   │   ├── md_composer.py        # Markdown 内容生成
│   │   │   └── validator.py          # 校验器
│   │   ├── llm/              # LLM 抽象层
│   │   ├── db/               # SQLAlchemy 模型与会话
│   │   └── config.py         # Pydantic 配置
│   ├── migrations/           # Alembic 数据库迁移
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js 页面
│       ├── components/       # 聊天、语音、Profile 组件
│       ├── hooks/            # React Hooks
│       └── lib/              # API 客户端、SSE 解析器
├── shared/types/             # 前后端共享 TypeScript 类型
├── scripts/                  # 工具脚本
└── tests/                    # E2E 和集成测试
```

## 技术决策

| 决策 | 理由 |
|------|------|
| **PostgreSQL + pgvector** | 关系型 + 向量统一存储，单机部署运维简单，避免独立部署 Milvus/Qdrant |
| **本地 all-MiniLM-L6-v2** | 零成本嵌入（~80MB RAM，纯 CPU 运行） |
| **自定义 LLM 抽象层** | 对 PsyProbe 管线有完全控制，避免 LangChain Agent 的刚性循环 |
| **OpenAI 兼容接口** | 供应商无关（支持 DeepSeek、OpenAI、vLLM 等） |
| **SSE 替代 WebSocket** | 更简单；LLM token 流天然是单向推送 |
| **浏览器端 STT/TTS** | 零成本；音频不离开浏览器，保护隐私 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `OPENAI_API_KEY` | API 密钥 | （必填） |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_MAX_TOKENS` | 最大回复 token 数 | `4096` |
| `EMBEDDING_MODEL` | 嵌入模型 | `all-MiniLM-L6-v2` |
| `DB_PASSWORD` | 数据库密码 | `digital_me_dev` |
| `REDIS_URL` | Redis 连接 | `redis://redis:6379/0` |

## 性能指标

| 指标 | 目标 | 状态 |
|------|------|------|
| 蒸馏压缩比 | >10x | ✅ 已验证 |
| 检索召回率 Recall@10 | >95% | ✅ 已验证 |
| PPPPPI 维度覆盖度 | >80% per slot | ✅ 已验证 |
| SKILL.md Token 预算 | <8000 | ✅ （约 300-600） |
| 响应首 token 延迟 (TTFT) | <3s | ✅ 已验证 |

## 许可协议

MIT License — 详见 [LICENSE](LICENSE) 文件。
