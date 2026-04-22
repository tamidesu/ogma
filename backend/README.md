# ProfSim Backend

AI-driven Interactive Profession Simulation Platform. Users make decisions inside realistic professional scenarios; a Groq LLM provides structured mentoring feedback on each choice.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 + uvicorn |
| Database | PostgreSQL 16 (SQLAlchemy 2.0 async + asyncpg) |
| Cache / Sessions | Redis 7 (hiredis) |
| Migrations | Alembic (async) |
| AI Provider | Groq (`llama-3.3-70b-versatile`) |
| RAG | BM25 (`rank-bm25`) — in-process, no embedding API |
| Auth | JWT HS256 — access + refresh token rotation |
| Validation | Pydantic v2 |
| Logging | structlog (JSON in production) |
| Retries | tenacity |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, middleware
│   ├── config.py                # Pydantic settings (reads .env)
│   ├── dependencies.py          # FastAPI DI aliases (DBSession, CurrentUser)
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py          # register, login, refresh, logout, me
│   │   │   ├── sessions.py      # CRUD + decisions + feedback SSE stream
│   │   │   ├── professions.py   # list professions + scenarios
│   │   │   └── progress.py      # skill profiles + XP
│   │   └── schemas/             # Pydantic request/response models
│   │
│   ├── ai/
│   │   ├── prompt_builder.py    # Profession personas + prompt assembly
│   │   ├── context_assembler.py # Builds PromptContext from DB + outcome + RAG
│   │   ├── feedback_generator.py# Orchestrates AI call + DB persistence
│   │   ├── groq_adapter.py      # Groq API, JSON mode, streaming, retries
│   │   ├── provider_adapter.py  # AIProvider ABC + StructuredFeedback dataclass
│   │   └── rag/
│   │       ├── bm25_retriever.py# BM25Okapi per-profession index
│   │       ├── retriever.py     # Abstract Retriever interface
│   │       └── knowledge/       # .txt knowledge bases (one per profession)
│   │           ├── software_engineer.txt
│   │           ├── doctor.txt
│   │           ├── lawyer.txt
│   │           └── business_manager.txt
│   │
│   ├── simulation/
│   │   ├── engine.py            # SimulationEngine (top-level facade)
│   │   ├── executor.py          # StepExecutor — validates + applies effects
│   │   ├── rule_evaluator.py    # Condition checks + effect application
│   │   ├── state_machine.py     # Next-step resolution (transitions + fallback)
│   │   ├── metrics.py           # Profession scoring weights + XP levels
│   │   ├── loader.py            # DB → domain model loading
│   │   └── models/              # Pure Python frozen dataclasses
│   │       ├── scenario.py      # Scenario, Step, DecisionOption, Effect
│   │       ├── session_state.py # MetricSnapshot, SimSessionState
│   │       └── outcome.py       # StepOutcome, SkillXPGain
│   │
│   ├── db/
│   │   ├── base.py              # Base, TimestampMixin, UUIDPrimaryKey
│   │   ├── session.py           # async_session_factory, init_db
│   │   ├── redis.py             # Redis singleton, init/close helpers
│   │   ├── models/              # SQLAlchemy ORM models
│   │   └── repositories/        # Async DB access layer
│   │
│   ├── services/
│   │   ├── auth_service.py      # register, login, refresh, logout
│   │   ├── session_service.py   # Redis-backed session cache (write-through)
│   │   ├── decision_service.py  # Decision pipeline orchestrator
│   │   └── progress_service.py  # XP, leveling, completion records
│   │
│   ├── core/
│   │   ├── security.py          # JWT + bcrypt helpers
│   │   └── exceptions.py        # Domain exception hierarchy + HTTP mapping
│   │
│   └── middleware/
│       └── rate_limit.py        # Redis sliding-window rate limiter
│
├── alembic/
│   └── versions/
│       ├── 0001_initial_schema.py
│       └── 0002_ai_feedback_structured_fields.py
│
├── scripts/
│   └── seed_scenarios.py        # Idempotent scenario seeder
│
├── tests/
│   ├── unit/
│   │   ├── simulation/          # rule_evaluator, executor, metrics
│   │   └── ai/                  # prompt_builder, groq_adapter, bm25_retriever
│   └── integration/
│
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker + Docker Compose
- A Groq API key — [console.groq.com](https://console.groq.com)

### 2. Environment

Copy and fill in the required values:

```bash
cp .env.example .env
```

Required variables:

```env
APP_SECRET_KEY=your-random-secret-key-32-chars-min
DATABASE_URL=postgresql+asyncpg://profsim:profsim@localhost:5432/profsim
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=gsk_...
```

### 3. Start infrastructure

```bash
docker-compose up postgres redis -d
```

### 4. Install dependencies

```bash
pip install -e ".[dev]"
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Seed scenarios

```bash
python scripts/seed_scenarios.py --publish
```

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

API docs available at **http://localhost:8000/docs**

### Docker (full stack)

```bash
docker-compose up --build
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `APP_SECRET_KEY` | — | JWT signing secret (required) |
| `APP_CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array of allowed origins |
| `DATABASE_URL` | — | PostgreSQL asyncpg URL (required) |
| `DATABASE_POOL_SIZE` | `10` | SQLAlchemy connection pool size |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_SESSION_TTL` | `1800` | Session cache TTL in seconds |
| `GROQ_API_KEY` | — | Groq API key (required) |
| `GROQ_DEFAULT_MODEL` | `llama-3.3-70b-versatile` | Primary LLM model |
| `GROQ_FALLBACK_MODEL` | `llama-3.1-8b-instant` | Fallback on primary failure |
| `GROQ_TEMPERATURE` | `0.7` | LLM sampling temperature |
| `RAG_ENABLED` | `true` | Enable BM25 RAG context injection |
| `AI_FEEDBACK_ASYNC` | `true` | Run AI feedback in background task |
| `AI_STRUCTURED_OUTPUT` | `true` | Use Groq JSON mode for rich feedback |
| `AI_FEEDBACK_HISTORY_DEPTH` | `5` | Past decisions passed to AI prompt |
| `RATE_LIMIT_PER_MINUTE` | `100` | Requests per minute per IP |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

---

## API Overview

All responses are wrapped in `{"data": ..., "meta": {...}, "errors": null}`.

### Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token |
| `POST` | `/api/v1/auth/logout` | Invalidate refresh token |
| `GET` | `/api/v1/auth/me` | Current user profile |

### Professions & Scenarios

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/professions` | List all professions |
| `GET` | `/api/v1/professions/{slug}/scenarios` | List scenarios for a profession |

### Simulation Sessions

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/sessions` | Start a new session |
| `GET` | `/api/v1/sessions/{id}` | Get session state + current step |
| `POST` | `/api/v1/sessions/{id}/decisions` | Make a decision (returns immediately) |
| `POST` | `/api/v1/sessions/{id}/pause` | Pause session |
| `DELETE` | `/api/v1/sessions/{id}` | Abandon session |
| `GET` | `/api/v1/sessions/{id}/history` | Full decision history |
| `GET` | `/api/v1/sessions/{id}/decisions/{did}/feedback` | Poll for AI feedback |
| `GET` | `/api/v1/sessions/{id}/decisions/{did}/feedback/stream` | SSE stream for AI feedback |

### Progress

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/progress` | XP, level, skill scores |

---

## AI Feedback System

When a decision is made the response is returned **immediately** — AI feedback runs as a background task. The frontend can retrieve feedback via:

- **Polling**: `GET /sessions/{id}/decisions/{did}/feedback` — returns `{"ready": true, "feedback": {...}}` when done
- **SSE stream**: `GET /sessions/{id}/decisions/{did}/feedback/stream` — server pushes `{"event": "pending"}` each second then `{"event": "ready", "feedback": {...}}`

### Structured Feedback Fields

Each AI response contains:

| Field | Description |
|---|---|
| `text` | 3–5 sentence mentoring narrative on the decision |
| `key_insight` | Single-sentence core lesson |
| `coaching_question` | A reflective question for the user |
| `consequence_analysis` | Where this pattern leads if continued |
| `alternative_path` | What the road not taken would have meant |
| `tone` | `encouraging` / `critical` / `analytical` / `neutral` |

### RAG Context

Each feedback prompt is enriched with up to 3 relevant paragraphs retrieved from a per-profession BM25 knowledge base (`app/ai/rag/knowledge/*.txt`). No external embedding API is required — indices are built in-process at startup from plain text files.

### Profession Personas

Each profession has a named expert persona embedded in the system prompt:

- **Software Engineer** → Alex Rivera, staff engineer (18 years, distributed systems)
- **Doctor** → Dr. Amara Osei, consultant physician (22 years, emergency + clinical ethics)
- **Lawyer** → Margaret Chen, senior litigation partner (30 years)
- **Business Manager** → David Kowalski, former COO + executive coach

---

## Simulation Engine

The simulation engine is **fully deterministic** — zero AI calls, pure Python frozen dataclasses. Decisions are processed synchronously in under 10 ms.

### Supported Effect Types

| Type | Description |
|---|---|
| `metric_delta` | Add/subtract from a metric (clamped 0–100) |
| `metric_set` | Set a metric to an absolute value |
| `state_set` | Set a boolean state flag |
| `state_toggle` | Flip a boolean state flag |
| `skill_xp` | Award XP for a skill |
| `unlock_step` | Unlock a step that was conditionally hidden |

### Supported Condition Types

`metric_gte`, `metric_lte`, `state_is_true`, `state_equals`, `not`, `and`, `or`

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# AI layer only
pytest tests/unit/ai/

# Simulation layer only
pytest tests/unit/simulation/
```

---

## Adding a New Profession

1. Create `app/ai/rag/knowledge/{profession_slug}.txt` — one paragraph per entry, blank line separated, `TOPIC HEADER:` prefix on each
2. Add a persona in `app/ai/prompt_builder.py` → `_PERSONAS` dict
3. Add profession metric labels to `_METRIC_LABELS`
4. Add scoring weights to `app/simulation/metrics.py` → `_PROFESSION_WEIGHTS`
5. Create scenario JSON files in `tests/fixtures/scenarios/` and run `python scripts/seed_scenarios.py --publish`

---

## Code Quality

```bash
# Lint + format check
ruff check app tests
ruff format --check app tests

# Type check
mypy app
```
