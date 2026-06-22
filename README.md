# Sorigamis

A cross-platform Flutter mobile app (Android + iOS) that records conversations and routes them through an AI pipeline to produce speaker-attributed transcripts, summaries, and action items.

## Status

M1 is tracked as **two parallel platform tracks — both 🚧 work in progress:**

| Track | Status | Notes |
|-------|--------|-------|
| **M1-iOS** 🚧 WIP | Foundation (Plan 1) done & verified on iOS Simulator | Shared Dart built test-driven (`flutter test` 9/9, `flutter analyze` clean); app launches, seeds 5 Modes, renders Recordings screen |
| **M1-Android** 🚧 WIP | Not yet built or run | Stock `flutter create` Android scaffold only; native setup (permissions, foreground service, WorkManager) still to come |

> The Dart/Flutter codebase is shared across both tracks — the split reflects **platform build & verification status**, not separate source trees. Tests run on the Dart VM and pass independently of platform.

Remaining M1 work is split into a [plan series](docs/superpowers/plans/2026-06-23-sorigamis-m1-plan-series.md), safest-first. See [RUNBOOK.md](RUNBOOK.md) for setup, build, and run instructions.

## Concept

The core interaction model is **Modes** — named recording contexts (e.g. "Team Meeting", "Sales Call") that bundle AI Skills and apply them automatically. Pick a Mode once, hit Record, get back structured results.

The app is a thin client: it records locally, uploads audio to Google Drive, and triggers the AI pipeline. All AI computation runs in the pipeline.

## Milestones

| Milestone | Scope |
|-----------|-------|
| **M1-iOS** 🚧 | Full app UI on iOS — onboarding, recording, Modes/Skills, Drive upload, result viewing — with the AI pipeline **mocked** |
| **M1-Android** 🚧 | Same app UI brought up and verified on Android (build, permissions, emulator/device run) |
| **M2 — AI Integration** | Real pipeline server (FastAPI) wrapping Whisper + pyannote diarization (Stage 1) + LLM multi-agent summarization (Stage 2), running on LAN |
| **M3 — Cloud** | Cloud-hosted pipeline, FCM push notifications, multi-user team sharing |

## Tech Stack

- **Flutter + Dart 3** — Android & iOS from one codebase
- **Riverpod** — state management
- **Drift (SQLite)** — offline-first local database
- **Firebase Auth** — Google sign-in
- **Google Drive API** — audio backup
- **FastAPI** (M2) — pipeline server wrapping `faster-whisper`, `pyannote.audio`, and Claude

## Architecture

```
┌─────────────────────────────────────────────┐
│              Sorigamis (Flutter)             │
│  UI Layer     Screens + Widgets (Riverpod)  │
│  Domain       Use cases, entities           │
│  Data         Repos, local DB, API clients  │
└──────┬────────────────┬──────────────────┬──┘
       │ Firebase Auth  │ Google Drive     │ Pipeline REST
       ▼                ▼                  ▼
  Firebase Auth    Google Drive      Pipeline Server
                   (audio backup)    (mock in M1, LAN in M2)
```

The pipeline is reached through a `PipelineClient` interface. Milestone 1 uses a mock; Milestone 2 swaps in the live HTTP client with no UI changes.

## Getting Started

New to Flutter or setting up a fresh machine? Follow **[RUNBOOK.md](RUNBOOK.md)** — it covers the full toolchain (Flutter SDK, Xcode, CocoaPods, simulator) step by step.

Once the toolchain is installed:

```bash
# Install dependencies
flutter pub get

# Generate Drift database code (after any change to DB tables/DAOs)
dart run build_runner build --delete-conflicting-outputs

# Run on a device/simulator
flutter run -d "iPhone 17 Pro"

# Run tests (Dart VM — no simulator needed)
flutter test
```

## Project Structure

```
docs/
  superpowers/
    specs/    Design spec
    plans/    Implementation plan series
lib/
  core/       enums, go_router config
  data/
    db/       Drift database, tables, DAOs (+ generated *.g.dart)
    seed/     seedIfEmpty() — default Modes & Skills
  features/
    recordings/   RecordingsScreen
  providers/  Riverpod providers (databaseProvider + DAO/stream providers)
  app.dart    MaterialApp.router shell
  main.dart   ProviderScope + DB init + seed
test/         Test suite (mirrors lib/)
ios/          iOS runner (built & verified)
android/      Android runner (stock scaffold — not yet built)
```

## Design Docs

- [Design Spec](docs/superpowers/specs/2026-06-21-sorigamis-design.md)
- [M1 Implementation Plan Series](docs/superpowers/plans/2026-06-23-sorigamis-m1-plan-series.md)
- [RUNBOOK — setup, build, run, troubleshooting](RUNBOOK.md)
