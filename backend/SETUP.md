# ProfSim Backend — Setup Guide

## Quick Start (Docker)

```bash
# 1. Copy env file
cp .env.example .env
# Edit .env — set GROQ_API_KEY

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec api alembic upgrade head

# 4. Seed profession data (published)
docker-compose exec api python -m scripts.seed_scenarios --publish

# 5. API is live at http://localhost:8000/docs
```

## Local Development (without Docker)

```bash
# Requirements: Python 3.11+, PostgreSQL 15+, Redis 7+

# 1. Install dependencies
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
# Set DATABASE_URL, REDIS_URL, GROQ_API_KEY

# 3. Run migrations
alembic upgrade head

# 4. Seed data
python -m scripts.seed_scenarios --publish

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

## Running Tests

```bash
# Unit tests only (no DB required)
pytest tests/unit/ -v

# All tests
pytest -v --cov=app --cov-report=term-missing
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Login → access + refresh token |
| POST | /api/v1/auth/refresh | Rotate refresh token |
| GET | /api/v1/professions | List all professions |
| GET | /api/v1/professions/{id}/scenarios | Scenarios for a profession |
| POST | /api/v1/sessions | Start a simulation session |
| GET | /api/v1/sessions/{id} | Get session state + current step |
| POST | /api/v1/sessions/{id}/decisions | Make a decision |
| POST | /api/v1/sessions/{id}/pause | Pause session |
| DELETE | /api/v1/sessions/{id} | Abandon session |
| GET | /api/v1/sessions/{id}/history | Decision history |
| GET | /api/v1/sessions/{id}/decisions/{did}/feedback | Poll for AI feedback |
| GET | /api/v1/users/me/progress | XP, level, skills |
| GET | /api/v1/users/me/sessions | Session history |

## Core Professions Seeded

- **Software Engineer** — 3 scenarios: incident response, architecture decisions, code review
- **Doctor** — 3 scenarios: mass casualty triage, diagnostic dilemma, patient autonomy
- **Lawyer** — 2 scenarios: ethics vs client, settlement negotiation
- **Business Manager** — 2 scenarios: budget crisis, product launch failure

## Architecture Notes

- **Simulation Engine** is 100% deterministic — zero AI calls
- **AI feedback** runs as `BackgroundTask`, non-blocking
- Poll `GET /sessions/{id}/decisions/{did}/feedback` every 2–3s for the feedback
- Session state is cached in Redis (TTL 30min), source of truth is PostgreSQL
- New profession = JSON file in `tests/fixtures/scenarios/` + re-run seed script
