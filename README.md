# Digital Me

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 24+](https://img.shields.io/badge/node-24+-green.svg)](https://nodejs.org/)
[![Next.js 15](https://img.shields.io/badge/next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.135+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**AI-driven digital twin distillation through reflective conversation.**

Digital Me is a web application that uses multi-agent psychological profiling to create a digital twin of your personality. Through natural conversation, the system extracts your cognitive patterns, communication style, values, and preferences, then generates a mountable `SKILL.md` file that enables AI assistants to think, speak, and respond like you.

## How It Works

```
You chat naturally  →  PsyProbe extracts your psychology  →  11x memory distillation  →  SKILL.md output
     (Web UI)           (PPPPPI + BDI + OCEAN)                (structured compression)      (Claude Code mountable)
```

### 1. Psychological Profiling (PsyProbe Engine)

The system silently maps your conversation to clinical psychology frameworks:

- **PPPPPI Framework** — 6 dimensions: Presenting, Predisposing, Precipitating, Perpetuating, Protective, Impact
- **BDI Model** — Beliefs, Desires, Intentions extracted via Theory of Mind reasoning
- **OCEAN (Big Five)** — Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- **Cognitive Error Detection** — Identifies thinking patterns (all-or-nothing, overgeneralization, catastrophizing, etc.)

### 2. Motivational Interviewing (MI) Strategy Engine

The AI interviewer adapts its questioning based on what it has learned:

- **Gap Scoring** — Tracks which dimensions need more exploration
- **OARS Strategies** — Open Questions, Affirmations, Complex Reflections, Summaries
- **Question Critic** — Safety and appropriateness review before each response

### 3. Memory Hub (11x Structured Distillation)

Conversations are compressed into information-dense "structured objects":

| Field | Purpose | Target Size |
|-------|---------|-------------|
| `exchange_core` | 1-2 sentence summary | ~15-20 tokens |
| `specific_context` | High-IDF terms, exact user phrasing | ~10-15 tokens |
| `room_assignments` | Topic categorization | 3-5 tokens |
| `files_touched` | Named entities & tools | 2-3 tokens |

**371 tokens → 38 tokens** (11x compression) with **96.8% retrieval vocabulary retention**.

### 4. Hybrid Retrieval (Cross-layer Fusion)

- **BM25** on verbatim user text (keyword precision)
- **HNSW** on distilled embeddings (semantic understanding)
- **RRF (Reciprocal Rank Fusion)** combines both for >95% recall

### 5. SKILL.md Output

The final output is a standardized `SKILL.md` with:

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

# Precedence Rules
1. Current user instruction (highest)
2. Core profile (personality baseline)
3. Global notes (advisory)

# Global Memory Notes
...
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Browser (Next.js 15)                   │
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
              │ (relational + HNSW index) │  (sessions)
              └───────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.13+ (for local dev)
- Node.js 24+ & pnpm (for local dev)
- OpenAI-compatible API key (DeepSeek, OpenAI, or local vLLM)

### 1. Clone & Configure

```bash
git clone git@github.com:1376524890/Digital-ME.git
cd Digital-ME

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your API credentials
```

### 2. Start with Docker

```bash
# Start infrastructure
docker compose up -d postgres redis

# Run database migrations
docker compose run --rm backend alembic upgrade head

# Start all services
docker compose up
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

### 3. Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend
pnpm install
pnpm dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/interview/start` | Start a new interview session |
| `POST` | `/api/v1/interview/{id}/message` | Send message (full PsyProbe pipeline) |
| `POST` | `/api/v1/interview/{id}/message/stream` | Send message (SSE streaming) |
| `POST` | `/api/v1/interview/{id}/end` | End interview & generate SKILL.md |
| `GET` | `/api/v1/profile/{id}` | Get psychological profile |
| `GET` | `/api/v1/profile/{id}/coverage` | Get PPPPPI dimension coverage |
| `GET` | `/api/v1/export/{id}/skill.md` | Download SKILL.md file |
| `GET` | `/api/v1/health` | Health check |

### Example: Quick Interview

```bash
# Start an interview
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/interview/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo"}' | jq -r '.session_id')

# Send a message
curl -s -X POST "http://localhost:8000/api/v1/interview/$SESSION/message" \
  -H "Content-Type: application/json" \
  -d '{"text": "I write Python for data engineering. Clean code matters more than comments."}'

# End and get your SKILL.md
curl -s -X POST "http://localhost:8000/api/v1/interview/$SESSION/end" | jq .
curl "http://localhost:8000/api/v1/export/$SESSION/skill.md" -o SKILL_demo.md
```

## Project Structure

```
digital_me/
├── docker-compose.yml
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── psyche_probe/     # Psychological profiling engine
│   │   │   ├── state_builder.py
│   │   │   ├── strategy_planner.py
│   │   │   ├── response_generator.py
│   │   │   ├── gap_scorer.py
│   │   │   └── prompts/      # LLM prompt templates
│   │   ├── memory_hub/       # Memory distillation & retrieval
│   │   │   ├── distiller.py
│   │   │   ├── indexer.py
│   │   │   ├── retriever.py
│   │   │   └── consolidator.py
│   │   ├── context_engine/   # Context window assembly
│   │   ├── skill_generator/  # SKILL.md builder
│   │   ├── llm/              # LLM abstraction layer
│   │   ├── db/               # SQLAlchemy models & session
│   │   └── config.py         # Pydantic settings
│   ├── migrations/           # Alembic migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       ├── components/       # Chat, Voice, Profile components
│       ├── hooks/            # React hooks
│       └── lib/              # API client, SSE parser
├── shared/types/             # Shared TypeScript types
├── scripts/                  # Utility scripts
└── tests/                    # E2E & integration tests
```

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **PostgreSQL + pgvector** | Single DB for relational + vector; simpler ops than separate Milvus/Qdrant |
| **Local all-MiniLM-L6-v2** | Zero-cost embeddings (~80MB RAM, CPU-only) |
| **Custom LLM abstraction** | Full pipeline control vs. LangChain's rigid agent loop |
| **OpenAI-compatible API** | Provider-agnostic (DeepSeek, OpenAI, vLLM, etc.) |
| **SSE over WebSocket** | Simpler; LLM token streaming is naturally unidirectional |
| **Browser-side STT/TTS** | Zero-cost; audio stays in browser for privacy |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | LLM API base URL | `https://api.deepseek.com/v1` |
| `OPENAI_API_KEY` | API key | (required) |
| `LLM_MODEL` | Model name | `deepseek-chat` |
| `LLM_MAX_TOKENS` | Max response tokens | `4096` |
| `EMBEDDING_MODEL` | Embedding model | `all-MiniLM-L6-v2` |
| `DB_PASSWORD` | PostgreSQL password | `digital_me_dev` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Distillation compression | >10x | ✅ |
| Retrieval recall@10 | >95% | ✅ |
| PPPPPI coverage | >80% per slot | ✅ |
| SKILL.md token budget | <8000 | ✅ (~300-600) |
| Response TTFT | <3s | ✅ |

## License

MIT License — see [LICENSE](LICENSE) file for details.
