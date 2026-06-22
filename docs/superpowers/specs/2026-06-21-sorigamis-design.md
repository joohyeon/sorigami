# Sorigamis — Mobile App Design Spec
**Date:** 2026-06-21  
**Updated:** 2026-06-22  
**Status:** Approved

---

## 1. Overview

Sorigamis is a cross-platform mobile app (Android + iOS) that records conversations and routes them through an AI pipeline to produce speaker-attributed transcripts, summaries, and action items. The core interaction model is **Modes** — named recording contexts (e.g. "Team Meeting", "Sales Call") that bundle AI Skills and apply them automatically. Users pick a Mode once, hit Record, and get back structured results — and automatically triggered integration actions — without configuring anything per recording.

The app is a thin client: it records, stores metadata, backs up audio to the user's cloud (Google Drive), and triggers the AI pipeline. All AI computation and integration action execution happen in the pipeline, not on the device.

**Skills are the unit of extensibility.** Anyone can build a Skill — combining AI intent (what to extract from the audio) with integration actions (what to do with the result, e.g. create Linear tickets, post to Slack). Skills are publishable to an in-app **Skill Marketplace** so others can install and use them. A Mode is simply an ordered set of Skills applied together after a recording.

### Background

A working local AI pipeline already exists as the foundation for Sorigamis. It performs **Stage 1** processing: audio transcoding → automatic speech recognition (with word timestamps) → speaker diarization → speaker centroid re-assignment, producing a speaker-attributed transcript. It is multilingual (Korean + English) and runs on consumer hardware (CPU/MPS). The **Stage 2** multi-agent step — extracting summaries, tasks, decisions, and other structured outputs from the transcript — is new work that Skills drive.

Long-term, Sorigamis grows beyond Fixli's internal productivity tool into a broader AX/AI work orchestration platform.

### Target Users

- **Primary (MVP):** Fixli internal team (ops, sales, CS, product) — frequent meetings, no time for manual notes
- **Expansion:** Meeting-heavy startup and SMB teams

### User Scenarios

**Internal meeting:** User creates a recording → selects "Team Meeting" mode → records → saves locally → audio uploads to Google Drive → app triggers the AI pipeline → pipeline runs Stage 1 (transcript) → runs each Skill in order (AI extraction + integration actions) → user views unified results; action items were already created in Linear and posted to Slack.

**Field / offline conversation:** User records in low-connectivity → recording saves locally → on reconnect, the upload queue processes automatically → user reviews results once processing completes.

**Multilingual meeting:** User sets language to "auto" (or picks Korean/English) → Whisper detects and transcribes → Stage 2 returns results in the user's configured output language.

**Skill author:** Power user creates a "Sales Call Follow-up" Skill — AI intent set to extract commitments, action set to create a HubSpot deal note via webhook — publishes it to the Marketplace. Teammates install it with one tap.

### Key Metrics

- Upload / processing completion rate vs. recordings created
- AI processing success rate and average processing time
- Weekly active users (WAU) and recordings per user per week
- Result view rate (sessions where results were opened)
- Skill Marketplace installs and published skill count
- Crash-free session rate

---

## 2. Milestones & Roadmap

The build is split into two milestones along a clean seam: the **mobile app** and the **AI pipeline integration**. The app is designed so Milestone 1 is fully functional and demoable on its own, with the pipeline mocked.

### Milestone 1 — Mobile App

Everything the user touches, end to end, with the pipeline **stubbed**:
- Onboarding, permissions, Firebase Auth (Google sign-in)
- Recording (record / pause / stop, background-safe), local SQLite storage
- Modes & Skills configuration and management, including action config
- Skill Marketplace — browse, install, publish (backed by Firestore in M1)
- Google Drive audio upload (OAuth, upload queue, retry)
- Result viewing UI (transcript + per-skill sections + action logs) rendered against a **mock pipeline client** returning canned results
- Settings, including the Pipeline Server URL field (validated against `/health`)

### Milestone 2 — AI Integration & Pipeline

Stand up the real pipeline and wire the app to it:
- Pipeline server wrapping the existing `test_audio_diarize.py` (Stage 1) + new Stage 2 multi-agent step
- Sequential skill execution: Stage 1 once → Skills run in sortOrder, AI then actions per skill
- Integration action execution: Slack, Linear, Google Calendar, generic webhook
- Skill config → pipeline parameter mapping
- Multilingual transcription/summarization
- Swap the app's mock pipeline client for the live one — no UI changes

**Deployment for M2:** the pipeline runs **on a developer machine on the local network** (LAN), wrapped in a thin FastAPI server; the app reaches it via the Pipeline Server URL. The API contract is identical to a future cloud deployment (Milestone 3), so that migration is just hosting the same server, swapping the URL, and adding FCM push.

### Milestone 3 — Cloud

- Cloud-hosted pipeline with job queue + object storage
- FCM push notifications on completion (replaces poll-only)
- Multi-user / team sharing, Fixli orchestrator integration
- Marketplace moderation and featured skills curation

---

## 3. Architecture

### System Layers

```
┌─────────────────────────────────────────────────────┐
│                   Sorigamis (Flutter)                 │  ← Milestone 1
│                                                       │
│  UI Layer        Screens + Widgets (Riverpod)         │
│  Domain Layer    Use cases, entities, interfaces      │
│  Data Layer      Repositories, local DB, API clients  │
└──────┬──────────────────┬──────────────┬─────────────┘
       │ Firebase Auth JWT │ Google Drive │ Pipeline REST
       ▼                   ▼ OAuth        ▼ (mock in M1, LAN in M2)
 ┌───────────┐   ┌──────────────┐   ┌──────────────────────────────────┐
 │ Firebase  │   │ Google Drive │   │  Pipeline Server  (Milestone 2)  │
 │ Auth +    │   │ (audio       │   │  Stage 1: transcode → whisper →  │
 │ Firestore │   │  backup)     │   │    pyannote → ECAPA              │
 │ (Mktplace)│   └──────────────┘   │  Stage 2: LLM per Skill          │
 └───────────┘                      │  Actions: Slack / Linear /        │
                                    │    GCal / webhook per Skill       │
                                    └──────────────────────────────────┘
```

### Key Decisions

- **Flutter + Riverpod** — async job polling fits provider pattern cleanly; avoids BLoC boilerplate
- **Clean architecture (3 layers)** — UI never touches network directly; repositories abstract local vs. remote and let the pipeline be mocked in M1
- **Drift (SQLite)** — offline-first local DB; recordings, metadata, and cached AI results survive offline
- **Firebase Auth** — identity and JWT tokens only
- **Firestore** — Skill Marketplace catalog (read-heavy, simple document model)
- **Google Drive OAuth** — separate credential from app auth, stored encrypted in local DB
- **WorkManager** (Android) / **BGTaskScheduler** (iOS) — keeps Drive uploads and polling alive in background
- **Configurable pipeline base URL** — mock in M1, LAN IP in M2, hosted URL in M3; same contract throughout
- **Pipeline owns action execution** — keeps credentials off the device, matches the thin-client principle; adding new integration types requires pipeline updates, not app releases

---

# Milestone 1 — Mobile App

## 4. Modes & Skills System

This is the central design concept of Sorigamis.

### Concepts

**Mode** is the user-facing concept — a named recording context with an icon, backed by an **ordered** list of Skills. Users see and interact with Modes everywhere: on the recording screen, in the recordings list, and in Settings. The order of Skills in a Mode determines execution order in the pipeline.

**Skill** is a complete automation unit with three parts:
1. **AI intent** — what to extract from the transcript (pipeline-agnostic fields)
2. **Integration actions** — an ordered list of actions the pipeline fires after the AI step for that skill
3. **Marketplace metadata** — author, version, install count (populated only for published/installed skills)

```
Mode "Team Meeting" 🗓
  └── Skill 1: "Meeting Summary"
        AI intent:   output_type=summary, tone=concise
        Actions:     [{ type: slack, webhook_url: "...", message: "{{output}}" }]

  └── Skill 2: "Action Items"
        AI intent:   output_type=tasks, identify_speakers=true
        Actions:     [{ type: linear, api_key: "...", team_id: "...",
                        title: "{{task}}", assignee_from_speaker: true }]

  └── Skill 3: "Decision Log"
        AI intent:   output_type=custom, focus_area: "decisions made"
        Actions:     []
```

### Pipeline Execution Flow

Stage 1 runs once (shared across all skills). Then skills execute sequentially in sortOrder:

```
Audio in
  │
  ▼ Stage 1 (once, shared)
  Speaker-attributed transcript
  │
  ▼ Skill 1: "Meeting Summary"
    → AI extraction → output stored
    → Action: POST summary to Slack #general
  │
  ▼ Skill 2: "Action Items"
    → AI extraction (uses same Stage 1 transcript)
    → Action: Create Linear tickets, one per task
  │
  ▼ Skill 3: "Decision Log"
    → AI extraction
    → (no actions configured)
  │
  ▼ All results → app polls /jobs/:id/result
```

Each skill sees the Stage 1 transcript as input. Skills do not chain (Skill 2 does not receive Skill 1's output). Action failure does not abort subsequent skills.

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

**Transcription intent** (what to transcribe, not how):
- `language` — `auto | ko | en | ...` (spoken language; `auto` = let the pipeline detect)
- `identifySpeakers` — Bool; "tell me who said what"
- `vocabularyHints` — `List<String>`; domain terms to recognize accurately

**Output intent** (what to produce from the transcript):
- `outputType` — `summary | tasks | both | custom`
- `focusArea` — free text: `"decisions made"`, `"blockers"`, `"commitments"`
- `tone` — `formal | casual | concise`
- `outputLanguage` — `auto | ko | en | ...`
- `additionalInstructions` — free-text for power users

**Integration actions** (what to do after AI extraction):
- `actions` — ordered list of `SkillAction` entries (see data model)
- Supported types: `slack | linear | google_calendar | webhook`
- Templates support `{{output}}` (full AI output) and `{{speaker}}` (attributed speaker name)

**Advanced overrides** (escape hatch, optional):
- `pipelineParams` — opaque `Map<String, dynamic>` forwarded to pipeline untouched

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

## 5. Skill Marketplace

An in-app library where users publish, discover, and install Skills.

### Browsing & Installing

- Accessible from Settings → Skills → "Browse Marketplace"
- Skills listed with: name, description, author, install count, output type tag, action type badges
- One-tap install: skill is copied into the user's local skill library with all action config (including embedded credentials/URLs) included as the creator set them
- Installed skills appear in SkillListScreen with an "installed from marketplace" badge
- Search by name/tag; filter by output type or action type

### Publishing

- From SkillEditScreen → "Publish to Marketplace"
- Creator provides a short description and tags before publishing
- Published skills are **immutable snapshots** — editing creates a new version; installed users stay on their version until they manually update
- No moderation for MVP — any authenticated user can publish
- "Update available" badge appears on installed skills when the author publishes a new version

### Credential Model

Action config (Slack webhook URLs, Linear API keys, Google Calendar tokens, webhook URLs) is **embedded in the skill** and included in the marketplace snapshot. This is intentional: the creator's endpoint is the shared destination (e.g. a team's shared Linear workspace or Slack channel). Users who clone and edit a skill can redirect actions to their own endpoints.

### Skill Versioning

Version is a monotonically increasing integer, auto-incremented on each publish. No auto-update — manual update only.

### Marketplace Backend (M1)

Backed by **Firestore** (Firebase): a `marketplace_skills` collection where each document is a full skill snapshot. Read-heavy; write on publish/update. Authentication via Firebase Auth — only the author can update their own published skills.

---

## 6. Data Model

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
├── skillResults      List<SkillResult>   (JSON, one entry per skill in execution order)
└── receivedAt        DateTime

SkillResult (embedded JSON)
├── skillId           UUID
├── skillName         String
├── output            String
└── actionsLog        List<ActionLog>   (one entry per action)

ActionLog (embedded JSON)
├── type              String   ('slack' | 'linear' | 'google_calendar' | 'webhook')
├── firedAt           DateTime
├── success           Bool
└── error             String?

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
├── identifySpeakers      Bool
├── vocabularyHints       List<String>
│   # Output intent
├── outputType            Enum (summary | tasks | both | custom)
├── focusArea             String?
├── tone                  Enum (formal | casual | concise)
├── outputLanguage        String
├── additionalInstructions String?
│   # Advanced — opaque passthrough
├── pipelineParams        Map<String, dynamic>?
│   # Integration actions (new)
├── actions               List<SkillAction>   (JSON, ordered by sortOrder)
│   # Marketplace metadata (null for locally-created skills)
├── marketplaceSkillId    String?   (Firestore doc ID, null if not from marketplace)
├── marketplaceVersion    Int?
└── createdAt             DateTime

SkillAction (embedded JSON)
├── type                  Enum (slack | linear | google_calendar | webhook)
├── config                Map<String, dynamic>   (type-specific config — see below)
└── sortOrder             Int

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

**Action config shapes per type:**

```
slack:            { webhook_url: String, message_template: String }
linear:           { api_key: String, team_id: String, title_template: String,
                    assignee_from_speaker: Bool }
google_calendar:  { calendar_id: String, oauth_token: String,
                    event_title_template: String }
webhook:          { url: String, method: "POST"|"GET", headers: Map<String,String>?,
                    body_template: String }
```

Templates support `{{output}}` (skill AI output), `{{speaker}}` (speaker attribution from transcript), and `{{recording_title}}` (the recording's title as set by the user).

### Firestore (Marketplace Catalog)

```
marketplace_skills/{docId}
├── authorId          String   (Firebase UID)
├── authorName        String
├── name              String
├── description       String
├── tags              List<String>
├── outputType        String
├── actionTypes       List<String>   (e.g. ['slack', 'linear'])
├── latestVersion     Int
├── installCount      Int
├── skillSnapshot     Map   (full Skill config at publish time, incl. actions)
└── publishedAt       Timestamp
```

### Key Decisions

- `actions` stored as JSON array in Skill — pipeline receives the full action config per skill in the job submission payload
- `marketplaceSkillId` links local skill to its marketplace origin for update-checking
- `actionsLog` in `SkillResult` gives the debug view its per-action execution detail
- Firestore for marketplace — avoids running a custom catalog API in M1; auth-rules restrict writes to the author's UID

---

## 7. Screen Flow

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
│       ├── AIProcessTab      (submit to pipeline, processing stage + current skill, retry)
│       └── ResultTab
│           ├── Unified output view  (default — all skill outputs labelled by skill name)
│           │   Copy / Share (native share sheet) per skill section
│           └── [Skill Details] toggle  (debug view)
│               └── Per-skill expandable row
│                   ├── Skill name + status (✓ AI done → ✓ Actions fired | ✗ error)
│                   ├── AI output text
│                   └── Action log (type, fired_at, success/error per action)
│
└── SettingsScreen
    ├── AccountSection            (Firebase user, sign out)
    ├── PipelineServerSection     (server URL, test connection via /health)
    ├── GoogleDriveSection        (connect/disconnect, target folder)
    ├── ModesSection
    │   ├── ModeListScreen        (all modes, seed modes first, set default)
    │   └── ModeEditScreen        (name, icon, skill multi-select with sort order)
    ├── SkillsSection
    │   ├── SkillListScreen       (all skills; "installed" badge on marketplace skills)
    │   │   └── [Browse Marketplace] → MarketplaceScreen
    │   │       ├── Search / filter by tag, output type, action type
    │   │       ├── SkillCard: name, author, description, install count, action badges
    │   │       └── SkillDetailScreen
    │   │           ├── Full description, version, author, action type preview
    │   │           └── [Install] / [Update available] / [Installed ✓]
    │   └── SkillEditScreen
    │       ├── Name / description
    │       ├── Output intent: output type / focus / tone / output language / instructions
    │       ├── Transcription intent: language / identify speakers / vocabulary hints
    │       ├── Actions section
    │       │   ├── Action list (ordered, drag to reorder)
    │       │   └── ActionEditSheet (per action)
    │       │       ├── Type: Slack | Linear | Google Calendar | Webhook
    │       │       └── Type-specific config fields
    │       │           slack:    Webhook URL, message template
    │       │           linear:   API key, team ID, title template, assignee from speaker toggle
    │       │           gcal:     Calendar ID, OAuth connect, event title template
    │       │           webhook:  URL, method, headers, body template
    │       └── Advanced (collapsed): pipelineParams JSON editor
    │           [Publish to Marketplace] button (if skill is complete)
    ├── DefaultsSection           (language, category)
    └── NotificationsSection      (toggle — Milestone 3)
```

### Key UX Decisions

- **Onboarding requests permissions before sign-in** — avoids cold-start denial mid-recording
- **Pipeline Server section** — a "Test connection" button hits `/health` and shows ✅/❌
- **Mode chip row** is the primary interaction on RecordingInfoSheet
- **Active mode persists** via `UserSettings.activeModeId`
- **ResultTab** unified view is the default; Skill Details toggle for debug
- **AIProcessTab** shows current skill name and phase (AI / actions) during processing
- **RecordingsList** cards show the mode icon for at-a-glance scanning
- **Offline state** surfaced inline as a "waiting for connection" chip

---

## 8. App Error Handling & Offline Behaviour

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

## 9. Pipeline Client Contract (M1 builds against; M2 implements)

The app reaches the pipeline through a repository interface. In Milestone 1 it is backed by a **mock client** (canned transcript + skill results + action logs, simulated delays/states). Milestone 2 swaps in the live client with no UI changes.

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
  - skills:            JSON array  (resolved skill config incl. actions — see Section 11)
Response: { job_id: UUID, status: "requested" }

GET /api/v1/jobs/:job_id
Response: {
  job_id:         UUID,
  status:         "requested" | "processing" | "completed" | "failed",
  stage:          "transcribing" | "diarizing" | "running_skills" | null,
  current_skill:  { index: Int, name: String, phase: "ai" | "actions" } | null,
  error:          String?
}

GET /api/v1/jobs/:job_id/result
Response: {
  transcript:    String,   # speaker-attributed (Stage 1 output, shared across all skills)
  skill_results: [
    {
      skill_id:    UUID,
      skill_name:  String,
      output:      String,
      actions_log: [
        { type: String, fired_at: DateTime, success: Bool, error: String? }
      ]
    }
  ]
}

### Skill Resolution (app-side, before submission)

```
1. If recording has customSkillIds → use those
2. Else use skills from recording.modeId (in sortOrder)
3. Else use skills from the default mode
4. Else send empty skills array (server uses its own defaults)
```

### Polling Strategy

- App calls `/health` before submitting; if unreachable, surfaces "Pipeline server not reachable — check the URL in Settings"
- Start polling 10s after submission; interval 15s while `processing`, 30s after 5 min
- Max attempts: 40 (≈ 20 min); exhausted → `failed` with "Timed out — tap to retry"
- On app foreground → resume polling for any `processing` jobs
- Milestone 3: FCM `job_completed` push cancels polling and fetches result immediately

---

# Milestone 2 — AI Integration & Pipeline

## 10. Audio Processing & Pipeline Integration

### Pipeline Server (M2 — local LAN)

A thin FastAPI wrapper (~150–250 lines) around the existing Stage 1 audio pipeline, plus the new Stage 2 multi-agent step and integration action execution. Runs on a developer machine; the app reaches it via the Pipeline Server URL.

```
POST /api/v1/jobs        → save uploaded audio, spawn pipeline, return job_id
GET  /api/v1/jobs/:id    → status + current_skill progress
GET  /api/v1/jobs/:id/result → skill results + action logs
GET  /api/v1/health      → liveness/version
```

### Pipeline Stages

```
Audio in (any format)
   │
   ▼ Stage 1 (audio pipeline) — once, shared
 ┌──────────────────────────────────────────────┐
 │ 1. Transcode → 16kHz mono WAV                 │
 │ 2. ASR with word timestamps and VAD           │
 │ 3. Speaker diarization (if identify_speakers) │
 │ 4. Speaker centroid re-assignment             │
 │ → speaker-attributed transcript               │
 └──────────────────────────────────────────────┘
   │
   ▼ For each Skill in sortOrder:
 ┌──────────────────────────────────────────────┐
 │  a. Assemble Stage 2 prompt from AI intent    │
 │  b. LLM call(transcript) → skill output       │
 │  c. For each Action in skill.actions:         │
 │     - Interpolate {{output}}, {{speaker}}     │
 │     - Fire integration (Slack / Linear /      │
 │       GCal / webhook)                         │
 │     - Log result (success / error)            │
 │     - Failure → logged, does NOT abort        │
 └──────────────────────────────────────────────┘
   │
   ▼ store all results → status "completed"
```

### Audio Capture (app-side note)

- Recorded as M4A (AAC); the pipeline transcodes any input via ffmpeg
- Pipeline always transcodes to 16 kHz mono WAV (Whisper's native input)

---

## 11. Skill → Pipeline Parameter Mapping

The `skills` array in `POST /jobs`, per skill:

```json
{
  "skill_id":                "UUID",
  "skill_name":              "String",
  "sort_order":              0,
  "language":                "auto",
  "identify_speakers":       true,
  "vocabulary_hints":        ["Fixli", "OKR"],
  "output_type":             "tasks",
  "focus_area":              "String?",
  "tone":                    "concise",
  "output_language":         "en",
  "additional_instructions": "String?",
  "pipeline_params":         {},
  "actions": [
    {
      "type":   "linear",
      "config": {
        "api_key":              "lin_...",
        "team_id":              "TEAM_ID",
        "title_template":       "{{output}}",
        "assignee_from_speaker": true
      },
      "sort_order": 0
    },
    {
      "type":   "slack",
      "config": {
        "webhook_url":       "https://hooks.slack.com/...",
        "message_template":  "Action items from {{recording_title}}:\n{{output}}"
      },
      "sort_order": 1
    }
  ]
}
```

Intent → pipeline mapping (owned by pipeline, expected to change as pipeline evolves):

| Intent field | Current pipeline target | Notes |
|---|---|---|
| `language` | ASR language setting | 'auto' → omit; pipeline detects |
| `vocabulary_hints` | ASR initial prompt / vocabulary bias | joined to improve domain term recognition |
| `identify_speakers` | enable/disable diarization | off → transcript only, faster |
| `output_type` / `focus_area` / `tone` / `output_language` | Stage 2 system prompt | assembled structured |
| `additional_instructions` | Stage 2 system prompt | appended verbatim |
| `pipeline_params.*` | merged over pipeline defaults | e.g. `num_speakers`, `vad_threshold` |
| `actions` | executed after Stage 2 per skill | pipeline resolves templates + fires integrations |

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

## 12. Multilingual Support

- Whisper auto-detects language when `language = 'auto'`
- `output_language` controls Stage 2 output independently — Korean meeting → English summary is supported
- App UI language is independent of recording/result language

---

## 13. Pipeline-Side Error Handling

- App validates duration and file readability before submission; server validates again on receipt
- `current_skill` field in status response drives the UI's per-skill progress indicator
- If Stage 1 fails (e.g. corrupt audio, ffmpeg error), job → `failed` with error passed through
- If a Skill's AI step fails, its actions are skipped; failure noted in `actions_log`; subsequent skills still run
- If an action fails, it is logged with the error; the next action and next skill still run
- Server error messages passed through verbatim (internal users benefit from raw errors)

---

## 14. Out of Scope for Milestones 1–2

- Cloud-hosted pipeline, job queue, object storage (Milestone 3)
- FCM push notifications (Milestone 3 — poll-only until then)
- Marketplace moderation / featured skills curation (Milestone 3)
- Skill chaining (later skill consuming earlier skill's output as input)
- mDNS/Bonjour auto-discovery of the pipeline server (manual URL for now)
- Dropbox / OneDrive integration (Google Drive only)
- In-app audio playback of recordings
- Team / multi-user sharing of results
- Speaker labeling/renaming UI (pipeline outputs speaker_a/b; renaming deferred)
- Fixli orchestrator integration (future AX platform)
- App Store / Play Store submission pipeline
- Real-time live transcription during recording
- Marketplace analytics dashboard for skill authors
