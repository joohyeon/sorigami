# Sorigami

A cross-platform Flutter mobile app (Android + iOS) that records conversations and routes them through an AI pipeline to produce speaker-attributed transcripts, summaries, and action items.

## Concept

The core interaction model is **Modes** — named recording contexts (e.g. "Team Meeting", "Sales Call") that bundle AI Skills and apply them automatically. Pick a Mode once, hit Record, get back structured results.

The app is a thin client: it records locally, uploads audio to Google Drive, and triggers the AI pipeline. All AI computation runs in the pipeline.

## Milestones

| Milestone | Scope |
|-----------|-------|
| **M1 — Mobile App** | Full app UI — onboarding, recording, Modes/Skills, Drive upload, result viewing — with the AI pipeline **mocked** |
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
│              Sorigami (Flutter)              │
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

```bash
# Install dependencies
flutter pub get

# Generate Drift database code
dart run build_runner build --delete-conflicting-outputs

# Configure Firebase (first time only)
dart pub global activate flutterfire_cli && flutterfire configure

# Run on a connected device
flutter run -d <device>

# Run tests
flutter test
```

## Project Structure

```
docs/
  superpowers/
    specs/    Design spec
    plans/    Implementation plan
lib/          Flutter source (Milestone 1 — to be scaffolded)
test/         Test suite (mirrors lib/)
```

## Design Docs

- [Design Spec](docs/superpowers/specs/2026-06-21-sorigami-design.md)
- [Milestone 1 Implementation Plan](docs/superpowers/plans/2026-06-21-sorigami-milestone-1.md)
