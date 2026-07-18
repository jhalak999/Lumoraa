# Lumora — AI Content Automation Studio

Turn a topic into a fully produced short-form video: research → script →
scene plan → image prompts → images → voice → subtitles → rendered video →
thumbnail → SEO metadata. Every stage is a real, independently-triggerable
pipeline step backed by a Celery task, with structured (Pydantic-validated)
output at every hop.

This repo is a working, from-scratch build — not a tutorial skeleton. Every
file has been compiled, dependency-installed, and (on the backend) unit
tested and import-checked in a clean environment; the frontend has been
type-checked and production-built. See **Verification** at the bottom for
exactly what was checked and what you still need to do before going live.

---

## Architecture at a glance

```
backend/
  app/
    core/          # settings, logging, exceptions, JWT/password security — no framework imports
    db/             # SQLAlchemy async engine/session + declarative base
    models/         # ORM: User, Project, Asset, GenerationJob
    schemas/         # Pydantic contracts — including agent OUTPUT schemas (the structured-output contracts)
    services/
      agents/        # One class per agent (Research, Script, ScenePlanner, ImagePrompt, SEO) + orchestrator
      providers/
        llm/         # OpenRouter client wired into Pydantic AI
        image/       # Stability -> Replicate -> OpenAI fallback chain
        tts/         # ElevenLabs -> gTTS fallback chain
      media/         # FFmpeg video assembly, faster-whisper subtitle generation, Pillow thumbnails
      auth_service.py, project_service.py, generation_service.py, storage_service.py
    api/v1/endpoints/  # Thin HTTP layer — routes only call services, never contain business logic
    tasks/           # Celery app + one task per pipeline stage + full-pipeline chain
  alembic/           # Hand-written initial migration (0001) — schema matches the ORM models exactly
  tests/             # pytest unit tests (security, provider fallback) — all passing

frontend/
  src/
    app/             # Router + root layout (AuthProvider lives inside the router tree)
    components/ui/   # shadcn-style primitives (Button, Card, Dialog, Select, Tabs, Progress, ...)
    components/layout/  # AppShell (sidebar nav) + ProtectedRoute
    features/
      auth/          # login/register pages, AuthProvider (JWT + silent refresh)
      dashboard/     # stats cards, recent projects
      projects/      # list/create/detail pages, React Query hooks
      generation/     # Pipeline Rail (signature component), stage triggers, job polling, output panels
    lib/              # axios client w/ auto-refresh, cn(), project-status helpers
    types/api.ts       # TypeScript types mirroring the backend Pydantic schemas
```

**Design principles applied:** each agent is single-responsibility and
extends one base class (open/closed — add a new agent without touching
existing ones); routes never contain business logic (thin controller,
fat service); every external AI/media call goes through a swappable
provider interface with an explicit fallback chain; the frontend is
feature-sliced, not type-sliced, so a stage's API call + hook + component
live together.

---

## Prerequisites

- Python 3.12, Node.js 20+
- PostgreSQL 16, Redis 7 (docker-compose provides both)
- FFmpeg installed and on `PATH` (the Dockerfile installs it automatically)
- API keys — **the app works with zero paid keys** using gTTS for voice
  and will simply fail image generation until at least one image provider
  key is set (see "Provider fallback chains" below).

## Backend setup

```bash
cd backend
cp .env.example .env          # then fill in SECRET_KEY (openssl rand -hex 32) and provider keys
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head            # requires Postgres running — use docker-compose or a local instance
uvicorn app.main:app --reload   # API at http://localhost:8000, docs at /api/docs
```

In a second terminal, start the Celery worker (required for ANY generation
to run — the API only enqueues tasks, it never runs agents inline):

```bash
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
```

Or run the whole backend stack (Postgres + Redis + API + worker) with:

```bash
docker compose up --build
```

If you want automatic nightly cleanup, run the Celery beat scheduler as well:

```bash
docker compose up --build celery_beat
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api and /static to :8000
```

`npm run build` produces a production bundle in `dist/`.

## Free deployment options

For a basic college project demo, the simplest path is to host the backend and worker on a free Docker-based provider such as Railway or Render, then deploy the frontend as a static site on Vercel or Netlify.

Key points:

- The backend needs Postgres and Redis.
- The backend also needs a Celery worker process running alongside the API.
- Generated media is stored locally by default, so hosted deployments are best for demos rather than long-lived production use unless you add S3-compatible storage.
- The frontend now supports `VITE_API_BASE_URL` so it can call a remote backend URL instead of `/api/v1` on the same origin.

### Deploying the backend + worker

1. Choose a provider with Docker support and free Postgres/Redis add-ons. Railway is a good option for a college demo.
2. Add the Postgres and Redis add-ons, then set these env vars from the add-on connection strings:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `CELERY_BROKER_URL`
   - `CELERY_RESULT_BACKEND`
3. Set other required env vars:
   - `SECRET_KEY` (random hex)
   - `ENVIRONMENT=production`
   - `DEBUG=false`
   - `BACKEND_CORS_ORIGINS=https://<your-frontend-domain>`
   - `PUBLIC_ASSET_BASE_URL=https://<your-backend-domain>/static`
   - `STABILITY_API_KEY`, `ELEVENLABS_API_KEY`, and any other provider keys you want to use
   - `IMAGE_PROVIDER_ORDER`, `TTS_PROVIDER_ORDER`, etc.
4. Deploy the backend service from the `backend` directory using the existing `Dockerfile`.
   - API start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Worker start command: `celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2`
5. Run database migrations in the deployed environment: `alembic upgrade head`.

### Deploying the frontend

1. Deploy the `frontend` directory to Vercel or Netlify as a static site.
2. Set `VITE_API_BASE_URL=https://<your-backend-domain>/api/v1` in the frontend environment.
3. Build command: `npm run build`.
4. Publish directory: `dist`.

### Demo mode and storage cleanup

- Enable `DEMO_MODE=true` to make the backend keep video length under `DEMO_MAX_VIDEO_DURATION_SECONDS`, reduce scene count to `DEMO_MAX_SCENES`, use `DEMO_VIDEO_RESOLUTION`, and favor faster/free TTS/image providers.
- The app now supports `DEMO_TTS_PROVIDER_ORDER` and `DEMO_IMAGE_PROVIDER_ORDER` so you can choose a cost-friendly demo fallback chain.
- Local storage cleanup is implemented in `app.services.storage_service.cleanup_old_storage_files()` and can be run automatically by Celery Beat if you also run a `celery beat` process.
- For a truly “on-demand” demo, keep the service deployed but only start the worker/beat when you expect visitors, and rely on the cleanup helper to remove stale generated assets.

### Notes

- If you want the backend and frontend on the same origin, use a reverse proxy or serve the built frontend from the backend container.
- For a stable production deployment later, replace `STORAGE_BACKEND=local` with an S3-compatible backend and make generated assets persistent.

## Provider fallback chains

Both image generation and voice synthesis are configured as **ordered
fallback chains** (`IMAGE_PROVIDER_ORDER`, `TTS_PROVIDER_ORDER` in `.env`).
If the first provider errors, times out, or rejects the request, the next
one is tried automatically — a single vendor outage never takes down the
pipeline.

| Stage | Order (default) | Notes |
|---|---|---|
| Images | `stability` → `replicate` → `openai` | All three need their respective API key; the chain fails loudly only if *every* configured provider fails. |
| Voice | `elevenlabs` → `gtts` | `gtts` needs no API key at all, so voice generation always has a working fallback. |
| LLM (agents) | OpenRouter only | Model per agent is configurable independently (`OPENROUTER_*_MODEL` in `.env`) so you can, e.g., use a cheaper model for SEO than for scriptwriting. |

## Running one stage vs. the full pipeline

Every stage can be triggered independently from the project detail page
(useful for reviewing/regenerating a single step), or you can fire
`POST /projects/{id}/generate/full-pipeline` to run all ten stages back to
back as a single Celery chain. Progress is visible two ways: the coarse
`project.status` (what the Pipeline Rail reads) and granular
`GenerationJob` rows per stage (what the Activity panel reads), polled by
the frontend while anything is in flight.

---

## Verification performed while building this

Because "production-ready" claims are cheap without evidence, here's
exactly what was actually run, in this sandbox, against this code:

- **Backend**: every `.py` file byte-compiled cleanly; a full `pip install`
  of `requirements.txt` succeeded in a clean virtualenv with zero dependency
  conflicts; `from app.main import app` imports successfully and all 19
  routes registered correctly; the orchestrator, image fallback manager, and
  TTS fallback manager all construct without errors even with zero API keys
  configured (real bugs — eager client construction requiring an API key —
  were found and fixed this way); `pytest` passes (6/6) covering password
  hashing, JWT issuance/validation/rejection, and image-provider fallback
  behavior including the "all providers fail" path.
- **Frontend**: `npm install` resolved cleanly; `tsc -b --noEmit` passes
  with zero type errors across the whole app; `npm run build` produces a
  working production bundle.
- **Not verified** (would require real credentials/infra this sandbox
  doesn't have): actual OpenRouter/Stability/Replicate/ElevenLabs API
  calls, a live Postgres migration run, an end-to-end Celery task execution,
  and real FFmpeg video assembly against generated (rather than hand-typed)
  inputs. Treat those integration points as "correctly wired, not yet
  smoke-tested against live services" — budget time for that pass before a
  real launch.

## Known gaps to close before a real launch

- **S3 storage backend** is stubbed (`StorageBackend` interface exists;
  only `LocalStorageBackend` is implemented) — needed before horizontally
  scaling workers.
- **Rate limiting** (`RATE_LIMIT_PER_MINUTE` in settings) is defined but not
  yet enforced by middleware.
- **Email verification** (`User.is_verified`) exists as a field but there's
  no email-sending flow yet.
- **Alembic autogenerate** wasn't run against a live database — the initial
  migration was hand-written to match the models; run
  `alembic revision --autogenerate` once you have a real Postgres instance
  to double-check it as a safety net.
