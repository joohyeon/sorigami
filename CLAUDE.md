# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sorigami** is a cross-platform Flutter mobile app (Android + iOS) that records conversations and routes them through an AI pipeline to produce speaker-attributed transcripts, summaries, and action items. The core concept is **Modes** — named recording contexts (e.g. "Team Meeting") that bundle AI Skills and apply them automatically.

The app is a thin client: record → store locally → upload to Google Drive → trigger AI pipeline → poll for results. All AI runs in the pipeline, not on device.

**Current state:** Only `docs/` exists. Flutter code has not been scaffolded yet.

## Build & Run Commands

```bash
# Run app on a connected device/emulator
flutter run -d <device>

# Run all tests
flutter test

# Run a single test file
flutter test test/path/to/foo_test.dart

# Generate Drift (SQLite ORM) code after schema changes
dart run build_runner build --delete-conflicting-outputs

# Configure Firebase (run once during setup)
dart pub global activate flutterfire_cli && flutterfire configure
```

## Architecture

**Three-layer clean architecture:**
- **UI Layer** — Screens + Widgets, powered by Riverpod providers (`features/`)
- **Domain Layer** — Plain Dart entities, use-case functions (`domain/`)
- **Data Layer** — Repositories, DAOs, local DB, pipeline/Drive API clients (`data/`)

The key seam is `PipelineClient` (abstract interface in `data/pipeline/pipeline_client.dart`). In Milestone 1 it is backed by `MockPipelineClient`; Milestone 2 swaps in a live HTTP client with no UI changes. Never bypass this interface.

**State management:** `flutter_riverpod`. The root `databaseProvider` is overridden in `main()` with a concrete `AppDatabase`; all DAO providers derive from it.

## Key Files & Layers

```
lib/
  main.dart                   ProviderScope + DB init + seed + Firebase.initializeApp
  app.dart                    MaterialApp.router, auth sync to currentUserIdProvider
  core/
    router.dart               go_router; redirects to /signin when no user
    enums.dart                UploadStatus, JobStatus, OutputType, Tone
  data/
    db/database.dart          Drift @DriftDatabase + tables (schemaVersion: 1)
    db/daos/                  RecordingDao, SkillDao, ModeDao, SettingsDao
    db/open_connection.dart   NativeDatabase for production; NativeDatabase.memory() in tests
    seed/seed_data.dart       seedIfEmpty() — inserts 5 seed Modes + Skills on first run
    pipeline/pipeline_client.dart    PipelineClient abstract + DTOs (SkillRequest, etc.)
    pipeline/mock_pipeline_client.dart  M1 mock (returns canned transcript/results)
    auth/auth_service.dart    Firebase Auth + GoogleSignIn wrapper
    drive/drive_uploader.dart Google Drive upload
  domain/
    models/skill_resolution.dart  resolveSkills() — maps recording → SkillRequest list
  features/
    auth/         sign_in_screen.dart
    onboarding/   permissions_screen.dart
    recordings/   recordings_screen.dart, recording_info_sheet.dart,
                  recording_control_screen.dart, recording_service.dart
    detail/       recording_detail_screen.dart + info_tab, upload_tab, ai_process_tab, result_tab
    settings/     settings_screen.dart + sub-screens for modes and skills
  providers/
    providers.dart   databaseProvider, DAO providers, pipelineClientProvider,
                     currentUserIdProvider, authServiceProvider
test/              Mirrors lib/ structure; uses NativeDatabase.memory() for DB tests
```

## Core Concepts

### Modes & Skills
- **Mode** — user-visible recording context (name + emoji icon + ordered list of Skills). 5 seed modes ship with the app: General (📝, default), Team Meeting (🗓), Sales Call (📞), Standup (⚡), Interview (🎙).
- **Skill** — captures AI intent in pipeline-agnostic terms: `language`, `identifySpeakers`, `vocabularyHints` (transcription intent) + `outputType`, `focusArea`, `tone`, `outputLanguage`, `additionalInstructions` (output intent) + opaque `pipelineParams: Map<String, dynamic>` (forwarded to pipeline as-is, never interpreted by the app).

### Skill Resolution Order (before pipeline submission)
1. `recording.customSkillIds` if set
2. Skills from `recording.modeId`
3. Skills from the default Mode
4. Empty (pipeline uses its own defaults)

### Pipeline Contract (fixed — do not change)
```
GET  /api/v1/health              → { ok: true, version: String }
POST /api/v1/jobs                → multipart: audio_file + recording_id + skills JSON → { job_id, status }
GET  /api/v1/jobs/:id            → { job_id, status, stage, error? }
GET  /api/v1/jobs/:id/result     → { transcript, skill_results: [{skill_id, skill_name, output}] }
```
All requests carry `Authorization: Bearer <firebase_jwt>`. Polling: start 10s after submit, 15s interval, max 40 attempts.

## Development Practices

**TDD is required:** every task writes the failing test first, then the implementation, then verifies it passes. Commit after each task.

**Drift code generation:** any change to `lib/data/db/database.dart` tables or DAOs requires running `dart run build_runner build --delete-conflicting-outputs` to regenerate `.g.dart` files.

**Secrets:** `driveRefreshToken` goes in `flutter_secure_storage` only — never in SQLite.

**pipelineServerUrl** in `UserSettings` is the single knob that switches between mock (empty), LAN IP (M2), and cloud URL (M3). The `/health` endpoint is used to validate it in Settings.

## Milestones

- **M1 (current):** Full app UI with `MockPipelineClient` — no real AI needed.
- **M2:** Real FastAPI pipeline server wrapping `test_audio_diarize.py` (Stage 1: ffmpeg → Whisper → pyannote → ECAPA-TDNN) + Stage 2 LLM multi-agent. Runs on LAN. Swap `MockPipelineClient` for live HTTP client.
- **M3:** Cloud-hosted pipeline, FCM push, multi-user.
