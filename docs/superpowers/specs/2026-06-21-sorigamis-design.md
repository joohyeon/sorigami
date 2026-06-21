# Sorigamis — Mobile App Design Spec
**Date:** 2026-06-21  
**Status:** Approved

---

## 1. Overview

Sorigamis is a cross-platform mobile app (Android + iOS) that records conversations and routes them through an AI pipeline to produce speaker-attributed transcripts, summaries, and action items. The core interaction model is **Modes** — named recording contexts (e.g. "Team Meeting", "Sales Call") that bundle AI Skills and apply them automatically. Users pick a Mode once, hit Record, and get back structured results without configuring anything per recording.

The app is a thin client: it records, stores metadata, backs up audio to the user's cloud (Google Drive), and triggers the AI pipeline. All AI computation happens in the pipeline, not on the device.

### Background

A working local pipeline already exists at `scripts/test_audio_diarize.py` in the SoriNote repo. It performs **Stage 1** processing: ffmpeg transcode → faster-whisper ASR (word timestamps) → pyannote speaker diarization → ECAPA-TDNN centroid re-assignment, producing a speaker-attributed transcript. It is multilingual (Korean + English) and CPU/MPS-capable. The **Stage 2** multi-agent step (summary / task / decision extraction) is new pipeline work.

Long-term, Sorigamis grows beyond Fixli's internal productivity tool into a broader AX/AI work orchestration platform.

### Target Users

- **Primary (MVP):** Fixli internal team (ops, sales, CS, product) — frequent meetings, no time for manual notes
- **Expansion:** Meeting-heavy startup and SMB teams

### User Scenarios

**Internal meeting:** User creates a recording → selects "Team Meeting" mode → records → saves locally → audio uploads to Google Drive → app triggers the AI pipeline → user views speaker-attributed transcript, summary, action items, and decision log.

**Field / offline conversation:** User records in low-connectivity → recording saves locally → on reconnect, the upload queue processes automatically → user reviews results once processing completes.

**Multilingual meeting:** User sets language to "auto" (or picks Korean/English) → Whisper detects and transcribes → Stage 2 returns results in the user's configured output language.

### Key Metrics

- Upload / processing completion rate vs. recordings created
- AI processing success rate and average processing time
- Weekly active users (WAU) and recordings per user per week
- Result view rate (sessions where results were opened)
- Crash-free session rate

---

## 2. Milestones & Roadmap

The build is split into two milestones along a clean seam: the **mobile app** and the **AI pipeline integration**. The app is designed so Milestone 1 is fully functional and demoable on its own, with the pipeline mocked.

### Milestone 1 — Mobile App

Everything the user touches, end to end, with the pipeline **stubbed**:
- Onboarding, permissions, Firebase Auth (Google sign-in)
- Recording (record / pause / stop, background-safe), local SQLite storage
- Modes & Skills configuration and management
- Google Drive audio upload (OAuth, upload queue, retry)
- Result viewing UI (transcript + per-skill sections) rendered against a **mock pipeline client** returning canned results
- Settings, including the Pipeline Server URL field (validated against `/health`)

The app talks to the pipeline through a repository interface (Section 8). In M1 that interface is backed by a stub/mock server, so the whole UX — including the result screens — can be built and tested with no real AI.

### Milestone 2 — AI Integration & Pipeline

Stand up the real pipeline and wire the app to it:
- Pipeline server wrapping the existing `test_audio_diarize.py` (Stage 1) + new Stage 2 multi-agent step
- Real implementation of the job submission / status / result contract
- Skill config → pipeline parameter mapping
- Multilingual transcription/summarization
- Swap the app's mock pipeline client for the live one — no UI changes

**Deployment for M2:** the pipeline runs **on a developer machine on the local network** (LAN), wrapped in a thin FastAPI server; the app reaches it via the Pipeline Server URL. The API contract is identical to a future cloud deployment (Milestone 3), so that migration is just hosting the same server, swapping the URL, and adding FCM push.

### Milestone 3 — Cloud

- Cloud-hosted pipeline with job queue + object storage
- FCM push notifications on completion (replaces poll-only)
- Multi-user / team sharing, Fixli orchestrator integration

---

## 3. Architecture

### System Layers

```
┌─────────────────────────────────────────────────────┐
│                   Sorigamis (Flutter)                 │  ← Milestone 1
│                                                     │
│  UI Layer        Screens + Widgets (Riverpod)       │
│  Domain Layer    Use cases, entities, interfaces    │
│  Data Layer      Repositories, local DB, API client │
└──────┬──────────────────┬──────────────────┬────────┘
       │ Firebase Auth JWT │ Google Drive     │ Pipeline REST
       ▼                   ▼ OAuth            ▼ (mock in M1, LAN in M2)
 ┌───────────┐   ┌──────────────┐   ┌─────────────────────────┐
 │ Firebase  │   │ Google Drive │   │  Pipeline Server        │  ← Milestone 2
 │ Auth      │   │ (audio       │   │  (FastAPI wrapper)      │
 │           │   │  backup)     │   │   Stage 1: transcode →  │
 └───────────┘   └──────────────┘   │    whisper → pyannote → │
                                     │    ECAPA reassign       │
                                     │   Stage 2: LLM agents   │
                                     └─────────────────────────┘
```

### Key Decisions

- **Flutter + Riverpod** — async job polling fits provider pattern cleanly; avoids BLoC boilerplate
- **Clean architecture (3 layers)** — UI never touches network directly; repositories abstract local vs. remote and let the pipeline be mocked in M1
- **Drift (SQLite)** — offline-first local DB; recordings, metadata, and cached AI results survive offline
- **Firebase Auth** — identity and JWT tokens only
- **Google Drive OAuth** — separate credential from app auth, stored encrypted in local DB
- **WorkManager** (Android) / **BGTaskScheduler** (iOS) — keeps Drive uploads and polling alive in background
- **Configurable pipeline base URL** — mock in M1, LAN IP in M2, hosted URL in M3; same contract throughout

---

# Milestone 1 — Mobile App

## 4. Modes & Skills System

This is the central design concept of Sorigamis.

### Concepts

**Mode** is the user-facing concept — a named recording context with an icon, backed by a set of Skills. Users see and interact with Modes everywhere: on the recording screen, in the recordings list, and in Settings.

**Skill** is the underlying AI capability. A Skill captures *user intent* — what to transcribe and what to produce — in pipeline-agnostic terms, plus an optional opaque overrides bag. In Milestone 1 these fields are authored and stored by the app; Milestone 2 maps them onto the pipeline's actual parameters. Users manage Skills in Settings but never select them per recording.

```
Mode "Team Meeting" 🗓
  └── Skill: Meeting Summary   (Stage1: auto speakers, ko/auto • Stage2: summary, concise)
  └── Skill: Action Items      (Stage1: assignee detection on • Stage2: tasks)
  └── Skill: Decision Log      (Stage2: custom focus: decisions made)
```

### Seed Modes (shipped with app, editable)

| Mode | Icon | Skills included |
|------|------|-----------------|
| General | 📝 | Summary, Action Items |
| Team Meeting | 🗓 | Meeting Summary, Action Items, Decision Log |
| Sales Call | 📞 | Call Summary, Follow-ups |
| Standup | ⚡ | Standup Digest, Blockers |
| Interview | 🎙 | Interview Summary, Key Quotes |

**General** is the default mode for new users. All seed modes are editable and deletable.

### Skill Configuration

A Skill describes **user intent**, not pipeline internals. The app stores stable, pipeline-agnostic fields; the pipeline owns the mapping from intent to whatever knobs its current implementation exposes (Section 10). This keeps the app's data model durable as `test_audio_diarize.py` and Stage 2 evolve — adding or changing a pipeline knob never forces an app schema migration.

**Transcription intent** (what to transcribe, not how):
- `language` — `auto | ko | en | ...` (spoken language; `auto` = let the pipeline detect)
- `identifySpeakers` — Bool; "tell me who said what" (the pipeline decides how — diarization, speaker count, etc.)
- `vocabularyHints` — `List<String>`; domain terms to recognize accurately, e.g. `["Fixli", "OKR", "Sorigamis"]`

**Output intent** (what to produce from the transcript):
- `outputType` — `summary | tasks | both | custom`
- `focusArea` — free text: `"decisions made"`, `"blockers"`, `"commitments"`
- `tone` — `formal | casual | concise`
- `outputLanguage` — `auto | ko | en | ...` (may differ from spoken language)
- `additionalInstructions` — free-text for power users

**Advanced overrides** (escape hatch, optional):
- `pipelineParams` — opaque `Map<String, dynamic>` (JSON) passed through to the pipeline untouched. This is where implementation-specific knobs live (e.g. `{"num_speakers": 2, "vad_threshold": 0.6, "whisper_model": "large-v3"}`). The app neither validates nor interprets these — it forwards them, and the pipeline merges them over its defaults. New pipeline knobs are usable immediately with no app release.

Most users only touch Output intent; seed Skills set sensible transcription defaults. `pipelineParams` stays empty unless a power user fills it.

> **Scalability path:** the pipeline can later expose a `/capabilities` schema describing its tunable params, and the app can render the Advanced section dynamically from that schema — so even the advanced UI tracks the pipeline without app updates. Out of scope for M1/M2; the opaque bag is the MVP mechanism.

### Mode Selection UX

```
RecordingsScreen
  └── [● Record] FAB tapped
        └── RecordingInfoSheet (bottom sheet)
              ┌─────────────────────────────────────┐
              │  🗓 Team  │ 📞 Sales │ ⚡ Standup │ +│
              │  Meeting  │  Call    │             │  │
              │  (active) │          │             │  │
              └─────────────────────────────────────┘
              Title (required)
              Memo / Tags / Language  (optional, collapsed)
              [Start Recording]
```

- Active mode chip is highlighted; persists from last session via `UserSettings.activeModeId`
- `+` opens custom skill multi-select for this recording only (does not change the mode)
- New users start with **General** mode pre-selected

---

## 5. Data Model

### Local Database (Drift/SQLite)

```
Recording
├── id                UUID (PK)
├── title             String
├── memo              String?
├── tags              List<String>
├── category          String?   ('meeting' | 'interview' | 'call' | 'note' | ...)
├── language          String    ('auto' | 'ko' | 'en' | ...)
├── modeId            UUID?     (FK → Mode, nullable = General mode)
├── customSkillIds    List<UUID>? (per-recording skill override)
├── createdAt         DateTime
├── updatedAt         DateTime
├── audioFilePath     String    (local file path)
├── audioDuration     Duration?
├── audioFileSize     Int?      (bytes)
├── uploadStatus      Enum (none | queued | uploading | done | failed)
├── driveFileId       String?   (Google Drive file ID after upload)
├── jobId             String?   (AI pipeline job ID)
├── jobStatus         Enum (none | requested | processing | completed | failed)
└── jobError          String?

RecordingResult
├── id                UUID (PK)
├── recordingId       UUID (FK → Recording)
├── transcript        String              (speaker-attributed, shared across skills)
├── skillResults      List<SkillResult>   (JSON, one entry per skill)
└── receivedAt        DateTime

SkillResult (embedded JSON)
├── skillId           UUID
├── skillName         String
└── output            String

Mode
├── id                UUID (PK)
├── name              String
├── icon              String        (emoji)
├── isDefault         Bool
├── isSeeded          Bool
└── createdAt         DateTime

ModeSkill  (Mode ↔ Skill, ordered)
├── modeId            UUID (FK → Mode)
├── skillId           UUID (FK → Skill)
└── sortOrder         Int

Skill
├── id                    UUID (PK)
├── name                  String
├── description           String?
│   # Transcription intent (pipeline-agnostic)
├── language              String    ('auto' | 'ko' | 'en' | ...)
├── identifySpeakers      Bool      ("who said what"; pipeline decides how)
├── vocabularyHints       List<String>  (domain terms to recognize accurately)
│   # Output intent
├── outputType            Enum (summary | tasks | both | custom)
├── focusArea             String?
├── tone                  Enum (formal | casual | concise)
├── outputLanguage        String
├── additionalInstructions String?
│   # Advanced — opaque passthrough; app never interprets these
├── pipelineParams        Map<String, dynamic>?  (JSON; merged over pipeline defaults)
└── createdAt             DateTime

UserSettings
├── userId                String    (Firebase UID)
├── activeModeId          UUID?     (last used mode, restored on app open)
├── pipelineServerUrl     String    (mock in M1; LAN IP in M2)
├── defaultLanguage       String
├── defaultCategory       String?
├── driveConnected        Bool
├── driveRefreshToken     String?   (encrypted via Flutter Secure Storage)
├── notificationsEnabled  Bool
└── fcmToken              String?   (Milestone 3; null until then)
```

### Key Decisions

- `pipelineServerUrl` — the one knob that flips between mock, LAN, and cloud
- `activeModeId` — restores last used mode on app open, zero tap for repeat users
- `customSkillIds` — per-recording skill override without mutating the mode
- Skill stores pipeline-agnostic intent + an opaque `pipelineParams` bag — the app's schema stays stable as the pipeline evolves; the pipeline owns intent→knob mapping
- `driveRefreshToken` stored via Flutter Secure Storage — never in plain SQLite
- `RecordingResult` lazy-loaded — only fetched when user opens ResultTab

---

## 6. Screen Flow

```
Onboarding (first launch only)
└── SplashScreen
    └── OnboardingScreen
        └── PermissionsScreen
            ├── Microphone permission request
            └── Storage permission request (Android)
                └── → GoogleSignInScreen → RecordingsScreen

Main (bottom nav: Recordings | Settings)
│
├── RecordingsScreen (list, search, filter by mode/category/tag)
│   │  Each card: title, mode icon, date, duration, status badge
│   │
│   ├── RecordingInfoSheet (FAB)
│   │   ├── Mode chip row     (seed modes first, + custom)
│   │   ├── Title             (required)
│   │   ├── Memo / Tags / Language  (optional, collapsed)
│   │   └── [Start Recording] → RecordingControlScreen
│   │         (start / pause / stop + live waveform + elapsed time)
│   │         └── on stop → save to local DB → RecordingsScreen
│   │
│   └── RecordingDetailScreen
│       ├── InfoTab           (metadata, mode used, edit title/memo/tags)
│       ├── UploadTab         (Google Drive status, upload/retry, target folder)
│       ├── AIProcessTab      (submit to pipeline, processing stage, retry)
│       └── ResultTab
│           ├── Transcript    (speaker-attributed, collapsible)
│           └── Per-skill result sections (collapsible, labelled by skill name)
│               e.g. "Action Items", "Decision Log", "Meeting Summary"
│               Copy / Share (native share sheet) per section
│
└── SettingsScreen
    ├── AccountSection            (Firebase user, sign out)
    ├── PipelineServerSection     (server URL, test connection via /health)
    ├── GoogleDriveSection        (connect/disconnect, target folder)
    ├── ModesSection
    │   ├── ModeListScreen        (all modes, seed modes first, set default)
    │   └── ModeEditScreen        (name, icon, skill multi-select with sort order)
    ├── SkillsSection
    │   ├── SkillListScreen       (all skills, grouped by output type)
    │   └── SkillEditScreen
    │       ├── Name / description
    │       ├── Output intent: output type / focus / tone / output language / instructions
    │       ├── Transcription intent: language / identify speakers / vocabulary hints
    │       └── Advanced (collapsed): pipelineParams key-value/JSON editor
    ├── DefaultsSection           (language, category)
    └── NotificationsSection      (toggle — Milestone 3)
```

### Key UX Decisions

- **Onboarding requests permissions before sign-in** — avoids cold-start denial mid-recording
- **Pipeline Server section** — a "Test connection" button hits `/health` and shows ✅/❌
- **Mode chip row** is the primary interaction on RecordingInfoSheet
- **Active mode persists** via `UserSettings.activeModeId`
- **Advanced `pipelineParams` hidden by default** — typical users never touch pipeline-specific knobs
- **ResultTab** sections labelled by skill name; transcript shows speaker attribution
- **RecordingsList** cards show the mode icon for at-a-glance scanning
- **Offline state** surfaced inline as a "waiting for connection" chip

---

## 7. App Error Handling & Offline Behaviour

### Google Drive Upload Queue
- `WorkManager` job persists across app restarts and device reboots
- Exponential backoff: 30s → 2m → 10m → manual retry after 3 failures
- Drive token expiry handled silently via refresh; re-auth surfaced only if refresh fails

### Recording Safety
- Audio written to temp file during recording; moved to permanent path only on clean stop
- Temp file detected on next launch → offered as recoverable draft
- Background recording via foreground `Service` (Android) + persistent notification / `AVAudioSession` (iOS)

### Auth
- Firebase token refresh transparent via Dio interceptor — retries once on 401 before prompting re-login
- Sign-out clears local DB records for the user's UID; audio files on-device are preserved

---

## 8. Pipeline Client Contract (M1 builds against; M2 implements)

The app reaches the pipeline through a repository interface. In Milestone 1 it is backed by a **mock client** (canned transcript + skill results, simulated delays/states) so the entire app — including the result screens — is buildable and demoable. Milestone 2 swaps in the live client with no UI changes.

### Authentication
All requests: `Authorization: Bearer <firebase_jwt>`.

### Endpoints (consumed by the app)

```
GET /api/v1/health
Response: { ok: true, version: String }

POST /api/v1/jobs
Body: multipart/form-data
  - audio_file:        binary      (any format — server transcodes)
  - recording_id:      UUID
  - audio_duration_s:  Int
  - category:          String?
  - mode_name:         String?
  - skills:            JSON array  (resolved skill config — see Section 10)
Response: { job_id: UUID, status: "requested" }

GET /api/v1/jobs/:job_id
Response: {
  job_id: UUID,
  status: "requested" | "processing" | "completed" | "failed",
  stage:  "transcribing" | "diarizing" | "summarizing" | null,
  error:  String?
}

GET /api/v1/jobs/:job_id/result
Response: {
  transcript: String,   # speaker-attributed
  skill_results: [ { skill_id: UUID, skill_name: String, output: String } ]
}
```

### Skill Resolution (app-side, before submission)

```
1. If recording has customSkillIds → use those
2. Else use skills from recording.modeId
3. Else use skills from the default mode
4. Else send empty skills array (server uses its own defaults)
```

### Polling Strategy

- App calls `/health` before submitting; if unreachable, surfaces "Pipeline server not reachable — check the URL in Settings"
- Start polling 10s after submission; interval 15s while `processing`, 30s after 5 min
- Max attempts: 40 (≈ 20 min); exhausted → `failed` with "Timed out — tap to retry"
- On app foreground → resume polling for any `processing` jobs
- Milestone 3: FCM `job_completed` push cancels polling and fetches the result immediately

---

# Milestone 2 — AI Integration & Pipeline

## 9. Audio Processing & Pipeline Integration

### Pipeline Server (M2 — local LAN)

A thin FastAPI wrapper (~150–250 lines) around the existing `test_audio_diarize.py`, plus a new Stage 2 step. Runs on a developer machine; the app reaches it via the Pipeline Server URL.

```
POST /api/v1/jobs        → save uploaded audio, spawn pipeline subprocess, return job_id
GET  /api/v1/jobs/:id    → status (requested | processing | completed | failed) + stage
GET  /api/v1/jobs/:id/result → parse diarized output + Stage 2 → JSON
GET  /api/v1/health      → liveness/version for the app's connection test
```

Implements the exact contract in Section 8. In M2 the server may relax JWT verification for local development, but the app always sends the header.

### Pipeline Stages

Stage 1 is the existing script, invoked with per-job env vars. Stage 2 is new.

```
Audio in (any format)
   │
   ▼ Stage 1 (test_audio_diarize.py)
 ┌──────────────────────────────────────────────┐
 │ 1. ffmpeg transcode → 16kHz mono WAV          │
 │ 2. faster-whisper ASR (word timestamps, VAD)  │  ← WHISPER_LANG, WHISPER_PROMPT,
 │ 3. pyannote diarization (if identify_speakers)│    WHISPER_VAD_THRESHOLD
 │ 4. ECAPA-TDNN centroid re-assignment          │  ← NUM_SPEAKERS
 │ → speaker-attributed transcript               │
 └──────────────────────────────────────────────┘
   │  (utterances: speaker_a/b/..., text, confidence)
   ▼ Stage 2 (new, per Skill)
 ┌──────────────────────────────────────────────┐
 │ For each Skill in the job:                    │
 │   assemble system prompt from Stage 2 fields  │
 │   + additionalInstructions                    │
 │   LLM call(transcript) → skill output         │
 └──────────────────────────────────────────────┘
   │
   ▼ store result → app polls /jobs/:id/result
```

### Audio Capture (app-side note)

- Recorded as M4A (AAC); the pipeline transcodes any input via ffmpeg, so format is flexible
- The pipeline always transcodes to 16 kHz mono WAV (Whisper's native input) regardless of source

---

## 10. Skill → Pipeline Parameter Mapping

The app sends **intent** plus an opaque `pipeline_params` bag. The pipeline owns the translation from intent to whatever knobs its current implementation exposes — so when `test_audio_diarize.py` changes, only this mapping layer changes, never the app.

The `skills` array in `POST /jobs` per skill:

```
skills: [
  {
    skill_id:                UUID,
    skill_name:              String,
    # transcription intent
    language:                String,        ('auto' | 'ko' | 'en' | ...)
    identify_speakers:       Bool,          ("who said what")
    vocabulary_hints:        [String],      (domain terms)
    # output intent
    output_type:             "summary" | "tasks" | "both" | "custom",
    focus_area:              String?,
    tone:                    "formal" | "casual" | "concise",
    output_language:         String,
    additional_instructions: String?,
    # opaque overrides — forwarded as-is, merged over pipeline defaults
    pipeline_params:         { ... }?       e.g. {"num_speakers": 2, "vad_threshold": 0.6}
  }
]
```

The mapping below is **owned by the pipeline (Milestone 2), not the app**. It reflects the *current* `test_audio_diarize.py` and is expected to change as the pipeline evolves:

| Intent field | Current pipeline target | Notes |
|---|---|---|
| `language` | `WHISPER_LANG` env | 'auto' → omit; pipeline detects |
| `vocabulary_hints` | `WHISPER_PROMPT` env | joined into the ASR initial prompt |
| `identify_speakers` | run pyannote diarization (or skip) + ECAPA reassign | off → transcript only, faster |
| `output_type` / `focus_area` / `tone` / `output_language` | Stage 2 system prompt | assembled structured |
| `additional_instructions` | Stage 2 system prompt | appended verbatim |
| `pipeline_params.*` | merged over pipeline defaults | e.g. `num_speakers`→`NUM_SPEAKERS`, `vad_threshold`→`WHISPER_VAD_THRESHOLD` |

### Stage 2 System Prompt Assembly

```
You are a {tone} assistant. Extract {output_type} from this meeting transcript.
The transcript is speaker-attributed (speaker_a, speaker_b, ...).
Focus on: {focus_area}.
{if output_type includes tasks} Attribute each action item to the speaker who committed to it.
Respond in {output_language}.

{additional_instructions}

Transcript:
{stage1_transcript}
```

---

## 11. Multilingual Support

- Whisper auto-detects language when `language = 'auto'`
- `output_language` controls Stage 2 output independently — Korean meeting → English summary is supported
- App UI language is independent of recording/result language

---

## 12. Pipeline-Side Error Handling

- App validates duration and file readability before submission; server validates again on receipt
- `stage` field in the status response drives the UI's "Transcribing… / Diarizing… / Summarizing…" hint
- If Stage 1 fails (e.g. corrupt audio, ffmpeg error), job → `failed` with the error message passed through
- If a Stage 2 skill fails, that skill's `output` carries an error note; other skills still return
- Server error messages passed through verbatim (internal users benefit from raw errors)

---

## 13. Out of Scope for Milestones 1–2

- Cloud-hosted pipeline, job queue, object storage (Milestone 3)
- FCM push notifications (Milestone 3 — poll-only until then)
- mDNS/Bonjour auto-discovery of the pipeline server (manual URL for now)
- Dropbox / OneDrive integration (Google Drive only)
- In-app audio playback of recordings
- Team / multi-user sharing of results
- Speaker labeling/renaming UI (pipeline outputs speaker_a/b; renaming deferred)
- Fixli orchestrator integration (future AX platform)
- App Store / Play Store submission pipeline
- Real-time live transcription during recording
