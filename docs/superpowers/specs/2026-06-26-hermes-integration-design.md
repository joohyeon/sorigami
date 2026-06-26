# Sorigamis — Hermes Pipeline Integration Design
**Date:** 2026-06-26  
**Status:** Approved  
**Scope:** M2 pipeline server — Hermes as the intelligent orchestrator

---

## 1. Overview

The Sorigamis pipeline server (M2) uses **Hermes** as an intelligent orchestrator that understands what users need from their recordings, proposes an execution plan, waits for user confirmation, and executes tasks as coordinated subagents. The Flutter app remains a thin client — the existing `PipelineClient` interface is preserved with no UI changes required.

**Core principles:**
- Hermes is the AI brain: it reads the user's Mode + Skills, generates a plan, and executes it
- Users confirm before execution (upfront plan) and before high-stakes steps (speaker labels, external posts)
- All results sync to local Drift DB for offline access
- Skills and Modes are user-managed: defaults shared across all users, custom ones owned per user

---

## 2. Architecture

```
Flutter App (thin client)
      │
      │  REST  (PipelineClient interface — no Flutter changes)
      ▼
FastAPI wrapper  (Fly.io, CPU-only)
      │  spawns Hermes session per job
      ▼
Hermes Agent  (Fly.io, persistent, gemini-2.5-pro via GitHub Copilot)
  ├── sg-orchestrator skill     ← master skill, understands Modes
  ├── sg-skill-*               ← per-skill extraction (dynamic, from Supabase)
  └── tools: drive, whisper, diarize, supabase, fcm, integrations
      │
      │  reads/writes job state + results
      ▼
Supabase  (shared state, source of truth)
      │
      │  FCM push on status changes
      ▼
Flutter App → syncs to local Drift DB → user views offline
```

**Modal** handles GPU-heavy work (Whisper + pyannote). Fly.io runs FastAPI + Hermes (CPU-only).

**Job status state machine:**
```
submitted → analyzing → awaiting_plan_confirmation
  → executing → awaiting_checkpoint → executing → … → complete | failed
```

---

## 3. Naming Convention

All components use the `sg-` prefix (short for Sorigamis):

- Hermes skills: `sg-orchestrator`, `sg-skill-action-items`, `sg-skill-summary`, etc.
- Tools: `sg-drive-download`, `sg-whisper-transcribe`, `sg-diarize`, `sg-supabase-write`, `sg-notify-fcm`, `sg-slack-post`, `sg-linear-create`, `sg-webhook-call`
- Supabase tables: `sg_jobs`, `sg_utterances`, `sg_speakers`, `sg_skill_results`, `sg_action_logs`, `sg_skills`, `sg_modes`
- Fly.io app: `sg-pipeline`

---

## 4. User-Managed Skills & Modes

### Skill Tiers

**Default Skills** — shared, read-only, maintained centrally, visible to all users:
- `sg-skill-summary`
- `sg-skill-action-items`
- `sg-skill-decisions`
- `sg-skill-sentiment`

**User Skills** — owned per user, full CRUD from mobile:
- Custom name, AI intent prompt, integration actions
- Stored in `sg_skills` under `user_id`

**Modes** — user-owned bundles of Skills in a chosen order:
- e.g. "Sales Call" = [sg-skill-summary, my-crm-notes, sg-skill-action-items]
- One Mode selected per recording session
- Full CRUD from mobile Modes screen

### Supabase Schema

```sql
sg_skills (
  id uuid PK,
  user_id uuid NULL,        -- NULL = default/shared
  name text,
  description text,
  ai_prompt text,           -- injected into Hermes at runtime
  integration_actions jsonb, -- [{type, config}]
  is_default bool,
  created_at timestamptz
)

sg_modes (
  id uuid PK,
  user_id uuid,
  name text,
  skill_ids uuid[],         -- ordered
  created_at timestamptz
)
```

### Dynamic Skill Loading

Hermes does not load static `.md` files per skill. At job start, `sg-orchestrator` fetches the user's Mode from Supabase, reads each Skill's `ai_prompt` and `integration_actions`, and injects them as dynamic context into the session. Default skills are seeded as rows in `sg_skills` on first deploy.

---

## 5. Data Flow (Job Lifecycle)

### Step 1 — Record & Upload
User records → audio saved to Drift (local) → uploaded to Google Drive.  
App POSTs `/jobs` with `{drive_file_id, mode_id, user_id}` to FastAPI.

### Step 2 — Analyze (~30s, Hermes)
- `sg-orchestrator` downloads audio via `sg-drive-download`
- Runs `sg-whisper-transcribe` (Modal, faster-whisper large-v3, `language=ko`, same params as `test_audio_locally.py`)
- Reads user's Mode → fetches Skills from Supabase
- Generates proposed execution plan with steps and destinations

### Step 3 — Plan Confirmation (user, mobile)
Job status → `awaiting_plan_confirmation`. FCM push triggers app to show Plan screen.

**Plan screen interaction:**
- Each proposed step shown as a card with: toggle (include/skip), step name, parameters
- **Edit ▾** — expands card to override parameters for this job only (Slack channel, Linear project, AI prompt tweak). Does not modify the saved Skill.
- **Skip** — exclude a step from this job without changing the Mode
- **+ Add Skill** — add a step from Skills Library for this job only
- **Drag to reorder** — change execution order for this job only

App POSTs `/jobs/{id}/confirm {approved_steps[], per_step_overrides{}}`.  
Per-job overrides do not persist to the saved Mode or Skills.

### Step 4 — Execute: Transcribe + Diarize (Hermes)
- `sg-diarize` runs pyannote (Modal) → speaker-segmented transcript
- Results written to `sg_utterances` + `sg_speakers`

**Checkpoint — Speaker Assignment:**  
Job status → `awaiting_checkpoint`. FCM push → app shows speaker card:  
"Speaker A — 68% of conversation. Assign as Interviewer / Interviewee / [custom name]"  
User confirms → `/jobs/{id}/checkpoint`. `sg_speakers.confirmed_name` updated.  
All downstream Skill prompts use confirmed names ("John said… → assigned to John").

### Step 5 — Skill Extraction (Hermes, parallel)
Each approved Skill runs its `ai_prompt` against `sg_utterances`.  
Results written to `sg_skill_results`. Skills with no dependencies run in parallel.

### Step 6 — Integration Actions
For each integration action, before firing:  
**Checkpoint** — "Post summary to #meetings in Slack — confirm?"  
User approves → `sg-slack-post` / `sg-linear-create` / `sg-webhook-call` fires.  
Result written to `sg_action_logs`.

### Step 7 — Complete
Job status → `complete`. FCM push → app fetches full results → syncs to Drift.  
User views transcript, skill outputs, and action logs offline.

**Failure handling:**
- Any stage fails → `failed` status, error stored, FCM push with retry option
- User can skip a checkpoint step without failing the whole job
- Drive download retried 3× before failing

---

## 6. Storage Schema

### Supabase (cloud, source of truth)

```sql
sg_jobs (
  id uuid PK,
  user_id uuid,
  mode_id uuid,
  drive_file_id text,
  status text,              -- state machine values
  plan_json jsonb,          -- proposed steps
  checkpoint_json jsonb,    -- current checkpoint data
  created_at timestamptz
)

sg_utterances (
  id uuid PK,
  job_id uuid,
  start_sec float,
  end_sec float,
  text text,
  speaker_id uuid,
  confirmed_by_user bool,
  avg_logprob float,
  created_at timestamptz
)

sg_speakers (
  id uuid PK,
  job_id uuid,
  label text,               -- "A", "B", "C"
  confirmed_name text,      -- "Interviewer", "John" — null until confirmed
  talk_time_pct float,
  created_at timestamptz
)

sg_transcript_raw (
  id uuid PK,
  job_id uuid,
  whisper_json jsonb,       -- full Whisper output, for debugging/reprocessing
  diarize_json jsonb        -- full pyannote output
)

sg_skill_results (
  id uuid PK,
  job_id uuid,
  skill_id uuid,
  skill_name text,
  output_json jsonb,        -- structured LLM result
  output_markdown text,     -- human-readable, shown in app
  status text,              -- pending / running / complete / skipped / failed
  created_at timestamptz
)

sg_action_logs (
  id uuid PK,
  job_id uuid,
  skill_id uuid,
  action_type text,         -- slack / linear / webhook
  destination text,
  payload_json jsonb,
  status text,              -- pending / awaiting_confirmation / fired / skipped / failed
  fired_at timestamptz,
  error text
)
```

### Local Drift DB (device, offline-first)

```dart
utterances    — id, jobId, startSec, endSec, text, speakerId, confirmedByUser
speakers      — id, jobId, label, confirmedName, talkTimePct
skillResults  — id, jobId, skillId, skillName, outputMarkdown, status
actionLogs    — id, jobId, skillId, actionType, destination, status, firedAt
```

**Sync:** On `complete`, app fetches all four tables for the job from Supabase and upserts into Drift in a single transaction.

---

## 7. FastAPI Wrapper

### Endpoints

```
POST   /jobs                   — create job, spawn Hermes session
GET    /jobs/{id}              — poll status + current plan/checkpoint
POST   /jobs/{id}/confirm      — approve plan with per-step overrides
POST   /jobs/{id}/checkpoint   — confirm a mid-run checkpoint
GET    /jobs/{id}/results      — fetch full results for Drift sync
GET    /health                 — liveness check

POST   /skills                 — create user skill
GET    /skills                 — list (defaults + user's own)
PUT    /skills/{id}            — update skill
DELETE /skills/{id}            — delete skill

POST   /modes                  — create mode
GET    /modes                  — list user's modes
PUT    /modes/{id}             — update mode
DELETE /modes/{id}             — delete mode
```

### Hermes Session Launch

```bash
hermes -z "<job_context_json>" \
  --provider github-copilot \
  -m gemini-2.5-pro \
  -s sg-orchestrator \
  --yolo \
  --accept-hooks
```

`job_context_json` includes: `drive_file_id`, `job_id`, resolved Mode name, Skills with `ai_prompt` and `integration_actions`, confirmed speaker labels (once set), Supabase credentials scoped to the job.

---

## 8. Hermes Skills & Tools

### Master Skill: `sg-orchestrator`
Loaded for every job. Knows the pipeline stages, reads Mode/Skills from context, decides which steps need user confirmation checkpoints.

**Confirmation checkpoint rules:**
- Always: upfront plan approval
- Always: speaker label assignment
- Always: any external integration action before it fires (Slack, Linear, webhook)
- Never: transcription, LLM extraction (safe, no side effects)

### Per-Skill Extraction (dynamic, loaded from Supabase `ai_prompt`)
- `sg-skill-summary` — meeting summary
- `sg-skill-action-items` — tasks + owners
- `sg-skill-decisions` — decisions made
- `sg-skill-sentiment` — tone per speaker
- User-created skills loaded the same way

### Tools
| Tool | Purpose |
|------|---------|
| `sg-drive-download` | Fetch audio from Google Drive (service account) |
| `sg-whisper-transcribe` | Modal call — faster-whisper large-v3, `language=ko` |
| `sg-diarize` | Modal call — pyannote, `num_speakers=2` default |
| `sg-supabase-write` | Write job state, utterances, results |
| `sg-notify-fcm` | Push notification to Flutter app |
| `sg-slack-post` | Post to Slack channel |
| `sg-linear-create` | Create Linear issue |
| `sg-webhook-call` | Generic webhook POST |

---

## 9. Deployment

### Fly.io (`sg-pipeline`)

```toml
# fly.toml
app = "sg-pipeline"

[services]
  internal_port = 8080   # FastAPI

[env]
  HERMES_MODEL    = "gemini-2.5-pro"
  HERMES_PROVIDER = "github-copilot"

[secrets]
  GOOGLE_SERVICE_ACCOUNT_JSON
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  MODAL_TOKEN_ID
  MODAL_TOKEN_SECRET
  FCM_SERVER_KEY
```

Modal handles all GPU compute (Whisper + pyannote). Fly.io is CPU-only.

### Mobile App Change (M2 swap)
```dart
// main.dart — swap MockPipelineClient for LivePipelineClient
// No other Flutter changes required
final client = LivePipelineClient(baseUrl: settings.pipelineUrl);
```

---

## 10. Mobile Screens Affected

| Screen | Change |
|--------|--------|
| Skills Library | Browse defaults, create/edit/delete own skills |
| Modes | Create/edit/delete modes, reorder skills |
| Skill editor | Name, AI prompt, integration actions config |
| Plan confirmation | Step cards with toggle/edit/skip/add/reorder |
| Speaker checkpoint | Speaker card with name assignment |
| Action checkpoint | Confirm before each external action fires |
| Results | Transcript + per-skill cards + action log (offline from Drift) |

No changes to recording flow, Drive upload, auth, or settings screens.
