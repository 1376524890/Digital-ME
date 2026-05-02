# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Full stack (Docker)
make dev                    # Start postgres + redis + backend + frontend
make dev-db                 # Start infrastructure only
docker compose run --rm backend alembic upgrade head  # Run migrations
docker compose run --rm backend pytest                  # Run tests

# Frontend (local dev)
cd frontend && pnpm install && pnpm dev     # Next.js dev server on :3000
cd frontend && pnpm build                   # Production build

# Backend (local dev)
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000   # FastAPI on :8000
```

## Architecture

This is a **digital twin distillation** app — users chat with an AI interviewer that silently profiles their personality (PPPPPI clinical framework, BDI model, OCEAN traits) and compresses conversations 11x into a mountable `SKILL.md` file.

### Stack

- **Frontend**: Next.js 15 (App Router, React 19), Tailwind CSS v4, TypeScript — black/white minimalist design
- **Backend**: FastAPI (Python), SQLAlchemy 2.0 async, PostgreSQL 16 + pgvector (HNSW), Redis 7
- **LLM**: OpenAI-compatible API (default DeepSeek) via custom adapter with instructor for structured extraction
- **Embeddings**: local `all-MiniLM-L6-v2` via sentence-transformers (hash-based fallback if unavailable)
- **Browser STT/TTS**: Web Speech API (zh-CN), zero-cost, audio stays local

### Route Map (Next.js App Router)

| Path | File | Purpose |
|---|---|---|
| `/` | `frontend/src/app/page.tsx` | Home page with matrix-rain canvas animation |
| `/interview/[id]` | `frontend/src/app/interview/[id]/page.tsx` | Chat session (`id="new"` creates session then redirects) |
| `/profile/[id]` | `frontend/src/app/profile/[id]/page.tsx` | Psychological profile + SKILL.md viewer |

### API Endpoints (all under `/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/interview/start` | Create session, return `session_id` + greeting |
| `POST` | `/interview/{id}/message` | Full PsyProbe pipeline (non-streaming) |
| `POST` | `/interview/{id}/message/stream` | SSE token streaming + final `done` event |
| `POST` | `/interview/{id}/end` | End session, trigger SKILL.md generation |
| `GET` | `/profile/{id}` | Get ProfileSnapshot JSON |
| `GET` | `/profile/{id}/coverage` | Get PPPPPI dimension coverage percentages |
| `GET` | `/export/{id}/skill.md` | Download raw SKILL.md |

### Interview Pipeline (per-message flow)

The handler in `backend/src/api/interview.py` orchestrates these phases sequentially:

1. **State Building** (`psyche_probe/state_builder.py`) — Extract cognitive errors (regex → LLM confirm), PPPPPI dimension mapping, and BDI model updates from user text. Parallel LLM calls merge new evidence into existing profile.
2. **Gap Scoring** (`psyche_probe/gap_scorer.py`) — Pure math: compute coverage gaps across 6 PPPPPI dimensions, select highest-gap dimension as target.
3. **Strategy Planning** (`psyche_probe/strategy_planner.py`) — LLM selects a Motivational Interviewing strategy (OARS-based: open question, affirm, reflect, evoke, summarize) and generates candidate questions from templates.
4. **Response Generation** (`psyche_probe/response_generator.py`) — LLM generates final Chinese-language interviewer response (temperature 0.8, max 300 tokens) informed by profile summary + strategy.
5. **Background Distillation** — `asyncio.create_task` fires off `memory_hub/distiller.py` to compress the exchange ~10x into a `StructuredObject`, then `indexer.py` generates the pgvector embedding.

### Memory Hub (post-message, async)

- **Distiller**: Compresses `(user_text, ai_response)` into `exchange_core` (~20 tokens), `specific_context` (~15 tokens), `room_assignments` (JSONB categories), `files_touched` (named entities)
- **Indexer**: Lazy-loads sentence-transformers, generates 384-dim embeddings stored in pgvector
- **Retriever**: RRF fusion of BM25 (keyword) + HNSW (semantic) — **not called in real-time path**, only used post-session during SKILL.md generation
- **Consolidator**: Post-session dedup (cosine >0.92), conflict resolution, confidence pruning (<0.3)

### Database (`backend/src/db/models.py`)

- `Session` — `user_id`, `status` (active/completed), timestamps
- `Ply` — `session_id` FK, `sequence_num`, `user_text`, `ai_response`
- `StructuredObject` — 1:1 with Ply, includes `embedding` (Vector 384), `confidence`, all four distillation fields
- `ProfileSnapshot` — 1:1 with Session, all JSONB columns (pppppi_slots, bdi_model, ocean_scores, cognitive_errors, vocabulary_profile, syntax_preferences, key_taboos)
- `SkillFile` — 1:1 with Session, `yaml_frontmatter`, `global_notes`, `full_content`

### Key Patterns

- **Singleton factories**: Every engine module uses `_instance` + `get_xxx()` pattern, initialized on first call
- **Fire-and-forget background tasks**: `asyncio.create_task(_distill_and_index(...))` — opens its own DB session, failures are caught and logged
- **Graceful degradation**: Embedding model falls back to deterministic hash-based pseudo-embedding; cognitive error extraction falls back to regex-only on LLM failure; structured output falls back from instructor to raw JSON parsing with regex recovery
- **Frontend SSE**: `streamChat` is an async generator that POSTs to the stream endpoint, reads the fetch `ReadableStream`, parses SSE `data:` lines into `{type, content?, ply_id?}` events
- **Browser-side voice**: Web Speech API for both STT and TTS, zh-CN locale, no audio data leaves the browser

### Design Constraints

- **All conversation is in Simplified Chinese** — system prompts, strategy guidance, LLM training examples, and expected outputs
- **No authentication** — user identity is a simple `user_id` string (UUID from `localStorage`)
- **No real-time retrieval** — the Context Engine exists but is not wired into the streaming path; context is built from last 10 Plys + ProfileSnapshot only
- **Project uses `/home/marktom/digital_me/frontend/.env` for frontend env vars** (NEXT_PUBLIC_API_URL) and `.env` at repo root for backend/LLM config
