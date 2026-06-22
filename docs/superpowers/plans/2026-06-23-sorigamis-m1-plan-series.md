# Sorigamis M1 — Implementation Plan Series (Overview)

> **For agentic workers:** Each plan in this series is a standalone document. REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Milestone 1 of Sorigamis — a fully demoable Flutter app running against a mock pipeline — as a sequence of independently-shippable plans, safest-first for a developer new to Flutter.

**Why a series, not one plan:** M1 touches seven loosely-coupled subsystems. Building them as separate plans keeps each one runnable and reviewable on its own, and front-loads the parts with zero native risk so you build Flutter fluency before hitting OAuth and background services.

## Build order (safest first)

| Plan | Subsystem | Deliverable | Native risk |
|------|-----------|-------------|-------------|
| **1** | **Foundation & Recordings list** | App runs; Drift DB seeds 5 Modes; RecordingsScreen shows mode chips + empty list | none |
| 2 | Mock pipeline + Detail/Result flow | Create a recording row, submit to `MockPipelineClient`, poll, render transcript + per-skill results | none |
| 3 | Modes & Skills + Settings | Full CRUD for Modes/Skills/Actions; Settings screens | none |
| 4 | Audio recording | record/pause/stop, waveform, permissions, draft recovery | ⚠️ medium |
| 5 | Firebase Auth | Google sign-in, JWT, auth-gated router redirect | ⚠️ medium |
| 6 | Skill Marketplace | Firestore browse/install/publish | low |
| 7 | Drive upload + background | OAuth, upload queue, WorkManager/BGTaskScheduler, foreground recording service | 🔴 hardest |

Each plan's first task assumes the previous plan merged to `main`. Only **Plan 1 is fully detailed below.** Ask for Plan 2+ when you finish the prior one — written one at a time so the code stays accurate to what actually exists in the repo by then.

---

# Plan 1 — Foundation & Recordings List

**Goal:** A Flutter app that launches on a device, initializes a Drift (SQLite) database, seeds the 5 default Modes and their Skills on first run, and shows the Recordings screen with a live mode-chip row and an empty recordings list — all DB logic test-driven against an in-memory database.

**Architecture:** Three-layer clean architecture per CLAUDE.md. Drift owns persistence; Riverpod providers expose DAOs to the UI; the root `databaseProvider` is overridden in `main()` with a real `AppDatabase` and overridden with an in-memory one in tests. No network, no auth, no audio yet.

**Tech Stack:** Flutter (stable), Dart, `flutter_riverpod`, `drift` + `sqlite3_flutter_libs`, `go_router`, `uuid`, `build_runner`/`drift_dev` (codegen), `flutter_test`.

## Global Constraints

- Project name / package: `sorigamis` (verbatim — matches repo and CLAUDE.md).
- Drift `schemaVersion: 1` (per CLAUDE.md).
- Any change to `lib/data/db/database.dart` tables or DAOs requires regenerating code: `dart run build_runner build --delete-conflicting-outputs`.
- TDD is required: failing test first, then implementation, verify pass, commit per task.
- Production DB opens via `NativeDatabase` (file); tests use `NativeDatabase.memory()`.
- The 5 seed Modes: General (📝, default), Team Meeting (🗓), Sales Call (📞), Standup (⚡), Interview (🎙).
- Generated files (`*.g.dart`) are committed.

## File Structure

```
pubspec.yaml                         deps + flutter config
lib/
  main.dart                          ProviderScope + DB init + seedIfEmpty
  app.dart                           MaterialApp.router
  core/
    enums.dart                       UploadStatus, JobStatus, OutputType, Tone
    router.dart                      go_router config (Recordings only for now)
  data/
    db/
      open_connection.dart           file-backed LazyDatabase for production
      database.dart                  @DriftDatabase: tables + converters
      database.g.dart                GENERATED
      converters.dart                StringListConverter (List<String> <-> JSON)
      daos/
        recording_dao.dart           watchAll, insert (minimal)
        mode_dao.dart                watchAll, getDefault, insert
        skill_dao.dart               watchAll, insert
    seed/
      seed_data.dart                 seedIfEmpty()
  providers/
    providers.dart                   databaseProvider + DAO providers
  features/
    recordings/
      recordings_screen.dart         mode chip row + empty list
test/
  data/db/converters_test.dart
  data/db/recording_dao_test.dart
  data/db/mode_dao_test.dart
  data/seed/seed_data_test.dart
  features/recordings/recordings_screen_test.dart
  helpers/test_database.dart         builds an in-memory AppDatabase
```

---

### Task 1: Environment setup, scaffold, first run

No automated test — the deliverable is a running app, verified manually on a device. Fold all toolchain setup here.

- [ ] **Step 1: Install the Flutter SDK**

macOS: install via the official tarball or Homebrew.

```bash
brew install --cask flutter
```

If `brew` isn't available, follow https://docs.flutter.dev/get-started/install/macos and add the SDK `bin` to your `PATH` in `~/.zshrc`.

- [ ] **Step 2: Verify the toolchain**

Run: `flutter doctor`
Expected: Flutter shows a ✓. Resolve any ✗ for the platform you'll test on (Xcode for iOS, Android Studio + SDK for Android). You do NOT need both — pick one to start (iOS simulator is simplest on a Mac).

- [ ] **Step 3: Confirm a device is available**

Run: `flutter devices`
Expected: at least one device listed (e.g. "iPhone 15 Pro (simulator)"). To launch an iOS simulator: `open -a Simulator`.

- [ ] **Step 4: Scaffold the project into the current directory**

The repo already exists with `docs/` and `CLAUDE.md`; scaffold Flutter files into it without clobbering them.

```bash
cd /Users/hyeonjoo/VSCodeTestProjects/sorigamis
flutter create --project-name sorigamis --org com.fixli --platforms ios,android .
```

Expected: creates `lib/`, `ios/`, `android/`, `pubspec.yaml`, `test/`. Existing `docs/`, `CLAUDE.md`, `.git` are preserved.

- [ ] **Step 5: Run the default counter app on your device**

Run: `flutter run -d <device-id-from-step-3>`
Expected: the default Flutter counter app launches. Press `r` for hot reload, `q` to quit. This confirms the toolchain end-to-end.

- [ ] **Step 6: Commit the scaffold**

```bash
git add -A
git commit -m "chore: scaffold Flutter project (sorigamis)"
```

---

### Task 2: Dependencies, enums, and the StringList converter

**Files:**
- Modify: `pubspec.yaml`
- Create: `lib/core/enums.dart`
- Create: `lib/data/db/converters.dart`
- Test: `test/data/db/converters_test.dart`

**Interfaces:**
- Produces: `enum UploadStatus { none, queued, uploading, done, failed }`, `enum JobStatus { none, requested, processing, completed, failed }`, `enum OutputType { summary, tasks, both, custom }`, `enum Tone { formal, casual, concise }`
- Produces: `class StringListConverter extends TypeConverter<List<String>, String>` with `String toSql(List<String>)` and `List<String> fromSql(String)`.

- [ ] **Step 1: Add dependencies**

Edit `pubspec.yaml` so the `dependencies` and `dev_dependencies` sections include (keep the generated `flutter:` and `sdk:` lines):

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.5.1
  drift: ^2.18.0
  sqlite3_flutter_libs: ^0.5.20
  path_provider: ^2.1.3
  path: ^1.9.0
  go_router: ^14.1.0
  uuid: ^4.4.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  drift_dev: ^2.18.0
  build_runner: ^2.4.9
```

Run: `flutter pub get`
Expected: "Got dependencies!" with no version conflicts.

- [ ] **Step 2: Write the enums**

Create `lib/core/enums.dart`:

```dart
/// Drive upload lifecycle for a recording.
enum UploadStatus { none, queued, uploading, done, failed }

/// AI pipeline job lifecycle for a recording.
enum JobStatus { none, requested, processing, completed, failed }

/// What a Skill produces from the transcript.
enum OutputType { summary, tasks, both, custom }

/// Tone of the Skill's AI output.
enum Tone { formal, casual, concise }
```

- [ ] **Step 3: Write the failing test for the converter**

Create `test/data/db/converters_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/converters.dart';

void main() {
  final converter = const StringListConverter();

  test('round-trips a non-empty list through SQL form', () {
    const input = ['Fixli', 'OKR', 'standup'];
    final sql = converter.toSql(input);
    expect(converter.fromSql(sql), input);
  });

  test('maps an empty list to an empty list, not null', () {
    expect(converter.fromSql(converter.toSql(const [])), const <String>[]);
  });
}
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `flutter test test/data/db/converters_test.dart`
Expected: FAIL — `converters.dart` / `StringListConverter` not found.

- [ ] **Step 5: Implement the converter**

Create `lib/data/db/converters.dart`:

```dart
import 'dart:convert';
import 'package:drift/drift.dart';

/// Stores a `List<String>` as a JSON-encoded text column.
class StringListConverter extends TypeConverter<List<String>, String> {
  const StringListConverter();

  @override
  String toSql(List<String> value) => jsonEncode(value);

  @override
  List<String> fromSql(String fromDb) =>
      (jsonDecode(fromDb) as List<dynamic>).cast<String>();
}
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `flutter test test/data/db/converters_test.dart`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add pubspec.yaml pubspec.lock lib/core/enums.dart lib/data/db/converters.dart test/data/db/converters_test.dart
git commit -m "feat: add deps, core enums, and StringList converter"
```

---

### Task 3: Drift database, tables, and codegen

**Files:**
- Create: `lib/data/db/open_connection.dart`
- Create: `lib/data/db/database.dart`
- Create (generated): `lib/data/db/database.g.dart`
- Create: `test/helpers/test_database.dart`

**Interfaces:**
- Produces: `class AppDatabase extends _$AppDatabase` with constructor `AppDatabase(QueryExecutor e)`, `int get schemaVersion => 1`, and tables `Recordings`, `Modes`, `Skills`, `ModeSkills`.
- Produces: generated row classes `Recording`, `Mode`, `Skill`, `ModeSkill` and companions `RecordingsCompanion`, `ModesCompanion`, `SkillsCompanion`, `ModeSkillsCompanion`.
- Produces test helper: `AppDatabase newTestDatabase()` (in-memory).

- [ ] **Step 1: Write the production connection opener**

Create `lib/data/db/open_connection.dart`:

```dart
import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// File-backed database used in production (the app process).
LazyDatabase openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'sorigamis.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
```

- [ ] **Step 2: Write the database + tables**

Create `lib/data/db/database.dart`. (`part 'database.g.dart';` will be red until Step 4 generates it — that's expected.)

```dart
import 'package:drift/drift.dart';
import 'open_connection.dart';
import 'converters.dart';

part 'database.g.dart';

class Recordings extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get memo => text().nullable()();
  TextColumn get tags => text().map(const StringListConverter())
      .withDefault(const Constant('[]'))();
  TextColumn get category => text().nullable()();
  TextColumn get language => text().withDefault(const Constant('auto'))();
  TextColumn get modeId => text().nullable()();
  TextColumn get audioFilePath => text()();
  IntColumn get audioDurationMs => integer().nullable()();
  IntColumn get audioFileSize => integer().nullable()();
  TextColumn get uploadStatus =>
      text().withDefault(const Constant('none'))();
  TextColumn get driveFileId => text().nullable()();
  TextColumn get jobId => text().nullable()();
  TextColumn get jobStatus =>
      text().withDefault(const Constant('none'))();
  TextColumn get jobError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Modes extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get icon => text()();
  BoolColumn get isDefault => boolean().withDefault(const Constant(false))();
  BoolColumn get isSeeded => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Skills extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();
  TextColumn get language => text().withDefault(const Constant('auto'))();
  BoolColumn get identifySpeakers =>
      boolean().withDefault(const Constant(true))();
  TextColumn get vocabularyHints => text().map(const StringListConverter())
      .withDefault(const Constant('[]'))();
  TextColumn get outputType =>
      text().withDefault(const Constant('summary'))();
  TextColumn get focusArea => text().nullable()();
  TextColumn get tone => text().withDefault(const Constant('concise'))();
  TextColumn get outputLanguage =>
      text().withDefault(const Constant('auto'))();
  TextColumn get additionalInstructions => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class ModeSkills extends Table {
  TextColumn get modeId => text()();
  TextColumn get skillId => text()();
  IntColumn get sortOrder => integer()();

  @override
  Set<Column> get primaryKey => {modeId, skillId};
}

@DriftDatabase(tables: [Recordings, Modes, Skills, ModeSkills])
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  /// Convenience constructor for production.
  AppDatabase.open() : super(openConnection());

  @override
  int get schemaVersion => 1;
}
```

- [ ] **Step 3: Run code generation**

Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: "Succeeded after ..." and `lib/data/db/database.g.dart` now exists. The `part` directive resolves and red squiggles clear.

- [ ] **Step 4: Write the test-database helper**

Create `test/helpers/test_database.dart`:

```dart
import 'package:drift/native.dart';
import 'package:sorigamis/data/db/database.dart';

/// Fresh in-memory database for each test.
AppDatabase newTestDatabase() => AppDatabase(NativeDatabase.memory());
```

- [ ] **Step 5: Write a schema smoke test**

Add `test/data/db/database_smoke_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import '../../helpers/test_database.dart';

void main() {
  test('opens an in-memory database at schema version 1', () async {
    final db = newTestDatabase();
    expect(db.schemaVersion, 1);
    // Querying a table forces schema creation without error.
    expect(await db.select(db.modes).get(), isEmpty);
    await db.close();
  });
}
```

- [ ] **Step 6: Run the smoke test**

Run: `flutter test test/data/db/database_smoke_test.dart`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add lib/data/db/ test/helpers/test_database.dart test/data/db/database_smoke_test.dart
git commit -m "feat: add Drift database with Recordings/Modes/Skills/ModeSkills tables"
```

---

### Task 4: DAOs (Mode, Skill, Recording)

**Files:**
- Create: `lib/data/db/daos/mode_dao.dart`
- Create: `lib/data/db/daos/skill_dao.dart`
- Create: `lib/data/db/daos/recording_dao.dart`
- Modify: `lib/data/db/database.dart` (register DAOs)
- Test: `test/data/db/mode_dao_test.dart`
- Test: `test/data/db/recording_dao_test.dart`

**Interfaces:**
- Produces: `ModeDao` with `Future<int> insertMode(ModesCompanion)`, `Stream<List<Mode>> watchAllModes()` (default mode first, then by name), `Future<Mode?> getDefaultMode()`.
- Produces: `SkillDao` with `Future<int> insertSkill(SkillsCompanion)`, `Future<int> linkSkillToMode({required String modeId, required String skillId, required int sortOrder})`, `Stream<List<Skill>> watchAllSkills()`.
- Produces: `RecordingDao` with `Stream<List<Recording>> watchAllRecordings()` (newest first), `Future<int> insertRecording(RecordingsCompanion)`.

- [ ] **Step 1: Write the failing DAO tests**

Create `test/data/db/mode_dao_test.dart`:

```dart
import 'package:drift/drift.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import '../../helpers/test_database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = newTestDatabase());
  tearDown(() => db.close());

  ModesCompanion mode(String id, String name, {bool isDefault = false}) =>
      ModesCompanion.insert(
        id: id,
        name: name,
        icon: '📝',
        isDefault: Value(isDefault),
        createdAt: DateTime(2026, 1, 1),
      );

  test('watchAllModes emits the default mode first', () async {
    await db.modeDao.insertMode(mode('b', 'Zeta'));
    await db.modeDao.insertMode(mode('a', 'Alpha', isDefault: true));

    final modes = await db.modeDao.watchAllModes().first;
    expect(modes.first.name, 'Alpha');
    expect(modes.first.isDefault, isTrue);
  });

  test('getDefaultMode returns the default, or null when none', () async {
    expect(await db.modeDao.getDefaultMode(), isNull);
    await db.modeDao.insertMode(mode('a', 'Alpha', isDefault: true));
    expect((await db.modeDao.getDefaultMode())!.name, 'Alpha');
  });
}
```

Create `test/data/db/recording_dao_test.dart`:

```dart
import 'package:drift/drift.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import '../../helpers/test_database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = newTestDatabase());
  tearDown(() => db.close());

  test('watchAllRecordings emits newest first', () async {
    await db.recordingDao.insertRecording(RecordingsCompanion.insert(
      id: 'old', title: 'Old', audioFilePath: '/tmp/old.m4a',
      createdAt: DateTime(2026, 1, 1), updatedAt: DateTime(2026, 1, 1),
    ));
    await db.recordingDao.insertRecording(RecordingsCompanion.insert(
      id: 'new', title: 'New', audioFilePath: '/tmp/new.m4a',
      createdAt: DateTime(2026, 6, 1), updatedAt: DateTime(2026, 6, 1),
    ));

    final rows = await db.recordingDao.watchAllRecordings().first;
    expect(rows.map((r) => r.id).toList(), ['new', 'old']);
  });
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `flutter test test/data/db/mode_dao_test.dart test/data/db/recording_dao_test.dart`
Expected: FAIL — `db.modeDao` / `db.recordingDao` getters don't exist.

- [ ] **Step 3: Write the DAOs**

Create `lib/data/db/daos/mode_dao.dart`:

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'mode_dao.g.dart';

@DriftAccessor(tables: [Modes])
class ModeDao extends DatabaseAccessor<AppDatabase> with _$ModeDaoMixin {
  ModeDao(super.db);

  Future<int> insertMode(ModesCompanion entry) => into(modes).insert(entry);

  Stream<List<Mode>> watchAllModes() {
    return (select(modes)
          ..orderBy([
            (m) => OrderingTerm(expression: m.isDefault, mode: OrderingMode.desc),
            (m) => OrderingTerm(expression: m.name),
          ]))
        .watch();
  }

  Future<Mode?> getDefaultMode() {
    return (select(modes)..where((m) => m.isDefault.equals(true)))
        .getSingleOrNull();
  }
}
```

Create `lib/data/db/daos/skill_dao.dart`:

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'skill_dao.g.dart';

@DriftAccessor(tables: [Skills, ModeSkills])
class SkillDao extends DatabaseAccessor<AppDatabase> with _$SkillDaoMixin {
  SkillDao(super.db);

  Future<int> insertSkill(SkillsCompanion entry) => into(skills).insert(entry);

  Future<int> linkSkillToMode({
    required String modeId,
    required String skillId,
    required int sortOrder,
  }) {
    return into(modeSkills).insert(ModeSkillsCompanion.insert(
      modeId: modeId,
      skillId: skillId,
      sortOrder: sortOrder,
    ));
  }

  Stream<List<Skill>> watchAllSkills() =>
      (select(skills)..orderBy([(s) => OrderingTerm(expression: s.name)]))
          .watch();
}
```

Create `lib/data/db/daos/recording_dao.dart`:

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'recording_dao.g.dart';

@DriftAccessor(tables: [Recordings])
class RecordingDao extends DatabaseAccessor<AppDatabase>
    with _$RecordingDaoMixin {
  RecordingDao(super.db);

  Future<int> insertRecording(RecordingsCompanion entry) =>
      into(recordings).insert(entry);

  Stream<List<Recording>> watchAllRecordings() {
    return (select(recordings)
          ..orderBy([
            (r) => OrderingTerm(
                expression: r.createdAt, mode: OrderingMode.desc),
          ]))
        .watch();
  }
}
```

- [ ] **Step 4: Register the DAOs on the database**

In `lib/data/db/database.dart`, add the DAO imports below the existing imports:

```dart
import 'daos/mode_dao.dart';
import 'daos/skill_dao.dart';
import 'daos/recording_dao.dart';
```

Change the `@DriftDatabase` annotation to register the DAOs:

```dart
@DriftDatabase(
  tables: [Recordings, Modes, Skills, ModeSkills],
  daos: [RecordingDao, ModeDao, SkillDao],
)
```

- [ ] **Step 5: Regenerate code**

Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: generates `mode_dao.g.dart`, `skill_dao.g.dart`, `recording_dao.g.dart`, and adds `modeDao`/`skillDao`/`recordingDao` getters to `database.g.dart`.

- [ ] **Step 6: Run the DAO tests**

Run: `flutter test test/data/db/`
Expected: PASS (all DB tests).

- [ ] **Step 7: Commit**

```bash
git add lib/data/db/ test/data/db/
git commit -m "feat: add ModeDao, SkillDao, RecordingDao"
```

---

### Task 5: Seed data

**Files:**
- Create: `lib/data/seed/seed_data.dart`
- Test: `test/data/seed/seed_data_test.dart`

**Interfaces:**
- Consumes: `AppDatabase`, `ModeDao`, `SkillDao`.
- Produces: `Future<void> seedIfEmpty(AppDatabase db)` — inserts the 5 seed Modes and their Skills only when the `modes` table is empty; safe to call on every launch.

- [ ] **Step 1: Write the failing seed test**

Create `test/data/seed/seed_data_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/seed/seed_data.dart';
import '../../helpers/test_database.dart';

void main() {
  late final db = newTestDatabase();

  test('seeds 5 modes with General as default, and is idempotent', () async {
    final db = newTestDatabase();
    addTearDown(db.close);

    await seedIfEmpty(db);
    var modes = await db.modeDao.watchAllModes().first;
    expect(modes.length, 5);

    final general = modes.firstWhere((m) => m.name == 'General');
    expect(general.isDefault, isTrue);
    expect(general.icon, '📝');

    // Each seed mode links at least one skill.
    final skills = await db.skillDao.watchAllSkills().first;
    expect(skills, isNotEmpty);

    // Running again does not duplicate.
    await seedIfEmpty(db);
    modes = await db.modeDao.watchAllModes().first;
    expect(modes.length, 5);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `flutter test test/data/seed/seed_data_test.dart`
Expected: FAIL — `seed_data.dart` / `seedIfEmpty` not found.

- [ ] **Step 3: Implement the seed**

Create `lib/data/seed/seed_data.dart`:

```dart
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';
import '../db/database.dart';

const _uuid = Uuid();

/// Inserts the 5 default Modes and their Skills on first run only.
Future<void> seedIfEmpty(AppDatabase db) async {
  final existing = await db.modeDao.watchAllModes().first;
  if (existing.isNotEmpty) return;

  Future<String> addSkill(String name, String outputType,
      {String? focusArea}) async {
    final id = _uuid.v4();
    await db.skillDao.insertSkill(SkillsCompanion.insert(
      id: id,
      name: name,
      outputType: Value(outputType),
      focusArea: Value(focusArea),
      createdAt: DateTime.now(),
    ));
    return id;
  }

  Future<void> addMode(
      String name, String icon, List<String> skillIds,
      {bool isDefault = false}) async {
    final modeId = _uuid.v4();
    await db.modeDao.insertMode(ModesCompanion.insert(
      id: modeId,
      name: name,
      icon: icon,
      isDefault: Value(isDefault),
      isSeeded: const Value(true),
      createdAt: DateTime.now(),
    ));
    for (var i = 0; i < skillIds.length; i++) {
      await db.skillDao
          .linkSkillToMode(modeId: modeId, skillId: skillIds[i], sortOrder: i);
    }
  }

  final summary = await addSkill('Summary', 'summary');
  final actionItems = await addSkill('Action Items', 'tasks');
  final meetingSummary = await addSkill('Meeting Summary', 'summary');
  final decisionLog =
      await addSkill('Decision Log', 'custom', focusArea: 'decisions made');
  final callSummary = await addSkill('Call Summary', 'summary');
  final followUps =
      await addSkill('Follow-ups', 'tasks', focusArea: 'commitments');
  final standupDigest = await addSkill('Standup Digest', 'summary');
  final blockers = await addSkill('Blockers', 'tasks', focusArea: 'blockers');
  final interviewSummary = await addSkill('Interview Summary', 'summary');
  final keyQuotes =
      await addSkill('Key Quotes', 'custom', focusArea: 'key quotes');

  await addMode('General', '📝', [summary, actionItems], isDefault: true);
  await addMode('Team Meeting', '🗓', [meetingSummary, actionItems, decisionLog]);
  await addMode('Sales Call', '📞', [callSummary, followUps]);
  await addMode('Standup', '⚡', [standupDigest, blockers]);
  await addMode('Interview', '🎙', [interviewSummary, keyQuotes]);
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `flutter test test/data/seed/seed_data_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/data/seed/ test/data/seed/
git commit -m "feat: seed 5 default modes and skills on first run"
```

---

### Task 6: Riverpod providers and app entrypoint

**Files:**
- Create: `lib/providers/providers.dart`
- Create: `lib/main.dart` (overwrite the scaffold's default)
- Test: `test/providers/providers_test.dart`

**Interfaces:**
- Produces: `final databaseProvider = Provider<AppDatabase>((ref) => throw UnimplementedError('override in main'))`.
- Produces: `final recordingDaoProvider = Provider<RecordingDao>((ref) => ref.watch(databaseProvider).recordingDao)` and likewise `modeDaoProvider`, `skillDaoProvider`.
- Produces: `final allModesProvider = StreamProvider<List<Mode>>((ref) => ref.watch(modeDaoProvider).watchAllModes())` and `allRecordingsProvider` (Stream of `List<Recording>`).

- [ ] **Step 1: Write the failing provider test**

Create `test/providers/providers_test.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/seed/seed_data.dart';
import 'package:sorigamis/providers/providers.dart';
import 'package:sorigamis/data/db/database.dart';
import '../helpers/test_database.dart';

void main() {
  test('allModesProvider exposes seeded modes via the overridden db',
      () async {
    final db = newTestDatabase();
    await seedIfEmpty(db);
    addTearDown(db.close);

    final container = ProviderContainer(
      overrides: [databaseProvider.overrideWithValue(db)],
    );
    addTearDown(container.dispose);

    final modes = await container.read(allModesProvider.future);
    expect(modes.length, 5);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `flutter test test/providers/providers_test.dart`
Expected: FAIL — `providers.dart` not found.

- [ ] **Step 3: Write the providers**

Create `lib/providers/providers.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import '../data/db/daos/mode_dao.dart';
import '../data/db/daos/skill_dao.dart';
import '../data/db/daos/recording_dao.dart';

/// Overridden in main() with a concrete AppDatabase.
final databaseProvider = Provider<AppDatabase>(
  (ref) => throw UnimplementedError('databaseProvider must be overridden'),
);

final recordingDaoProvider =
    Provider<RecordingDao>((ref) => ref.watch(databaseProvider).recordingDao);
final modeDaoProvider =
    Provider<ModeDao>((ref) => ref.watch(databaseProvider).modeDao);
final skillDaoProvider =
    Provider<SkillDao>((ref) => ref.watch(databaseProvider).skillDao);

final allModesProvider = StreamProvider<List<Mode>>(
    (ref) => ref.watch(modeDaoProvider).watchAllModes());
final allRecordingsProvider = StreamProvider<List<Recording>>(
    (ref) => ref.watch(recordingDaoProvider).watchAllRecordings());
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `flutter test test/providers/providers_test.dart`
Expected: PASS.

- [ ] **Step 5: Write main.dart**

Overwrite `lib/main.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'data/db/database.dart';
import 'data/seed/seed_data.dart';
import 'providers/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final db = AppDatabase.open();
  await seedIfEmpty(db);

  runApp(
    ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const SorigamisApp(),
    ),
  );
}
```

(`app.dart` is created in Task 7 — `main.dart` won't compile until then; that's fine, they commit together would break the build, so Task 7 finishes the runnable slice. Do not run the app until Task 7.)

- [ ] **Step 6: Commit**

```bash
git add lib/providers/providers.dart lib/main.dart test/providers/providers_test.dart
git commit -m "feat: add Riverpod providers and app entrypoint with DB init + seed"
```

---

### Task 7: Router, app shell, and Recordings screen

**Files:**
- Create: `lib/core/router.dart`
- Create: `lib/app.dart`
- Create: `lib/features/recordings/recordings_screen.dart`
- Test: `test/features/recordings/recordings_screen_test.dart`

**Interfaces:**
- Consumes: `allModesProvider`, `allRecordingsProvider`, `databaseProvider`.
- Produces: `class SorigamisApp extends StatelessWidget` (uses `MaterialApp.router`), `final appRouter = GoRouter(...)` with a single `/` route → `RecordingsScreen`, and `class RecordingsScreen extends ConsumerWidget`.

- [ ] **Step 1: Write the failing widget test**

Create `test/features/recordings/recordings_screen_test.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/seed/seed_data.dart';
import 'package:sorigamis/features/recordings/recordings_screen.dart';
import 'package:sorigamis/providers/providers.dart';
import '../../helpers/test_database.dart';

void main() {
  testWidgets('shows mode chips and an empty-recordings message', (tester) async {
    final db = newTestDatabase();
    await seedIfEmpty(db);
    addTearDown(db.close);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [databaseProvider.overrideWithValue(db)],
        child: const MaterialApp(home: RecordingsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('General'), findsOneWidget);
    expect(find.text('Team Meeting'), findsOneWidget);
    expect(find.text('No recordings yet'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `flutter test test/features/recordings/recordings_screen_test.dart`
Expected: FAIL — `recordings_screen.dart` not found.

- [ ] **Step 3: Write the Recordings screen**

Create `lib/features/recordings/recordings_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/providers.dart';

class RecordingsScreen extends ConsumerWidget {
  const RecordingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final modes = ref.watch(allModesProvider);
    final recordings = ref.watch(allRecordingsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Recordings')),
      body: Column(
        children: [
          SizedBox(
            height: 56,
            child: modes.when(
              data: (list) => ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: list.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, i) {
                  final m = list[i];
                  return Center(
                    child: Chip(label: Text('${m.icon} ${m.name}')),
                  );
                },
              ),
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: recordings.when(
              data: (list) => list.isEmpty
                  ? const Center(child: Text('No recordings yet'))
                  : ListView.builder(
                      itemCount: list.length,
                      itemBuilder: (context, i) =>
                          ListTile(title: Text(list[i].title)),
                    ),
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {}, // RecordingInfoSheet — Plan 2
        child: const Icon(Icons.fiber_manual_record),
      ),
    );
  }
}
```

- [ ] **Step 4: Write the router and app shell**

Create `lib/core/router.dart`:

```dart
import 'package:go_router/go_router.dart';
import '../features/recordings/recordings_screen.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const RecordingsScreen()),
  ],
);
```

Create `lib/app.dart`:

```dart
import 'package:flutter/material.dart';
import 'core/router.dart';

class SorigamisApp extends StatelessWidget {
  const SorigamisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Sorigamis',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      routerConfig: appRouter,
    );
  }
}
```

- [ ] **Step 5: Run the widget test**

Run: `flutter test test/features/recordings/recordings_screen_test.dart`
Expected: PASS.

- [ ] **Step 6: Delete the scaffold's default widget test and run the full suite**

The scaffold created `test/widget_test.dart` referencing the old counter app; remove it.

```bash
rm test/widget_test.dart
flutter test
```

Expected: all tests PASS.

- [ ] **Step 7: Run the app on a device**

Run: `flutter run -d <device-id>`
Expected: app launches to the Recordings screen showing a horizontal row of mode chips (General, Team Meeting, Sales Call, Standup, Interview) and "No recordings yet". This is the Plan 1 deliverable.

- [ ] **Step 8: Commit**

```bash
git add lib/core/router.dart lib/app.dart lib/features/recordings/ test/features/recordings/
git rm test/widget_test.dart
git commit -m "feat: add router, app shell, and Recordings screen (Plan 1 complete)"
```

---

## Self-Review (Plan 1)

- **Spec coverage:** Plan 1 implements the foundation slice of §3 (3-layer architecture, Drift, Riverpod root `databaseProvider` override), the seed-modes requirement (§4 Seed Modes), the Recordings list shell with mode chips (§7 RecordingsScreen). It deliberately defers RecordingInfoSheet, audio, pipeline, auth, Drive, and marketplace to Plans 2–7. No M1 requirement is silently dropped — each is assigned to a later plan in the series table.
- **Placeholder scan:** No TBD/TODO/"handle edge cases" — every code step has complete code; the one stubbed `onPressed: () {}` on the FAB is intentional and labelled for Plan 2.
- **Type consistency:** DAO getter names (`modeDao`, `skillDao`, `recordingDao`) are consistent between Task 4 registration, the provider definitions in Task 6, and the tests. Companion field names (`isDefault`, `outputType`, `focusArea`) match the table columns in Task 3. `seedIfEmpty(AppDatabase)` signature matches its call site in `main.dart` and the test.
