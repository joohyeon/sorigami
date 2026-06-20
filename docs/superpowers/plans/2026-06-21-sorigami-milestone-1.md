# Sorigami Milestone 1 (Mobile App) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Sorigami Flutter app — record → metadata/Modes → Google Drive upload → trigger pipeline → view results — with the AI pipeline backed by a mock client so the whole UX is buildable and demoable without any real AI.

**Architecture:** Flutter + Riverpod, clean 3-layer (UI → domain → data). Drift (SQLite) for offline-first storage. Firebase Auth for Google sign-in. The pipeline is reached through a `PipelineClient` interface whose Milestone 1 implementation is a `MockPipelineClient` returning canned transcripts/skill results. Repositories abstract data sources so the mock swaps for the live client in M2 with no UI change.

**Tech Stack:** Flutter (Dart 3), flutter_riverpod, drift + sqlite3, firebase_auth + google_sign_in, googleapis (Drive), record (audio), dio (HTTP), go_router, flutter_secure_storage, workmanager.

## Global Constraints

- App name: **Sorigami** (verbatim, in all UI strings, package display name)
- Platforms: **Android + iOS** (Flutter single codebase)
- Pipeline contract is **fixed** (spec §8): `GET /health`, `POST /jobs`, `GET /jobs/:id`, `GET /jobs/:id/result`. M1 implements `PipelineClient` as a mock; do not change the contract.
- Skill model is **pipeline-agnostic** (spec §10): intent fields (`language`, `identifySpeakers`, `vocabularyHints`, `outputType`, `focusArea`, `tone`, `outputLanguage`, `additionalInstructions`) + opaque `pipelineParams` map. The app never interprets `pipelineParams`.
- Seed Modes (spec §4): General (📝, default), Team Meeting (🗓), Sales Call (📞), Standup (⚡), Interview (🎙).
- Result delivery is **poll-only** in M1 (no FCM).
- All persisted secrets (`driveRefreshToken`) go in `flutter_secure_storage`, never in SQLite.
- TDD: every task writes the failing test first. Commit after each task.

---

## File Structure

```
lib/
  main.dart                          App entry; ProviderScope; Firebase init
  app.dart                           MaterialApp.router; theme; router wiring
  core/
    router.dart                      go_router config + routes
    theme.dart                       ThemeData (light)
    enums.dart                       UploadStatus, JobStatus, OutputType, Tone
  data/
    db/
      database.dart                  Drift @DriftDatabase + tables
      database.g.dart                (generated)
      daos/
        recording_dao.dart
        skill_dao.dart
        mode_dao.dart
        settings_dao.dart
    seed/
      seed_data.dart                 Seed Modes + Skills inserted on first run
    pipeline/
      pipeline_client.dart           PipelineClient interface + DTOs
      mock_pipeline_client.dart      M1 mock implementation
    drive/
      drive_uploader.dart            Google Drive upload via googleapis
    auth/
      auth_service.dart              Firebase + Google sign-in
  domain/
    models/                          Plain Dart entities (mapped from Drift rows)
      recording.dart
      skill.dart
      mode.dart
      skill_resolution.dart          Resolve skills for a recording (spec §8)
  features/
    auth/        sign_in_screen.dart
    onboarding/  onboarding_screen.dart, permissions_screen.dart
    recordings/  recordings_screen.dart, recording_info_sheet.dart,
                 recording_control_screen.dart, recording_service.dart
    detail/      recording_detail_screen.dart, info_tab.dart, upload_tab.dart,
                 ai_process_tab.dart, result_tab.dart
    settings/    settings_screen.dart, pipeline_server_section.dart,
                 modes_section.dart, mode_edit_screen.dart,
                 skills_section.dart, skill_edit_screen.dart
  providers/                         Riverpod providers wiring repos to UI
test/
  ... mirrors lib/ ...
```

---

## Task 1: Project scaffold + dependencies

**Files:**
- Create: `pubspec.yaml`, `analysis_options.yaml`, `lib/main.dart`, `lib/app.dart`
- Create: platform folders via `flutter create`

**Interfaces:**
- Produces: a runnable Flutter app shell `SorigamiApp` (a `StatelessWidget` returning `MaterialApp`).

- [ ] **Step 1: Verify Flutter is installed**

Run: `flutter --version`
Expected: Flutter 3.x / Dart 3.x printed. If "command not found", install Flutter (https://docs.flutter.dev/get-started/install) and re-run before continuing.

- [ ] **Step 2: Scaffold the project**

Run from `/Users/hyeonjoo/VSCodeTestProjects/sorigami`:
```bash
flutter create --org com.fixli --project-name sorigami --platforms=android,ios .
```
Expected: `lib/`, `android/`, `ios/`, `pubspec.yaml` created alongside the existing `docs/`.

- [ ] **Step 3: Add dependencies**

Run:
```bash
flutter pub add flutter_riverpod go_router drift sqlite3_flutter_libs \
  firebase_core firebase_auth google_sign_in googleapis googleapis_auth \
  extension_google_sign_in_as_googleapis_auth record dio \
  flutter_secure_storage workmanager path_provider path uuid intl
flutter pub add dev:drift_dev dev:build_runner dev:mocktail
```
Expected: `pubspec.yaml` lists all packages; `flutter pub get` succeeds.

- [ ] **Step 4: Write `analysis_options.yaml`**

```yaml
include: package:flutter_lints/flutter.yaml
analyzer:
  exclude:
    - "**/*.g.dart"
linter:
  rules:
    prefer_const_constructors: true
    require_trailing_commas: true
```

- [ ] **Step 5: Write `lib/app.dart`**

```dart
import 'package:flutter/material.dart';

class SorigamiApp extends StatelessWidget {
  const SorigamiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sorigami',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
      home: const Scaffold(body: Center(child: Text('Sorigami'))),
    );
  }
}
```

- [ ] **Step 6: Write `lib/main.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';

void main() {
  runApp(const ProviderScope(child: SorigamiApp()));
}
```

- [ ] **Step 7: Run the app to verify it boots**

Run: `flutter run -d <device>` (or `flutter test` smoke once tests exist)
Expected: app shows "Sorigami" centered. Stop the app.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: scaffold Sorigami Flutter app with dependencies"
```

---

## Task 2: Core enums

**Files:**
- Create: `lib/core/enums.dart`
- Test: `test/core/enums_test.dart`

**Interfaces:**
- Produces: `UploadStatus { none, queued, uploading, done, failed }`, `JobStatus { none, requested, processing, completed, failed }`, `OutputType { summary, tasks, both, custom }`, `Tone { formal, casual, concise }`. Each has `.name` (built-in) for DB storage and a static `fromName(String)`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/core/enums.dart';

void main() {
  test('JobStatus round-trips through name', () {
    for (final s in JobStatus.values) {
      expect(JobStatus.fromName(s.name), s);
    }
  });
  test('OutputType.fromName falls back to summary on unknown', () {
    expect(OutputType.fromName('bogus'), OutputType.summary);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/core/enums_test.dart`
Expected: FAIL — `enums.dart` not found.

- [ ] **Step 3: Write `lib/core/enums.dart`**

```dart
enum UploadStatus { none, queued, uploading, done, failed;
  static UploadStatus fromName(String n) =>
      UploadStatus.values.firstWhere((e) => e.name == n, orElse: () => UploadStatus.none);
}

enum JobStatus { none, requested, processing, completed, failed;
  static JobStatus fromName(String n) =>
      JobStatus.values.firstWhere((e) => e.name == n, orElse: () => JobStatus.none);
}

enum OutputType { summary, tasks, both, custom;
  static OutputType fromName(String n) =>
      OutputType.values.firstWhere((e) => e.name == n, orElse: () => OutputType.summary);
}

enum Tone { formal, casual, concise;
  static Tone fromName(String n) =>
      Tone.values.firstWhere((e) => e.name == n, orElse: () => Tone.concise);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/core/enums_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/core/enums.dart test/core/enums_test.dart
git commit -m "feat: add core status/output enums with name round-trip"
```

---

## Task 3: Drift database — tables + schema

**Files:**
- Create: `lib/data/db/database.dart`
- Test: `test/data/db/database_test.dart`

**Interfaces:**
- Produces: `AppDatabase(QueryExecutor)` with tables `Recordings`, `RecordingResults`, `Skills`, `Modes`, `ModeSkills`, `UserSettingsTable`. `List<String>` columns and `Map` columns stored as TEXT (JSON) via type converters. `schemaVersion => 1`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() => db.close());

  test('can insert and read a recording', () async {
    final id = 'rec-1';
    await db.into(db.recordings).insert(RecordingsCompanion.insert(
          id: id, title: 'Standup', language: 'auto',
          audioFilePath: '/tmp/a.m4a', createdAt: DateTime(2026), updatedAt: DateTime(2026),
        ));
    final row = await (db.select(db.recordings)..where((t) => t.id.equals(id))).getSingle();
    expect(row.title, 'Standup');
    expect(row.uploadStatus, 'none'); // default
  });

  test('tags list converter round-trips', () async {
    await db.into(db.recordings).insert(RecordingsCompanion.insert(
          id: 'r2', title: 't', language: 'auto', audioFilePath: '/x',
          createdAt: DateTime(2026), updatedAt: DateTime(2026),
          tags: const Value(['a', 'b']),
        ));
    final row = await (db.select(db.recordings)..where((t) => t.id.equals('r2'))).getSingle();
    expect(row.tags, ['a', 'b']);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/db/database_test.dart`
Expected: FAIL — `database.dart` / generated symbols missing.

- [ ] **Step 3: Write `lib/data/db/database.dart`**

```dart
import 'dart:convert';
import 'package:drift/drift.dart';

part 'database.g.dart';

class StringListConverter extends TypeConverter<List<String>, String> {
  const StringListConverter();
  @override
  List<String> fromSql(String fromDb) =>
      (jsonDecode(fromDb) as List).cast<String>();
  @override
  String toSql(List<String> value) => jsonEncode(value);
}

class JsonMapConverter extends TypeConverter<Map<String, dynamic>, String> {
  const JsonMapConverter();
  @override
  Map<String, dynamic> fromSql(String fromDb) =>
      (jsonDecode(fromDb) as Map).cast<String, dynamic>();
  @override
  String toSql(Map<String, dynamic> value) => jsonEncode(value);
}

class Recordings extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get memo => text().nullable()();
  TextColumn get tags => text().map(const StringListConverter()).withDefault(const Constant('[]'))();
  TextColumn get category => text().nullable()();
  TextColumn get language => text()();
  TextColumn get modeId => text().nullable()();
  TextColumn get customSkillIds => text().map(const StringListConverter()).nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  TextColumn get audioFilePath => text()();
  IntColumn get audioDurationMs => integer().nullable()();
  IntColumn get audioFileSize => integer().nullable()();
  TextColumn get uploadStatus => text().withDefault(const Constant('none'))();
  TextColumn get driveFileId => text().nullable()();
  TextColumn get jobId => text().nullable()();
  TextColumn get jobStatus => text().withDefault(const Constant('none'))();
  TextColumn get jobError => text().nullable()();
  @override
  Set<Column> get primaryKey => {id};
}

class RecordingResults extends Table {
  TextColumn get id => text()();
  TextColumn get recordingId => text()();
  TextColumn get transcript => text()();
  TextColumn get skillResults => text()(); // JSON array
  DateTimeColumn get receivedAt => dateTime()();
  @override
  Set<Column> get primaryKey => {id};
}

class Skills extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();
  TextColumn get language => text().withDefault(const Constant('auto'))();
  BoolColumn get identifySpeakers => boolean().withDefault(const Constant(false))();
  TextColumn get vocabularyHints => text().map(const StringListConverter()).withDefault(const Constant('[]'))();
  TextColumn get outputType => text().withDefault(const Constant('summary'))();
  TextColumn get focusArea => text().nullable()();
  TextColumn get tone => text().withDefault(const Constant('concise'))();
  TextColumn get outputLanguage => text().withDefault(const Constant('auto'))();
  TextColumn get additionalInstructions => text().nullable()();
  TextColumn get pipelineParams => text().map(const JsonMapConverter()).nullable()();
  DateTimeColumn get createdAt => dateTime()();
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

class ModeSkills extends Table {
  TextColumn get modeId => text()();
  TextColumn get skillId => text()();
  IntColumn get sortOrder => integer().withDefault(const Constant(0))();
  @override
  Set<Column> get primaryKey => {modeId, skillId};
}

class UserSettingsTable extends Table {
  TextColumn get userId => text()();
  TextColumn get activeModeId => text().nullable()();
  TextColumn get pipelineServerUrl => text().withDefault(const Constant(''))();
  TextColumn get defaultLanguage => text().withDefault(const Constant('auto'))();
  TextColumn get defaultCategory => text().nullable()();
  BoolColumn get driveConnected => boolean().withDefault(const Constant(false))();
  BoolColumn get notificationsEnabled => boolean().withDefault(const Constant(true))();
  @override
  Set<Column> get primaryKey => {userId};
}

@DriftDatabase(tables: [
  Recordings, RecordingResults, Skills, Modes, ModeSkills, UserSettingsTable,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);
  @override
  int get schemaVersion => 1;
}
```

- [ ] **Step 4: Generate Drift code**

Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: `lib/data/db/database.g.dart` created; no errors.

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/data/db/database_test.dart`
Expected: PASS (both tests).

- [ ] **Step 6: Commit**

```bash
git add lib/data/db/database.dart lib/data/db/database.g.dart test/data/db/database_test.dart
git commit -m "feat: add Drift schema for recordings, skills, modes, settings"
```

---

## Task 4: RecordingDao

**Files:**
- Create: `lib/data/db/daos/recording_dao.dart`
- Modify: `lib/data/db/database.dart` (add `RecordingDao` to `daos:` and re-generate)
- Test: `test/data/db/daos/recording_dao_test.dart`

**Interfaces:**
- Consumes: `AppDatabase` (Task 3).
- Produces: `RecordingDao` with `Future<void> upsert(RecordingsCompanion)`, `Stream<List<Recording>> watchAll()`, `Future<Recording?> byId(String)`, `Future<void> setJobStatus(String id, String status, {String? jobId, String? error})`, `Future<void> setUploadStatus(String id, String status, {String? driveFileId})`, `Future<void> saveResult(RecordingResultsCompanion)`, `Future<RecordingResult?> resultFor(String recordingId)`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() => db.close());

  RecordingsCompanion rec(String id) => RecordingsCompanion.insert(
        id: id, title: 'T', language: 'auto', audioFilePath: '/a',
        createdAt: DateTime(2026), updatedAt: DateTime(2026));

  test('upsert then byId returns row', () async {
    await db.recordingDao.upsert(rec('r1'));
    expect((await db.recordingDao.byId('r1'))!.title, 'T');
  });

  test('setJobStatus updates status and jobId', () async {
    await db.recordingDao.upsert(rec('r1'));
    await db.recordingDao.setJobStatus('r1', 'processing', jobId: 'job-9');
    final r = await db.recordingDao.byId('r1');
    expect(r!.jobStatus, 'processing');
    expect(r.jobId, 'job-9');
  });

  test('saveResult then resultFor returns transcript', () async {
    await db.recordingDao.upsert(rec('r1'));
    await db.recordingDao.saveResult(RecordingResultsCompanion.insert(
        id: 'res1', recordingId: 'r1', transcript: 'hello',
        skillResults: '[]', receivedAt: DateTime(2026)));
    expect((await db.recordingDao.resultFor('r1'))!.transcript, 'hello');
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/db/daos/recording_dao_test.dart`
Expected: FAIL — `recordingDao` not defined.

- [ ] **Step 3: Write `lib/data/db/daos/recording_dao.dart`**

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'recording_dao.g.dart';

@DriftAccessor(tables: [Recordings, RecordingResults])
class RecordingDao extends DatabaseAccessor<AppDatabase> with _$RecordingDaoMixin {
  RecordingDao(super.db);

  Future<void> upsert(RecordingsCompanion r) =>
      into(recordings).insertOnConflictUpdate(r);

  Stream<List<Recording>> watchAll() =>
      (select(recordings)..orderBy([(t) => OrderingTerm.desc(t.createdAt)])).watch();

  Future<Recording?> byId(String id) =>
      (select(recordings)..where((t) => t.id.equals(id))).getSingleOrNull();

  Future<void> setJobStatus(String id, String status, {String? jobId, String? error}) =>
      (update(recordings)..where((t) => t.id.equals(id))).write(RecordingsCompanion(
        jobStatus: Value(status),
        jobId: jobId == null ? const Value.absent() : Value(jobId),
        jobError: Value(error),
        updatedAt: Value(DateTime.now()),
      ));

  Future<void> setUploadStatus(String id, String status, {String? driveFileId}) =>
      (update(recordings)..where((t) => t.id.equals(id))).write(RecordingsCompanion(
        uploadStatus: Value(status),
        driveFileId: driveFileId == null ? const Value.absent() : Value(driveFileId),
        updatedAt: Value(DateTime.now()),
      ));

  Future<void> saveResult(RecordingResultsCompanion r) =>
      into(recordingResults).insertOnConflictUpdate(r);

  Future<RecordingResult?> resultFor(String recordingId) =>
      (select(recordingResults)..where((t) => t.recordingId.equals(recordingId)))
          .getSingleOrNull();
}
```

- [ ] **Step 4: Register the DAO and regenerate**

In `lib/data/db/database.dart`, change the annotation to:
```dart
@DriftDatabase(tables: [
  Recordings, RecordingResults, Skills, Modes, ModeSkills, UserSettingsTable,
], daos: [RecordingDao])
```
Add `import 'daos/recording_dao.dart';` at the top.
Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: `recording_dao.g.dart` generated; `db.recordingDao` available.

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/data/db/daos/recording_dao_test.dart`
Expected: PASS (all three).

- [ ] **Step 6: Commit**

```bash
git add lib/data/db/ test/data/db/daos/recording_dao_test.dart
git commit -m "feat: add RecordingDao with status updates and result storage"
```

---

## Task 5: SkillDao, ModeDao, SettingsDao

**Files:**
- Create: `lib/data/db/daos/skill_dao.dart`, `lib/data/db/daos/mode_dao.dart`, `lib/data/db/daos/settings_dao.dart`
- Modify: `lib/data/db/database.dart` (`daos:` list) + regenerate
- Test: `test/data/db/daos/skill_mode_settings_test.dart`

**Interfaces:**
- Produces:
  - `SkillDao`: `Future<void> upsert(SkillsCompanion)`, `Future<List<Skill>> all()`, `Future<Skill?> byId(String)`, `Future<void> delete(String id)`.
  - `ModeDao`: `Future<void> upsertMode(ModesCompanion)`, `Future<List<Mode>> allModes()`, `Future<void> setSkills(String modeId, List<String> skillIds)`, `Future<List<String>> skillIdsFor(String modeId)`, `Future<Mode?> defaultMode()`, `Future<void> setDefault(String modeId)`.
  - `SettingsDao`: `Future<UserSettingsTableData> ensure(String userId)`, `Future<void> update(UserSettingsTableCompanion)`, `Stream<UserSettingsTableData?> watch(String userId)`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() => db.close());

  SkillsCompanion skill(String id) =>
      SkillsCompanion.insert(id: id, name: 'S$id', createdAt: DateTime(2026));

  test('mode setSkills then skillIdsFor preserves order', () async {
    await db.skillDao.upsert(skill('a'));
    await db.skillDao.upsert(skill('b'));
    await db.modeDao.upsertMode(ModesCompanion.insert(
        id: 'm1', name: 'Team', icon: '🗓', createdAt: DateTime(2026)));
    await db.modeDao.setSkills('m1', ['b', 'a']);
    expect(await db.modeDao.skillIdsFor('m1'), ['b', 'a']);
  });

  test('setDefault makes exactly one default', () async {
    await db.modeDao.upsertMode(ModesCompanion.insert(
        id: 'm1', name: 'A', icon: 'x', createdAt: DateTime(2026)));
    await db.modeDao.upsertMode(ModesCompanion.insert(
        id: 'm2', name: 'B', icon: 'y', createdAt: DateTime(2026)));
    await db.modeDao.setDefault('m1');
    await db.modeDao.setDefault('m2');
    expect((await db.modeDao.defaultMode())!.id, 'm2');
  });

  test('settings ensure creates a row once', () async {
    final s = await db.settingsDao.ensure('u1');
    expect(s.userId, 'u1');
    await db.settingsDao.update(UserSettingsTableCompanion(
        userId: const Value('u1'), pipelineServerUrl: const Value('http://x')));
    final again = await db.settingsDao.ensure('u1');
    expect(again.pipelineServerUrl, 'http://x');
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/db/daos/skill_mode_settings_test.dart`
Expected: FAIL — DAOs not defined.

- [ ] **Step 3: Write `lib/data/db/daos/skill_dao.dart`**

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'skill_dao.g.dart';

@DriftAccessor(tables: [Skills])
class SkillDao extends DatabaseAccessor<AppDatabase> with _$SkillDaoMixin {
  SkillDao(super.db);
  Future<void> upsert(SkillsCompanion s) => into(skills).insertOnConflictUpdate(s);
  Future<List<Skill>> all() => select(skills).get();
  Future<Skill?> byId(String id) =>
      (select(skills)..where((t) => t.id.equals(id))).getSingleOrNull();
  Future<void> delete(String id) =>
      (delete(skills)..where((t) => t.id.equals(id))).go();
}
```

- [ ] **Step 4: Write `lib/data/db/daos/mode_dao.dart`**

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'mode_dao.g.dart';

@DriftAccessor(tables: [Modes, ModeSkills])
class ModeDao extends DatabaseAccessor<AppDatabase> with _$ModeDaoMixin {
  ModeDao(super.db);

  Future<void> upsertMode(ModesCompanion m) => into(modes).insertOnConflictUpdate(m);
  Future<List<Mode>> allModes() =>
      (select(modes)..orderBy([(t) => OrderingTerm.desc(t.isSeeded)])).get();

  Future<void> setSkills(String modeId, List<String> skillIds) async {
    await (delete(modeSkills)..where((t) => t.modeId.equals(modeId))).go();
    for (var i = 0; i < skillIds.length; i++) {
      await into(modeSkills).insert(ModeSkillsCompanion.insert(
          modeId: modeId, skillId: skillIds[i], sortOrder: Value(i)));
    }
  }

  Future<List<String>> skillIdsFor(String modeId) async {
    final rows = await (select(modeSkills)
          ..where((t) => t.modeId.equals(modeId))
          ..orderBy([(t) => OrderingTerm.asc(t.sortOrder)]))
        .get();
    return rows.map((r) => r.skillId).toList();
  }

  Future<Mode?> defaultMode() =>
      (select(modes)..where((t) => t.isDefault.equals(true))).getSingleOrNull();

  Future<void> setDefault(String modeId) async {
    await update(modes).write(const ModesCompanion(isDefault: Value(false)));
    await (update(modes)..where((t) => t.id.equals(modeId)))
        .write(const ModesCompanion(isDefault: Value(true)));
  }
}
```

- [ ] **Step 5: Write `lib/data/db/daos/settings_dao.dart`**

```dart
import 'package:drift/drift.dart';
import '../database.dart';

part 'settings_dao.g.dart';

@DriftAccessor(tables: [UserSettingsTable])
class SettingsDao extends DatabaseAccessor<AppDatabase> with _$SettingsDaoMixin {
  SettingsDao(super.db);

  Future<UserSettingsTableData> ensure(String userId) async {
    final existing = await (select(userSettingsTable)
          ..where((t) => t.userId.equals(userId)))
        .getSingleOrNull();
    if (existing != null) return existing;
    await into(userSettingsTable).insert(UserSettingsTableCompanion.insert(userId: userId));
    return (select(userSettingsTable)..where((t) => t.userId.equals(userId))).getSingle();
  }

  Future<void> update(UserSettingsTableCompanion c) =>
      (this.update(userSettingsTable)..where((t) => t.userId.equals(c.userId.value)))
          .write(c);

  Stream<UserSettingsTableData?> watch(String userId) =>
      (select(userSettingsTable)..where((t) => t.userId.equals(userId))).watchSingleOrNull();
}
```

- [ ] **Step 6: Register DAOs and regenerate**

In `database.dart`, set `daos: [RecordingDao, SkillDao, ModeDao, SettingsDao]` and add the three imports.
Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: `.g.dart` files for each DAO generated.

- [ ] **Step 7: Run test to verify it passes**

Run: `flutter test test/data/db/daos/skill_mode_settings_test.dart`
Expected: PASS (all three).

- [ ] **Step 8: Commit**

```bash
git add lib/data/db/ test/data/db/daos/skill_mode_settings_test.dart
git commit -m "feat: add Skill, Mode, and Settings DAOs"
```

---

## Task 6: Seed data (Modes + Skills on first run)

**Files:**
- Create: `lib/data/seed/seed_data.dart`
- Test: `test/data/seed/seed_data_test.dart`

**Interfaces:**
- Consumes: `SkillDao`, `ModeDao` (Task 5).
- Produces: `Future<void> seedIfEmpty(AppDatabase db)` — idempotent; inserts the 5 seed Modes and their Skills only when `modes` is empty. After running, exactly one Mode (`General`) has `isDefault = true`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() => db.close());

  test('seeds 5 modes with General default, idempotent', () async {
    await seedIfEmpty(db);
    await seedIfEmpty(db); // second call must not duplicate
    final modes = await db.modeDao.allModes();
    expect(modes.length, 5);
    expect((await db.modeDao.defaultMode())!.name, 'General');
  });

  test('General mode has at least one skill', () async {
    await seedIfEmpty(db);
    final general = (await db.modeDao.allModes()).firstWhere((m) => m.name == 'General');
    expect((await db.modeDao.skillIdsFor(general.id)).isNotEmpty, true);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/seed/seed_data_test.dart`
Expected: FAIL — `seedIfEmpty` not defined.

- [ ] **Step 3: Write `lib/data/seed/seed_data.dart`**

```dart
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';
import '../db/database.dart';

const _uuid = Uuid();

Future<void> seedIfEmpty(AppDatabase db) async {
  if ((await db.modeDao.allModes()).isNotEmpty) return;
  final now = DateTime.now();

  Future<String> skill(String name, {
    String outputType = 'summary',
    String? focusArea,
    bool identifySpeakers = false,
  }) async {
    final id = _uuid.v4();
    await db.skillDao.upsert(SkillsCompanion.insert(
      id: id, name: name, createdAt: now,
      outputType: Value(outputType),
      focusArea: Value(focusArea),
      identifySpeakers: Value(identifySpeakers),
    ));
    return id;
  }

  Future<void> mode(String name, String icon, List<String> skillIds,
      {bool isDefault = false}) async {
    final id = _uuid.v4();
    await db.modeDao.upsertMode(ModesCompanion.insert(
      id: id, name: name, icon: icon, createdAt: now,
      isSeeded: const Value(true), isDefault: Value(isDefault),
    ));
    await db.modeDao.setSkills(id, skillIds);
  }

  final summary = await skill('Summary');
  final actions = await skill('Action Items', outputType: 'tasks', identifySpeakers: true);
  final meetingSummary = await skill('Meeting Summary');
  final decisions = await skill('Decision Log', outputType: 'custom', focusArea: 'decisions made');
  final callSummary = await skill('Call Summary');
  final followups = await skill('Follow-ups', outputType: 'tasks', focusArea: 'commitments & next steps');
  final standupDigest = await skill('Standup Digest');
  final blockers = await skill('Blockers', outputType: 'custom', focusArea: 'blockers');
  final interviewSummary = await skill('Interview Summary', identifySpeakers: true);
  final keyQuotes = await skill('Key Quotes', outputType: 'custom', focusArea: 'notable quotes');

  await mode('General', '📝', [summary, actions], isDefault: true);
  await mode('Team Meeting', '🗓', [meetingSummary, actions, decisions]);
  await mode('Sales Call', '📞', [callSummary, followups]);
  await mode('Standup', '⚡', [standupDigest, blockers]);
  await mode('Interview', '🎙', [interviewSummary, keyQuotes]);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/seed/seed_data_test.dart`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add lib/data/seed/seed_data.dart test/data/seed/seed_data_test.dart
git commit -m "feat: seed 5 modes and their skills on first run"
```

---

## Task 7: Pipeline client contract + DTOs

**Files:**
- Create: `lib/data/pipeline/pipeline_client.dart`
- Test: `test/data/pipeline/pipeline_client_test.dart`

**Interfaces:**
- Produces:
  - `class SkillRequest` with fields matching spec §10 (`skillId`, `skillName`, `language`, `identifySpeakers`, `vocabularyHints`, `outputType`, `focusArea`, `tone`, `outputLanguage`, `additionalInstructions`, `pipelineParams`) + `Map<String, dynamic> toJson()`.
  - `class JobSubmission { String recordingId; String audioFilePath; int audioDurationS; String? category; String? modeName; List<SkillRequest> skills; }`
  - `enum PipelineJobStatus { requested, processing, completed, failed }` with `fromName`.
  - `class JobStatusResult { String jobId; PipelineJobStatus status; String? stage; String? error; }`
  - `class SkillOutput { String skillId; String skillName; String output; }`
  - `class PipelineResult { String transcript; List<SkillOutput> skillResults; }`
  - `abstract class PipelineClient { Future<bool> health(); Future<String> submit(JobSubmission s); Future<JobStatusResult> status(String jobId); Future<PipelineResult> result(String jobId); }`

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/pipeline/pipeline_client.dart';

void main() {
  test('SkillRequest.toJson includes pipeline_params passthrough', () {
    final r = SkillRequest(
      skillId: 's1', skillName: 'Action Items', language: 'auto',
      identifySpeakers: true, vocabularyHints: ['Fixli'],
      outputType: 'tasks', focusArea: null, tone: 'concise',
      outputLanguage: 'en', additionalInstructions: null,
      pipelineParams: {'num_speakers': 2},
    );
    final j = r.toJson();
    expect(j['identify_speakers'], true);
    expect(j['vocabulary_hints'], ['Fixli']);
    expect(j['pipeline_params'], {'num_speakers': 2});
  });

  test('PipelineJobStatus.fromName parses', () {
    expect(PipelineJobStatus.fromName('completed'), PipelineJobStatus.completed);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/pipeline/pipeline_client_test.dart`
Expected: FAIL — symbols missing.

- [ ] **Step 3: Write `lib/data/pipeline/pipeline_client.dart`**

```dart
class SkillRequest {
  final String skillId;
  final String skillName;
  final String language;
  final bool identifySpeakers;
  final List<String> vocabularyHints;
  final String outputType;
  final String? focusArea;
  final String tone;
  final String outputLanguage;
  final String? additionalInstructions;
  final Map<String, dynamic>? pipelineParams;

  SkillRequest({
    required this.skillId,
    required this.skillName,
    required this.language,
    required this.identifySpeakers,
    required this.vocabularyHints,
    required this.outputType,
    required this.focusArea,
    required this.tone,
    required this.outputLanguage,
    required this.additionalInstructions,
    required this.pipelineParams,
  });

  Map<String, dynamic> toJson() => {
        'skill_id': skillId,
        'skill_name': skillName,
        'language': language,
        'identify_speakers': identifySpeakers,
        'vocabulary_hints': vocabularyHints,
        'output_type': outputType,
        'focus_area': focusArea,
        'tone': tone,
        'output_language': outputLanguage,
        'additional_instructions': additionalInstructions,
        if (pipelineParams != null) 'pipeline_params': pipelineParams,
      };
}

class JobSubmission {
  final String recordingId;
  final String audioFilePath;
  final int audioDurationS;
  final String? category;
  final String? modeName;
  final List<SkillRequest> skills;
  JobSubmission({
    required this.recordingId,
    required this.audioFilePath,
    required this.audioDurationS,
    required this.category,
    required this.modeName,
    required this.skills,
  });
}

enum PipelineJobStatus {
  requested, processing, completed, failed;
  static PipelineJobStatus fromName(String n) => PipelineJobStatus.values
      .firstWhere((e) => e.name == n, orElse: () => PipelineJobStatus.requested);
}

class JobStatusResult {
  final String jobId;
  final PipelineJobStatus status;
  final String? stage;
  final String? error;
  JobStatusResult({required this.jobId, required this.status, this.stage, this.error});
}

class SkillOutput {
  final String skillId;
  final String skillName;
  final String output;
  SkillOutput({required this.skillId, required this.skillName, required this.output});
}

class PipelineResult {
  final String transcript;
  final List<SkillOutput> skillResults;
  PipelineResult({required this.transcript, required this.skillResults});
}

abstract class PipelineClient {
  Future<bool> health();
  Future<String> submit(JobSubmission submission);
  Future<JobStatusResult> status(String jobId);
  Future<PipelineResult> result(String jobId);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/pipeline/pipeline_client_test.dart`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add lib/data/pipeline/pipeline_client.dart test/data/pipeline/pipeline_client_test.dart
git commit -m "feat: define PipelineClient contract and DTOs"
```

---

## Task 8: MockPipelineClient

**Files:**
- Create: `lib/data/pipeline/mock_pipeline_client.dart`
- Test: `test/data/pipeline/mock_pipeline_client_test.dart`

**Interfaces:**
- Consumes: `PipelineClient`, `JobSubmission`, `JobStatusResult`, `PipelineResult` (Task 7).
- Produces: `MockPipelineClient implements PipelineClient`. Constructor takes optional `Duration processingTime` (default 3s) and `bool healthy` (default true). `health()` returns `healthy`. `submit()` returns a generated job id and records submission time. `status()` returns `processing` until `processingTime` elapsed, then `completed`. `result()` returns a canned speaker-attributed transcript and one `SkillOutput` per submitted skill (echoing the skill name into the output).

- [ ] **Step 1: Write the failing test**

```dart
import 'package:fake_async/fake_async.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/pipeline/mock_pipeline_client.dart';
import 'package:sorigami/data/pipeline/pipeline_client.dart';

JobSubmission sub() => JobSubmission(
      recordingId: 'r1', audioFilePath: '/a.m4a', audioDurationS: 60,
      category: null, modeName: 'General',
      skills: [
        SkillRequest(skillId: 's1', skillName: 'Action Items', language: 'auto',
            identifySpeakers: true, vocabularyHints: const [], outputType: 'tasks',
            focusArea: null, tone: 'concise', outputLanguage: 'en',
            additionalInstructions: null, pipelineParams: null),
      ]);

void main() {
  test('health reflects flag', () async {
    expect(await MockPipelineClient(healthy: false).health(), false);
  });

  test('status flips processing → completed after processingTime', () {
    fakeAsync((async) {
      final c = MockPipelineClient(processingTime: const Duration(seconds: 3));
      late String jobId;
      c.submit(sub()).then((id) => jobId = id);
      async.flushMicrotasks();
      c.status(jobId).then((s) => expect(s.status, PipelineJobStatus.processing));
      async.elapse(const Duration(seconds: 4));
      c.status(jobId).then((s) => expect(s.status, PipelineJobStatus.completed));
      async.flushMicrotasks();
    });
  });

  test('result returns one output per submitted skill', () async {
    final c = MockPipelineClient(processingTime: Duration.zero);
    final id = await c.submit(sub());
    final r = await c.result(id);
    expect(r.transcript.contains('speaker_a'), true);
    expect(r.skillResults.length, 1);
    expect(r.skillResults.first.skillName, 'Action Items');
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/pipeline/mock_pipeline_client_test.dart`
Expected: FAIL — `MockPipelineClient` not defined. (Add `flutter pub add dev:fake_async` if missing, then re-run.)

- [ ] **Step 3: Write `lib/data/pipeline/mock_pipeline_client.dart`**

```dart
import 'package:uuid/uuid.dart';
import 'pipeline_client.dart';

class MockPipelineClient implements PipelineClient {
  MockPipelineClient({
    this.processingTime = const Duration(seconds: 3),
    this.healthy = true,
  });

  final Duration processingTime;
  final bool healthy;
  final _uuid = const Uuid();
  final Map<String, DateTime> _submittedAt = {};
  final Map<String, JobSubmission> _submissions = {};

  @override
  Future<bool> health() async => healthy;

  @override
  Future<String> submit(JobSubmission submission) async {
    final id = _uuid.v4();
    _submittedAt[id] = DateTime.now();
    _submissions[id] = submission;
    return id;
  }

  @override
  Future<JobStatusResult> status(String jobId) async {
    final start = _submittedAt[jobId];
    if (start == null) {
      return JobStatusResult(jobId: jobId, status: PipelineJobStatus.failed, error: 'unknown job');
    }
    final done = DateTime.now().difference(start) >= processingTime;
    return JobStatusResult(
      jobId: jobId,
      status: done ? PipelineJobStatus.completed : PipelineJobStatus.processing,
      stage: done ? null : 'summarizing',
    );
  }

  @override
  Future<PipelineResult> result(String jobId) async {
    final submission = _submissions[jobId];
    final skills = submission?.skills ?? const [];
    return PipelineResult(
      transcript: 'speaker_a: Welcome everyone.\n'
          'speaker_b: Thanks, let\'s get started.\n'
          'speaker_a: First item on the agenda...',
      skillResults: [
        for (final s in skills)
          SkillOutput(
            skillId: s.skillId,
            skillName: s.skillName,
            output: '[mock ${s.skillName}] Example ${s.outputType} output '
                'generated from the transcript.',
          ),
      ],
    );
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/pipeline/mock_pipeline_client_test.dart`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add lib/data/pipeline/mock_pipeline_client.dart test/data/pipeline/mock_pipeline_client_test.dart pubspec.yaml
git commit -m "feat: add MockPipelineClient for Milestone 1"
```

---

## Task 9: Skill resolution (mode → skills → SkillRequest list)

**Files:**
- Create: `lib/domain/models/skill_resolution.dart`
- Test: `test/domain/skill_resolution_test.dart`

**Interfaces:**
- Consumes: `Recording`, `Skill` (Drift row types), `ModeDao`, `SkillDao`, `SkillRequest` (Task 7).
- Produces: `Future<List<SkillRequest>> resolveSkills(Recording rec, {required ModeDao modeDao, required SkillDao skillDao})` implementing spec §8 resolution order: customSkillIds → mode skills → default mode skills → empty. Maps each `Skill` row to a `SkillRequest`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';
import 'package:sorigami/domain/models/skill_resolution.dart';

void main() {
  late AppDatabase db;
  setUp(() async {
    db = AppDatabase(NativeDatabase.memory());
    await seedIfEmpty(db);
  });
  tearDown(() => db.close());

  Future<Recording> recWith({String? modeId, List<String>? custom}) async {
    await db.recordingDao.upsert(RecordingsCompanion.insert(
      id: 'r1', title: 'T', language: 'auto', audioFilePath: '/a',
      createdAt: DateTime(2026), updatedAt: DateTime(2026),
      modeId: Value(modeId), customSkillIds: Value(custom),
    ));
    return (await db.recordingDao.byId('r1'))!;
  }

  test('falls back to default mode when modeId null', () async {
    final rec = await recWith();
    final reqs = await resolveSkills(rec, modeDao: db.modeDao, skillDao: db.skillDao);
    expect(reqs.isNotEmpty, true); // General's skills
  });

  test('custom skill ids win', () async {
    final all = await db.skillDao.all();
    final rec = await recWith(custom: [all.first.id]);
    final reqs = await resolveSkills(rec, modeDao: db.modeDao, skillDao: db.skillDao);
    expect(reqs.length, 1);
    expect(reqs.first.skillId, all.first.id);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/domain/skill_resolution_test.dart`
Expected: FAIL — `resolveSkills` not defined.

- [ ] **Step 3: Write `lib/domain/models/skill_resolution.dart`**

```dart
import '../../data/db/database.dart';
import '../../data/db/daos/mode_dao.dart';
import '../../data/db/daos/skill_dao.dart';
import '../../data/pipeline/pipeline_client.dart';

SkillRequest _toRequest(Skill s) => SkillRequest(
      skillId: s.id,
      skillName: s.name,
      language: s.language,
      identifySpeakers: s.identifySpeakers,
      vocabularyHints: s.vocabularyHints,
      outputType: s.outputType,
      focusArea: s.focusArea,
      tone: s.tone,
      outputLanguage: s.outputLanguage,
      additionalInstructions: s.additionalInstructions,
      pipelineParams: s.pipelineParams,
    );

Future<List<SkillRequest>> resolveSkills(
  Recording rec, {
  required ModeDao modeDao,
  required SkillDao skillDao,
}) async {
  List<String> ids;
  if (rec.customSkillIds != null && rec.customSkillIds!.isNotEmpty) {
    ids = rec.customSkillIds!;
  } else if (rec.modeId != null) {
    ids = await modeDao.skillIdsFor(rec.modeId!);
  } else {
    final def = await modeDao.defaultMode();
    ids = def == null ? [] : await modeDao.skillIdsFor(def.id);
  }
  final out = <SkillRequest>[];
  for (final id in ids) {
    final s = await skillDao.byId(id);
    if (s != null) out.add(_toRequest(s));
  }
  return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/domain/skill_resolution_test.dart`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add lib/domain/models/skill_resolution.dart test/domain/skill_resolution_test.dart
git commit -m "feat: resolve skills for a recording per contract order"
```

---

## Task 10: Riverpod providers (database, daos, pipeline, settings)

**Files:**
- Create: `lib/providers/providers.dart`
- Test: `test/providers/providers_test.dart`

**Interfaces:**
- Consumes: `AppDatabase`, DAOs, `MockPipelineClient`, `PipelineClient`.
- Produces:
  - `databaseProvider` (override in tests/main with a concrete `AppDatabase`).
  - `recordingDaoProvider`, `skillDaoProvider`, `modeDaoProvider`, `settingsDaoProvider` derived from `databaseProvider`.
  - `pipelineClientProvider` returning `MockPipelineClient()` (overridden in M2).
  - `currentUserIdProvider` (`StateProvider<String?>`).

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/pipeline/pipeline_client.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  test('daos and pipeline client resolve from container', () {
    final db = AppDatabase(NativeDatabase.memory());
    final c = ProviderContainer(overrides: [databaseProvider.overrideWithValue(db)]);
    addTearDown(c.dispose);
    expect(c.read(recordingDaoProvider), isNotNull);
    expect(c.read(pipelineClientProvider), isA<PipelineClient>());
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/providers/providers_test.dart`
Expected: FAIL — providers not defined.

- [ ] **Step 3: Write `lib/providers/providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import '../data/db/daos/recording_dao.dart';
import '../data/db/daos/skill_dao.dart';
import '../data/db/daos/mode_dao.dart';
import '../data/db/daos/settings_dao.dart';
import '../data/pipeline/pipeline_client.dart';
import '../data/pipeline/mock_pipeline_client.dart';

final databaseProvider = Provider<AppDatabase>((ref) {
  throw UnimplementedError('databaseProvider must be overridden in main()');
});

final recordingDaoProvider = Provider<RecordingDao>((ref) => ref.watch(databaseProvider).recordingDao);
final skillDaoProvider = Provider<SkillDao>((ref) => ref.watch(databaseProvider).skillDao);
final modeDaoProvider = Provider<ModeDao>((ref) => ref.watch(databaseProvider).modeDao);
final settingsDaoProvider = Provider<SettingsDao>((ref) => ref.watch(databaseProvider).settingsDao);

final pipelineClientProvider = Provider<PipelineClient>((ref) => MockPipelineClient());

final currentUserIdProvider = StateProvider<String?>((ref) => null);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/providers/providers_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/providers/providers.dart test/providers/providers_test.dart
git commit -m "feat: wire Riverpod providers for db, daos, pipeline"
```

---

## Task 11: Wire database into main + first-run seed

**Files:**
- Modify: `lib/main.dart`, `lib/data/db/database.dart` (add native open helper)
- Create: `lib/data/db/open_connection.dart`
- Test: `test/data/db/open_connection_test.dart`

**Interfaces:**
- Produces: `LazyDatabase openConnection()` opening a file `sorigami.sqlite` under the app documents dir. `main()` constructs `AppDatabase(openConnection())`, runs `seedIfEmpty`, and overrides `databaseProvider`.

- [ ] **Step 1: Write the failing test (helper exists and returns an executor)**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/open_connection.dart';

void main() {
  test('openConnection returns a non-null executor', () {
    TestWidgetsFlutterBinding.ensureInitialized();
    expect(openConnection(), isNotNull);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/db/open_connection_test.dart`
Expected: FAIL — `openConnection` not defined.

- [ ] **Step 3: Write `lib/data/db/open_connection.dart`**

```dart
import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

LazyDatabase openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'sorigami.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/db/open_connection_test.dart`
Expected: PASS.

- [ ] **Step 5: Update `lib/main.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'data/db/database.dart';
import 'data/db/open_connection.dart';
import 'data/seed/seed_data.dart';
import 'providers/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final db = AppDatabase(openConnection());
  await seedIfEmpty(db);
  runApp(ProviderScope(
    overrides: [databaseProvider.overrideWithValue(db)],
    child: const SorigamiApp(),
  ));
}
```

- [ ] **Step 6: Run app to confirm boot**

Run: `flutter run -d <device>`
Expected: app launches without DB errors; stop the app.

- [ ] **Step 7: Commit**

```bash
git add lib/data/db/open_connection.dart lib/main.dart test/data/db/open_connection_test.dart
git commit -m "feat: open native sqlite db and seed on first run"
```

---

## Task 12: Firebase Auth setup + AuthService

**Files:**
- Create: `lib/data/auth/auth_service.dart`
- Modify: `lib/main.dart` (Firebase.initializeApp), `android/`, `ios/` (Firebase config files)
- Test: `test/data/auth/auth_service_test.dart`

**Interfaces:**
- Produces: `class AuthService { Stream<String?> uidChanges(); Future<String?> signInWithGoogle(); Future<void> signOut(); }` wrapping `FirebaseAuth` + `GoogleSignIn`. Constructor accepts injected `FirebaseAuth` and `GoogleSignIn` for testing.

- [ ] **Step 1: Configure Firebase project**

Run: `dart pub global activate flutterfire_cli && flutterfire configure`
Select/create a Firebase project, enable Android + iOS apps. This writes `lib/firebase_options.dart`, `android/app/google-services.json`, `ios/Runner/GoogleService-Info.plist`. In the Firebase console, enable **Authentication → Google** sign-in.
Expected: `lib/firebase_options.dart` exists.

- [ ] **Step 2: Write the failing test (with mocktail)**

```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sorigami/data/auth/auth_service.dart';

class _MockAuth extends Mock implements FirebaseAuth {}
class _MockUser extends Mock implements User {}

void main() {
  test('uidChanges maps User stream to uid', () async {
    final auth = _MockAuth();
    final user = _MockUser();
    when(() => user.uid).thenReturn('u1');
    when(() => auth.authStateChanges()).thenAnswer((_) => Stream.value(user));
    final svc = AuthService(auth: auth);
    expect(await svc.uidChanges().first, 'u1');
  });
}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `flutter test test/data/auth/auth_service_test.dart`
Expected: FAIL — `AuthService` not defined.

- [ ] **Step 4: Write `lib/data/auth/auth_service.dart`**

```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AuthService {
  AuthService({FirebaseAuth? auth, GoogleSignIn? googleSignIn})
      : _auth = auth ?? FirebaseAuth.instance,
        _google = googleSignIn ?? GoogleSignIn(scopes: const ['email']);

  final FirebaseAuth _auth;
  final GoogleSignIn _google;

  Stream<String?> uidChanges() => _auth.authStateChanges().map((u) => u?.uid);

  Future<String?> signInWithGoogle() async {
    final account = await _google.signIn();
    if (account == null) return null; // user cancelled
    final auth = await account.authentication;
    final cred = GoogleAuthProvider.credential(
      accessToken: auth.accessToken,
      idToken: auth.idToken,
    );
    final result = await _auth.signInWithCredential(cred);
    return result.user?.uid;
  }

  Future<void> signOut() async {
    await _google.signOut();
    await _auth.signOut();
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/data/auth/auth_service_test.dart`
Expected: PASS.

- [ ] **Step 6: Initialize Firebase in `main.dart`**

Add near the top of `main()` after `ensureInitialized()`:
```dart
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
// ...
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
```
Add `authServiceProvider` to `lib/providers/providers.dart`:
```dart
import '../data/auth/auth_service.dart';
final authServiceProvider = Provider<AuthService>((ref) => AuthService());
```

- [ ] **Step 7: Commit**

```bash
git add lib/data/auth/ lib/providers/providers.dart lib/main.dart lib/firebase_options.dart \
  android/app/google-services.json ios/Runner/GoogleService-Info.plist test/data/auth/
git commit -m "feat: add Firebase Auth with Google sign-in"
```

---

## Task 13: Router + auth gate + app shell

**Files:**
- Create: `lib/core/router.dart`
- Modify: `lib/app.dart`
- Test: `test/core/router_test.dart`

**Interfaces:**
- Consumes: `authServiceProvider`, `currentUserIdProvider`.
- Produces: `GoRouter buildRouter(Ref ref)` with routes `/signin`, `/onboarding`, `/` (recordings), `/recording/:id`, `/settings`, plus settings sub-routes. Redirects to `/signin` when `currentUserIdProvider` is null. A `MainShell` widget hosts bottom navigation (Recordings | Settings).

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/app.dart';
import 'package:sorigami/providers/providers.dart';
import 'helpers/test_db.dart'; // see Task 13 step 3

void main() {
  testWidgets('unauthenticated user lands on sign-in', (tester) async {
    final db = makeTestDb();
    await tester.pumpWidget(ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const SorigamiApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Sign in with Google'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Create the test DB helper**

Create `test/core/helpers/test_db.dart`:
```dart
import 'package:drift/native.dart';
import 'package:sorigami/data/db/database.dart';

AppDatabase makeTestDb() => AppDatabase(NativeDatabase.memory());
```

- [ ] **Step 3: Run test to verify it fails**

Run: `flutter test test/core/router_test.dart`
Expected: FAIL — router/sign-in screen not wired.

- [ ] **Step 4: Write `lib/core/router.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/sign_in_screen.dart';
import '../features/recordings/recordings_screen.dart';
import '../features/detail/recording_detail_screen.dart';
import '../features/settings/settings_screen.dart';
import '../providers/providers.dart';

GoRouter buildRouter(Ref ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final loggedIn = ref.read(currentUserIdProvider) != null;
      final atSignIn = state.matchedLocation == '/signin';
      if (!loggedIn) return atSignIn ? null : '/signin';
      if (atSignIn) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/signin', builder: (_, __) => const SignInScreen()),
      GoRoute(path: '/', builder: (_, __) => const RecordingsScreen()),
      GoRoute(path: '/recording/:id',
          builder: (_, s) => RecordingDetailScreen(recordingId: s.pathParameters['id']!)),
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
    ],
  );
}

final routerProvider = Provider<GoRouter>((ref) => buildRouter(ref));
```

- [ ] **Step 5: Update `lib/app.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router.dart';
import 'providers/providers.dart';

class SorigamiApp extends ConsumerWidget {
  const SorigamiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Drive auth state into currentUserIdProvider.
    ref.listen(authServiceProvider, (_, __) {});
    final auth = ref.watch(authServiceProvider);
    ref.watch(_authSyncProvider);
    return MaterialApp.router(
      title: 'Sorigami',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
      routerConfig: ref.watch(routerProvider),
    );
  }
}

final _authSyncProvider = Provider<void>((ref) {
  final auth = ref.watch(authServiceProvider);
  final sub = auth.uidChanges().listen((uid) {
    ref.read(currentUserIdProvider.notifier).state = uid;
  });
  ref.onDispose(sub.cancel);
});
```

- [ ] **Step 6: Write a minimal `lib/features/auth/sign_in_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/providers.dart';

class SignInScreen extends ConsumerWidget {
  const SignInScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          onPressed: () => ref.read(authServiceProvider).signInWithGoogle(),
          child: const Text('Sign in with Google'),
        ),
      ),
    );
  }
}
```

- [ ] **Step 7: Add placeholder screens so the router compiles**

Create minimal `RecordingsScreen`, `RecordingDetailScreen`, `SettingsScreen` (each a `Scaffold` with a title). These are fully built in later tasks.
```dart
// lib/features/recordings/recordings_screen.dart
import 'package:flutter/material.dart';
class RecordingsScreen extends StatelessWidget {
  const RecordingsScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('Recordings')));
}
```
```dart
// lib/features/detail/recording_detail_screen.dart
import 'package:flutter/material.dart';
class RecordingDetailScreen extends StatelessWidget {
  const RecordingDetailScreen({super.key, required this.recordingId});
  final String recordingId;
  @override
  Widget build(BuildContext context) =>
      Scaffold(body: Center(child: Text('Detail $recordingId')));
}
```
```dart
// lib/features/settings/settings_screen.dart
import 'package:flutter/material.dart';
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('Settings')));
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `flutter test test/core/router_test.dart`
Expected: PASS — sign-in screen shown when logged out.

- [ ] **Step 9: Commit**

```bash
git add lib/core/router.dart lib/app.dart lib/features/ test/core/
git commit -m "feat: add router with auth gate and placeholder screens"
```

---

## Task 14: Onboarding + permissions screen

**Files:**
- Create: `lib/features/onboarding/permissions_screen.dart`
- Modify: `lib/core/router.dart` (add `/onboarding`), `lib/features/auth/sign_in_screen.dart` (route to onboarding on first sign-in)
- Test: `test/features/onboarding/permissions_screen_test.dart`

**Interfaces:**
- Consumes: `record`'s `AudioRecorder().hasPermission()`.
- Produces: `PermissionsScreen` with two buttons ("Allow microphone", "Continue") that request mic permission via the recorder and navigate to `/` when granted. A `permissionGateProvider` (FutureProvider) reporting whether mic permission is already granted.

- [ ] **Step 1: Write the failing widget test**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/features/onboarding/permissions_screen.dart';

void main() {
  testWidgets('shows microphone permission prompt', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PermissionsScreen()));
    expect(find.text('Allow microphone'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/onboarding/permissions_screen_test.dart`
Expected: FAIL — screen not defined.

- [ ] **Step 3: Write `lib/features/onboarding/permissions_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:record/record.dart';

class PermissionsScreen extends StatelessWidget {
  const PermissionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Welcome to Sorigami')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Sorigami needs your microphone to record conversations.'),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () async {
                final granted = await AudioRecorder().hasPermission();
                if (granted && context.mounted) context.go('/');
              },
              child: const Text('Allow microphone'),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 4: Add the route**

In `lib/core/router.dart` routes list:
```dart
GoRoute(path: '/onboarding', builder: (_, __) => const PermissionsScreen()),
```
Add `import '../features/onboarding/permissions_screen.dart';`.

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/onboarding/permissions_screen_test.dart`
Expected: PASS.

- [ ] **Step 6: Add platform permission declarations**

Android — in `android/app/src/main/AndroidManifest.xml` add inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
<uses-permission android:name="android.permission.INTERNET" />
```
iOS — in `ios/Runner/Info.plist` add:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>Sorigami records meetings to transcribe and summarize them.</string>
```

- [ ] **Step 7: Commit**

```bash
git add lib/features/onboarding/ lib/core/router.dart android/ ios/ test/features/onboarding/
git commit -m "feat: add permissions screen and platform mic declarations"
```

---

## Task 15: RecordingService (audio capture)

**Files:**
- Create: `lib/features/recordings/recording_service.dart`
- Test: `test/features/recordings/recording_service_test.dart`

**Interfaces:**
- Consumes: `record`'s `AudioRecorder`, `path_provider`.
- Produces: `class RecordingService { Future<String> start(); Future<void> pause(); Future<void> resume(); Future<RecordingFile> stop(); }` where `RecordingFile { String path; int durationMs; int fileSize; }`. Constructor takes injected `AudioRecorder` and a `Future<String> Function()` directory provider for testing. `start()` records AAC (`AudioEncoder.aacLc`) to a temp file; `stop()` moves it to a permanent path and returns metadata.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:record/record.dart';
import 'package:sorigami/features/recordings/recording_service.dart';

class _MockRecorder extends Mock implements AudioRecorder {}

void main() {
  setUpAll(() => registerFallbackValue(const RecordConfig()));

  test('start records to a path under temp dir', () async {
    final rec = _MockRecorder();
    when(() => rec.hasPermission()).thenAnswer((_) async => true);
    when(() => rec.start(any(), path: any(named: 'path'))).thenAnswer((_) async {});
    final svc = RecordingService(recorder: rec, tempDir: () async => '/tmp');
    final path = await svc.start();
    expect(path.startsWith('/tmp/'), true);
    expect(path.endsWith('.m4a'), true);
  });

  test('start throws when permission denied', () async {
    final rec = _MockRecorder();
    when(() => rec.hasPermission()).thenAnswer((_) async => false);
    final svc = RecordingService(recorder: rec, tempDir: () async => '/tmp');
    expect(svc.start(), throwsStateError);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/recordings/recording_service_test.dart`
Expected: FAIL — `RecordingService` not defined.

- [ ] **Step 3: Write `lib/features/recordings/recording_service.dart`**

```dart
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:record/record.dart';
import 'package:uuid/uuid.dart';

class RecordingFile {
  final String path;
  final int durationMs;
  final int fileSize;
  RecordingFile({required this.path, required this.durationMs, required this.fileSize});
}

class RecordingService {
  RecordingService({AudioRecorder? recorder, Future<String> Function()? tempDir})
      : _rec = recorder ?? AudioRecorder(),
        _tempDir = tempDir;

  final AudioRecorder _rec;
  final Future<String> Function()? _tempDir;
  final _uuid = const Uuid();
  DateTime? _startedAt;
  String? _path;

  Future<String> start() async {
    if (!await _rec.hasPermission()) {
      throw StateError('microphone permission denied');
    }
    final dir = await (_tempDir?.call() ?? Future<String>.value(Directory.systemTemp.path));
    final path = p.join(dir, '${_uuid.v4()}.m4a');
    await _rec.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
    _startedAt = DateTime.now();
    _path = path;
    return path;
  }

  Future<void> pause() => _rec.pause();
  Future<void> resume() => _rec.resume();

  Future<RecordingFile> stop() async {
    await _rec.stop();
    final path = _path!;
    final file = File(path);
    final size = await file.exists() ? await file.length() : 0;
    final ms = _startedAt == null ? 0 : DateTime.now().difference(_startedAt!).inMilliseconds;
    return RecordingFile(path: path, durationMs: ms, fileSize: size);
  }
}
```
> The `_tempDir` indirection lets tests inject a directory; in production the provider (Task 16) passes `() async => (await getTemporaryDirectory()).path`.

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/features/recordings/recording_service_test.dart`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add lib/features/recordings/recording_service.dart test/features/recordings/recording_service_test.dart
git commit -m "feat: add RecordingService for AAC capture with pause/resume"
```

---

## Task 16: Recording info sheet + control screen (create a Recording)

**Files:**
- Create: `lib/features/recordings/recording_info_sheet.dart`, `lib/features/recordings/recording_control_screen.dart`
- Create: `lib/providers/recording_providers.dart`
- Test: `test/features/recordings/recording_info_sheet_test.dart`

**Interfaces:**
- Consumes: `modeDaoProvider`, `recordingDaoProvider`, `RecordingService`, `currentUserIdProvider`, `settingsDaoProvider`.
- Produces: `recordingServiceProvider`. `RecordingInfoSheet` (mode chip row from `modeDao.allModes()`, a required Title field, Start button). `RecordingControlScreen` showing elapsed time and stop button; on stop it persists a `Recording` row (id via uuid, `modeId` = selected, `language` from settings default) and pops to `/`.

- [ ] **Step 1: Write the failing widget test**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';
import 'package:sorigami/features/recordings/recording_info_sheet.dart';
import 'package:sorigami/providers/providers.dart';
import 'package:drift/native.dart';

void main() {
  testWidgets('info sheet shows seeded mode chips', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await seedIfEmpty(db);
    await tester.pumpWidget(ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const MaterialApp(home: Scaffold(body: RecordingInfoSheet())),
    ));
    await tester.pumpAndSettle();
    expect(find.text('General'), findsOneWidget);
    expect(find.text('Team Meeting'), findsOneWidget);
    expect(find.text('Start Recording'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/recordings/recording_info_sheet_test.dart`
Expected: FAIL — sheet not defined.

- [ ] **Step 3: Write `lib/providers/recording_providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../features/recordings/recording_service.dart';
import '../data/db/database.dart';
import 'providers.dart';

final recordingServiceProvider = Provider<RecordingService>(
  (ref) => RecordingService(tempDir: () async => (await getTemporaryDirectory()).path),
);

final modesListProvider = FutureProvider<List<Mode>>(
  (ref) => ref.watch(modeDaoProvider).allModes(),
);
```

- [ ] **Step 4: Write `lib/features/recordings/recording_info_sheet.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/db/database.dart';
import '../../providers/recording_providers.dart';
import 'recording_control_screen.dart';

class RecordingInfoSheet extends ConsumerStatefulWidget {
  const RecordingInfoSheet({super.key});
  @override
  ConsumerState<RecordingInfoSheet> createState() => _State();
}

class _State extends ConsumerState<RecordingInfoSheet> {
  final _title = TextEditingController();
  String? _modeId;

  @override
  Widget build(BuildContext context) {
    final modes = ref.watch(modesListProvider);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: modes.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Text('Error: $e'),
        data: (list) {
          _modeId ??= list.firstWhere((m) => m.isDefault, orElse: () => list.first).id;
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                height: 48,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    for (final m in list)
                      Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text('${m.icon} ${m.name}'),
                          selected: _modeId == m.id,
                          onSelected: (_) => setState(() => _modeId = m.id),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _title,
                decoration: const InputDecoration(labelText: 'Title'),
                onChanged: (_) => setState(() {}), // re-evaluate Start button
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _title.text.trim().isEmpty
                    ? null
                    : () => Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) => RecordingControlScreen(
                            title: _title.text.trim(), modeId: _modeId!),
                        )),
                child: const Text('Start Recording'),
              ),
            ],
          );
        },
      ),
    );
  }
}
```

- [ ] **Step 5: Write `lib/features/recordings/recording_control_screen.dart`**

```dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:drift/drift.dart' show Value;
import 'package:uuid/uuid.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';
import '../../providers/recording_providers.dart';

class RecordingControlScreen extends ConsumerStatefulWidget {
  const RecordingControlScreen({super.key, required this.title, required this.modeId});
  final String title;
  final String modeId;
  @override
  ConsumerState<RecordingControlScreen> createState() => _State();
}

class _State extends ConsumerState<RecordingControlScreen> {
  Duration _elapsed = Duration.zero;
  Timer? _timer;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _begin();
  }

  Future<void> _begin() async {
    await ref.read(recordingServiceProvider).start();
    setState(() => _started = true);
    _timer = Timer.periodic(const Duration(seconds: 1),
        (_) => setState(() => _elapsed += const Duration(seconds: 1)));
  }

  Future<void> _stop() async {
    _timer?.cancel();
    final file = await ref.read(recordingServiceProvider).stop();
    final db = ref.read(recordingDaoProvider);
    await db.upsert(RecordingsCompanion.insert(
      id: const Uuid().v4(),
      title: widget.title,
      language: 'auto',
      audioFilePath: file.path,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      modeId: Value(widget.modeId),
      audioDurationMs: Value(file.durationMs),
      audioFileSize: Value(file.fileSize),
    ));
    if (mounted) context.go('/');
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final m = _elapsed.inMinutes.toString().padLeft(2, '0');
    final s = (_elapsed.inSeconds % 60).toString().padLeft(2, '0');
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('$m:$s', style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 32),
            FilledButton.icon(
              onPressed: _started ? _stop : null,
              icon: const Icon(Icons.stop),
              label: const Text('Stop & Save'),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `flutter test test/features/recordings/recording_info_sheet_test.dart`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add lib/features/recordings/ lib/providers/recording_providers.dart test/features/recordings/recording_info_sheet_test.dart
git commit -m "feat: add recording info sheet and control screen"
```

---

## Task 17: Recordings list screen

**Files:**
- Modify: `lib/features/recordings/recordings_screen.dart`
- Create: `lib/providers/recordings_list_provider.dart`
- Test: `test/features/recordings/recordings_screen_test.dart`

**Interfaces:**
- Consumes: `recordingDaoProvider.watchAll()`, `modeDaoProvider`.
- Produces: `recordingsStreamProvider` (`StreamProvider<List<Recording>>`). `RecordingsScreen` lists recordings (title, mode icon, date, duration, status badge), a FAB that opens `RecordingInfoSheet` in a bottom sheet, and a Settings action that routes to `/settings`. Tapping a row routes to `/recording/:id`.

- [ ] **Step 1: Write the failing widget test**

```dart
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';
import 'package:sorigami/features/recordings/recordings_screen.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  testWidgets('renders a recording title', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await seedIfEmpty(db);
    await db.recordingDao.upsert(RecordingsCompanion.insert(
      id: 'r1', title: 'Q3 Planning', language: 'auto', audioFilePath: '/a',
      createdAt: DateTime(2026), updatedAt: DateTime(2026),
    ));
    await tester.pumpWidget(ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const MaterialApp(home: RecordingsScreen()),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Q3 Planning'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/recordings/recordings_screen_test.dart`
Expected: FAIL — screen still placeholder.

- [ ] **Step 3: Write `lib/providers/recordings_list_provider.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import 'providers.dart';

final recordingsStreamProvider = StreamProvider<List<Recording>>(
  (ref) => ref.watch(recordingDaoProvider).watchAll(),
);
```

- [ ] **Step 4: Replace `lib/features/recordings/recordings_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../providers/recordings_list_provider.dart';
import 'recording_info_sheet.dart';

class RecordingsScreen extends ConsumerWidget {
  const RecordingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recordings = ref.watch(recordingsStreamProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sorigami'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => context.go('/settings'),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.mic),
        label: const Text('Record'),
        onPressed: () => showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          builder: (_) => const Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: RecordingInfoSheet(),
          ),
        ),
      ),
      body: recordings.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (list) => list.isEmpty
            ? const Center(child: Text('No recordings yet. Tap Record to start.'))
            : ListView.builder(
                itemCount: list.length,
                itemBuilder: (_, i) {
                  final r = list[i];
                  return ListTile(
                    title: Text(r.title),
                    subtitle: Text(DateFormat.yMMMd().add_jm().format(r.createdAt)),
                    trailing: _StatusBadge(status: r.jobStatus),
                    onTap: () => context.go('/recording/${r.id}'),
                  );
                },
              ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) => Chip(label: Text(status));
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/recordings/recordings_screen_test.dart`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/features/recordings/recordings_screen.dart lib/providers/recordings_list_provider.dart test/features/recordings/recordings_screen_test.dart
git commit -m "feat: build recordings list screen with FAB and status badges"
```

---

## Task 18: Google Drive uploader

**Files:**
- Create: `lib/data/drive/drive_uploader.dart`
- Test: `test/data/drive/drive_uploader_test.dart`

**Interfaces:**
- Consumes: `google_sign_in` (with Drive scope) + `extension_google_sign_in_as_googleapis_auth` + `googleapis/drive/v3`.
- Produces: `class DriveUploader { Future<bool> connect(); Future<void> disconnect(); Future<String> upload(String filePath, String fileName); }`. `connect()` requests the `drive.file` scope; `upload()` returns the created Drive file id. Constructor accepts an injected `drive.DriveApi Function()?` factory so tests can stub the API.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:googleapis/drive/v3.dart' as drive;
import 'package:mocktail/mocktail.dart';
import 'package:sorigami/data/drive/drive_uploader.dart';
import 'dart:io';

class _MockApi extends Mock implements drive.DriveApi {}
class _MockFiles extends Mock implements drive.FilesResource {}

void main() {
  setUpAll(() => registerFallbackValue(drive.File()));

  test('upload returns created file id', () async {
    final api = _MockApi();
    final files = _MockFiles();
    when(() => api.files).thenReturn(files);
    when(() => files.create(any(), uploadMedia: any(named: 'uploadMedia')))
        .thenAnswer((_) async => drive.File(id: 'file-123'));

    final tmp = File('${Directory.systemTemp.path}/u.m4a')..writeAsBytesSync([1, 2, 3]);
    final uploader = DriveUploader(apiFactory: () async => api);
    final id = await uploader.upload(tmp.path, 'u.m4a');
    expect(id, 'file-123');
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/drive/drive_uploader_test.dart`
Expected: FAIL — `DriveUploader` not defined.

- [ ] **Step 3: Write `lib/data/drive/drive_uploader.dart`**

```dart
import 'dart:io';
import 'package:extension_google_sign_in_as_googleapis_auth/extension_google_sign_in_as_googleapis_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/drive/v3.dart' as drive;

class DriveUploader {
  DriveUploader({GoogleSignIn? googleSignIn, Future<drive.DriveApi> Function()? apiFactory})
      : _google = googleSignIn ??
            GoogleSignIn(scopes: const [drive.DriveApi.driveFileScope]),
        _apiFactory = apiFactory;

  final GoogleSignIn _google;
  final Future<drive.DriveApi> Function()? _apiFactory;

  Future<bool> connect() async {
    final account = await _google.signIn();
    return account != null;
  }

  Future<void> disconnect() => _google.disconnect();

  Future<drive.DriveApi> _api() async {
    if (_apiFactory != null) return _apiFactory!();
    final client = await _google.authenticatedClient();
    if (client == null) throw StateError('Drive not connected');
    return drive.DriveApi(client);
  }

  Future<String> upload(String filePath, String fileName) async {
    final api = await _api();
    final file = File(filePath);
    final media = drive.Media(file.openRead(), await file.length());
    final created = await api.files.create(
      drive.File()..name = fileName,
      uploadMedia: media,
    );
    return created.id!;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/drive/drive_uploader_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/data/drive/drive_uploader.dart test/data/drive/drive_uploader_test.dart
git commit -m "feat: add Google Drive uploader with drive.file scope"
```

---

## Task 19: Upload controller (queue status on Recording)

**Files:**
- Create: `lib/features/detail/upload_controller.dart`
- Create: `lib/providers/upload_providers.dart`
- Test: `test/features/detail/upload_controller_test.dart`

**Interfaces:**
- Consumes: `DriveUploader`, `RecordingDao`.
- Produces: `class UploadController { Future<void> upload(String recordingId); }`. It sets `uploadStatus = uploading`, calls `DriveUploader.upload`, then sets `done` + `driveFileId`, or `failed` on error. `driveUploaderProvider`, `uploadControllerProvider`.

- [ ] **Step 1: Write the failing test**

```dart
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/drive/drive_uploader.dart';
import 'package:sorigami/features/detail/upload_controller.dart';

class _MockUploader extends Mock implements DriveUploader {}

void main() {
  late AppDatabase db;
  setUp(() => db = AppDatabase(NativeDatabase.memory()));
  tearDown(() => db.close());

  Future<void> seedRec() => db.recordingDao.upsert(RecordingsCompanion.insert(
        id: 'r1', title: 'T', language: 'auto', audioFilePath: '/a.m4a',
        createdAt: DateTime(2026), updatedAt: DateTime(2026)));

  test('successful upload sets status done and driveFileId', () async {
    await seedRec();
    final up = _MockUploader();
    when(() => up.upload(any(), any())).thenAnswer((_) async => 'file-9');
    await UploadController(uploader: up, dao: db.recordingDao).upload('r1');
    final r = await db.recordingDao.byId('r1');
    expect(r!.uploadStatus, 'done');
    expect(r.driveFileId, 'file-9');
  });

  test('failed upload sets status failed', () async {
    await seedRec();
    final up = _MockUploader();
    when(() => up.upload(any(), any())).thenThrow(Exception('network'));
    await UploadController(uploader: up, dao: db.recordingDao).upload('r1');
    expect((await db.recordingDao.byId('r1'))!.uploadStatus, 'failed');
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/detail/upload_controller_test.dart`
Expected: FAIL — `UploadController` not defined.

- [ ] **Step 3: Write `lib/features/detail/upload_controller.dart`**

```dart
import 'package:path/path.dart' as p;
import '../../data/db/daos/recording_dao.dart';
import '../../data/drive/drive_uploader.dart';

class UploadController {
  UploadController({required this.uploader, required this.dao});
  final DriveUploader uploader;
  final RecordingDao dao;

  Future<void> upload(String recordingId) async {
    final rec = await dao.byId(recordingId);
    if (rec == null) return;
    await dao.setUploadStatus(recordingId, 'uploading');
    try {
      final id = await uploader.upload(rec.audioFilePath, p.basename(rec.audioFilePath));
      await dao.setUploadStatus(recordingId, 'done', driveFileId: id);
    } catch (_) {
      await dao.setUploadStatus(recordingId, 'failed');
    }
  }
}
```

- [ ] **Step 4: Write `lib/providers/upload_providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/drive/drive_uploader.dart';
import '../features/detail/upload_controller.dart';
import 'providers.dart';

final driveUploaderProvider = Provider<DriveUploader>((ref) => DriveUploader());
final uploadControllerProvider = Provider<UploadController>((ref) => UploadController(
      uploader: ref.watch(driveUploaderProvider),
      dao: ref.watch(recordingDaoProvider),
    ));
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/detail/upload_controller_test.dart`
Expected: PASS (both).

- [ ] **Step 6: Commit**

```bash
git add lib/features/detail/upload_controller.dart lib/providers/upload_providers.dart test/features/detail/upload_controller_test.dart
git commit -m "feat: add upload controller with status transitions"
```

---

## Task 20: AI process controller (submit + poll + store result)

**Files:**
- Create: `lib/features/detail/ai_process_controller.dart`
- Create: `lib/providers/ai_providers.dart`
- Test: `test/features/detail/ai_process_controller_test.dart`

**Interfaces:**
- Consumes: `PipelineClient`, `RecordingDao`, `ModeDao`, `SkillDao`, `resolveSkills` (Task 9).
- Produces: `class AiProcessController { Future<void> process(String recordingId, {Duration pollInterval}); }`. It resolves skills, submits a `JobSubmission`, stores `jobId` + status `requested`, polls `status()` until terminal (with `pollInterval`, default 5s, max 40 attempts), then on `completed` fetches `result()` and stores a `RecordingResult` (skillResults JSON) and sets `jobStatus = completed`; on `failed`/timeout sets `jobStatus = failed` with the error. `aiProcessControllerProvider`.

- [ ] **Step 1: Write the failing test**

```dart
import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';
import 'package:sorigami/data/pipeline/mock_pipeline_client.dart';
import 'package:sorigami/features/detail/ai_process_controller.dart';

void main() {
  late AppDatabase db;
  setUp(() async {
    db = AppDatabase(NativeDatabase.memory());
    await seedIfEmpty(db);
  });
  tearDown(() => db.close());

  test('process stores result and marks completed', () async {
    final def = (await db.modeDao.defaultMode())!;
    await db.recordingDao.upsert(RecordingsCompanion.insert(
      id: 'r1', title: 'T', language: 'auto', audioFilePath: '/a.m4a',
      createdAt: DateTime(2026), updatedAt: DateTime(2026), modeId: Value(def.id),
      audioDurationMs: const Value(60000),
    ));
    final ctrl = AiProcessController(
      client: MockPipelineClient(processingTime: Duration.zero),
      recordingDao: db.recordingDao, modeDao: db.modeDao, skillDao: db.skillDao,
    );
    await ctrl.process('r1', pollInterval: const Duration(milliseconds: 1));
    final r = await db.recordingDao.byId('r1');
    expect(r!.jobStatus, 'completed');
    final res = await db.recordingDao.resultFor('r1');
    expect(res, isNotNull);
    expect((jsonDecode(res!.skillResults) as List).isNotEmpty, true);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/detail/ai_process_controller_test.dart`
Expected: FAIL — `AiProcessController` not defined.

- [ ] **Step 3: Write `lib/features/detail/ai_process_controller.dart`**

```dart
import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:uuid/uuid.dart';
import '../../data/db/daos/recording_dao.dart';
import '../../data/db/daos/mode_dao.dart';
import '../../data/db/daos/skill_dao.dart';
import '../../data/db/database.dart';
import '../../data/pipeline/pipeline_client.dart';
import '../../domain/models/skill_resolution.dart';

class AiProcessController {
  AiProcessController({
    required this.client,
    required this.recordingDao,
    required this.modeDao,
    required this.skillDao,
  });

  final PipelineClient client;
  final RecordingDao recordingDao;
  final ModeDao modeDao;
  final SkillDao skillDao;

  Future<void> process(String recordingId,
      {Duration pollInterval = const Duration(seconds: 5)}) async {
    final rec = await recordingDao.byId(recordingId);
    if (rec == null) return;

    final skills = await resolveSkills(rec, modeDao: modeDao, skillDao: skillDao);
    final modeName = rec.modeId == null
        ? null
        : (await modeDao.allModes())
            .firstWhere((m) => m.id == rec.modeId)
            .name;

    final jobId = await client.submit(JobSubmission(
      recordingId: rec.id,
      audioFilePath: rec.audioFilePath,
      audioDurationS: ((rec.audioDurationMs ?? 0) / 1000).round(),
      category: rec.category,
      modeName: modeName,
      skills: skills,
    ));
    await recordingDao.setJobStatus(recordingId, 'requested', jobId: jobId);

    for (var attempt = 0; attempt < 40; attempt++) {
      final s = await client.status(jobId);
      if (s.status == PipelineJobStatus.completed) {
        final result = await client.result(jobId);
        await recordingDao.saveResult(RecordingResultsCompanion.insert(
          id: const Uuid().v4(),
          recordingId: recordingId,
          transcript: result.transcript,
          skillResults: jsonEncode([
            for (final sr in result.skillResults)
              {'skill_id': sr.skillId, 'skill_name': sr.skillName, 'output': sr.output}
          ]),
          receivedAt: DateTime.now(),
        ));
        await recordingDao.setJobStatus(recordingId, 'completed');
        return;
      }
      if (s.status == PipelineJobStatus.failed) {
        await recordingDao.setJobStatus(recordingId, 'failed', error: s.error);
        return;
      }
      await recordingDao.setJobStatus(recordingId, 'processing');
      await Future<void>.delayed(pollInterval);
    }
    await recordingDao.setJobStatus(recordingId, 'failed', error: 'Timed out — tap to retry');
  }
}
```

- [ ] **Step 4: Write `lib/providers/ai_providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../features/detail/ai_process_controller.dart';
import 'providers.dart';

final aiProcessControllerProvider = Provider<AiProcessController>((ref) => AiProcessController(
      client: ref.watch(pipelineClientProvider),
      recordingDao: ref.watch(recordingDaoProvider),
      modeDao: ref.watch(modeDaoProvider),
      skillDao: ref.watch(skillDaoProvider),
    ));
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/detail/ai_process_controller_test.dart`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/features/detail/ai_process_controller.dart lib/providers/ai_providers.dart test/features/detail/ai_process_controller_test.dart
git commit -m "feat: add AI process controller (submit, poll, store result)"
```

---

## Task 21: Recording detail screen with tabs

**Files:**
- Modify: `lib/features/detail/recording_detail_screen.dart`
- Create: `lib/features/detail/info_tab.dart`, `upload_tab.dart`, `ai_process_tab.dart`, `result_tab.dart`
- Create: `lib/providers/detail_providers.dart`
- Test: `test/features/detail/result_tab_test.dart`

**Interfaces:**
- Consumes: `recordingDaoProvider`, `uploadControllerProvider`, `aiProcessControllerProvider`.
- Produces: `recordingByIdProvider` (`StreamProvider.family<Recording?, String>`), `resultByIdProvider` (`FutureProvider.family<RecordingResult?, String>`). `RecordingDetailScreen` is a 4-tab `TabBarView`: Info, Upload (button → uploadController), AIProcess (button → aiProcessController + status text), Result (transcript + one expansion tile per skill output, with Copy).

- [ ] **Step 1: Write the failing widget test (Result tab renders skill sections)**

```dart
import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/features/detail/result_tab.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  testWidgets('result tab shows transcript and skill section', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await db.recordingDao.upsert(RecordingsCompanion.insert(
      id: 'r1', title: 'T', language: 'auto', audioFilePath: '/a',
      createdAt: DateTime(2026), updatedAt: DateTime(2026)));
    await db.recordingDao.saveResult(RecordingResultsCompanion.insert(
      id: 'res1', recordingId: 'r1', transcript: 'speaker_a: hi',
      skillResults: jsonEncode([
        {'skill_id': 's1', 'skill_name': 'Action Items', 'output': 'do X'}
      ]),
      receivedAt: DateTime(2026)));
    await tester.pumpWidget(ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const MaterialApp(home: Scaffold(body: ResultTab(recordingId: 'r1'))),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Action Items'), findsOneWidget);
    expect(find.textContaining('speaker_a'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/detail/result_tab_test.dart`
Expected: FAIL — `ResultTab` not defined.

- [ ] **Step 3: Write `lib/providers/detail_providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import 'providers.dart';

final recordingByIdProvider = StreamProvider.family<Recording?, String>((ref, id) {
  final dao = ref.watch(recordingDaoProvider);
  return dao.watchAll().map((list) => list.where((r) => r.id == id).firstOrNull);
});

final resultByIdProvider = FutureProvider.family<RecordingResult?, String>(
  (ref, id) => ref.watch(recordingDaoProvider).resultFor(id),
);
```

- [ ] **Step 4: Write `lib/features/detail/result_tab.dart`**

```dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/detail_providers.dart';

class ResultTab extends ConsumerWidget {
  const ResultTab({super.key, required this.recordingId});
  final String recordingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(resultByIdProvider(recordingId));
    return result.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (res) {
        if (res == null) {
          return const Center(child: Text('No results yet. Run AI processing.'));
        }
        final skills = (jsonDecode(res.skillResults) as List).cast<Map<String, dynamic>>();
        return ListView(
          children: [
            ExpansionTile(
              title: const Text('Transcript'),
              initiallyExpanded: true,
              children: [_copyableBody(context, res.transcript)],
            ),
            for (final s in skills)
              ExpansionTile(
                title: Text(s['skill_name'] as String),
                children: [_copyableBody(context, s['output'] as String)],
              ),
          ],
        );
      },
    );
  }

  Widget _copyableBody(BuildContext context, String text) => Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SelectableText(text),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                icon: const Icon(Icons.copy, size: 16),
                label: const Text('Copy'),
                onPressed: () => Clipboard.setData(ClipboardData(text: text)),
              ),
            ),
          ],
        ),
      );
}
```

- [ ] **Step 5: Write `lib/features/detail/upload_tab.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/detail_providers.dart';
import '../../providers/upload_providers.dart';

class UploadTab extends ConsumerWidget {
  const UploadTab({super.key, required this.recordingId});
  final String recordingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rec = ref.watch(recordingByIdProvider(recordingId));
    return rec.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (r) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Upload status: ${r?.uploadStatus ?? "none"}'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => ref.read(uploadControllerProvider).upload(recordingId),
              child: const Text('Upload to Google Drive'),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 6: Write `lib/features/detail/ai_process_tab.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/detail_providers.dart';
import '../../providers/ai_providers.dart';

class AiProcessTab extends ConsumerWidget {
  const AiProcessTab({super.key, required this.recordingId});
  final String recordingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rec = ref.watch(recordingByIdProvider(recordingId));
    return rec.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (r) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('AI status: ${r?.jobStatus ?? "none"}'),
            if (r?.jobError != null) Text(r!.jobError!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => ref.read(aiProcessControllerProvider).process(recordingId),
              child: const Text('Process with AI'),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 7: Write `lib/features/detail/info_tab.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/detail_providers.dart';

class InfoTab extends ConsumerWidget {
  const InfoTab({super.key, required this.recordingId});
  final String recordingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rec = ref.watch(recordingByIdProvider(recordingId));
    return rec.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (r) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ListTile(title: const Text('Title'), subtitle: Text(r?.title ?? '')),
          ListTile(title: const Text('Memo'), subtitle: Text(r?.memo ?? '—')),
          ListTile(title: const Text('Language'), subtitle: Text(r?.language ?? '')),
        ],
      ),
    );
  }
}
```

- [ ] **Step 8: Replace `lib/features/detail/recording_detail_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'info_tab.dart';
import 'upload_tab.dart';
import 'ai_process_tab.dart';
import 'result_tab.dart';

class RecordingDetailScreen extends StatelessWidget {
  const RecordingDetailScreen({super.key, required this.recordingId});
  final String recordingId;

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Recording'),
          bottom: const TabBar(tabs: [
            Tab(text: 'Info'),
            Tab(text: 'Upload'),
            Tab(text: 'AI'),
            Tab(text: 'Result'),
          ]),
        ),
        body: TabBarView(children: [
          InfoTab(recordingId: recordingId),
          UploadTab(recordingId: recordingId),
          AiProcessTab(recordingId: recordingId),
          ResultTab(recordingId: recordingId),
        ]),
      ),
    );
  }
}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `flutter test test/features/detail/result_tab_test.dart`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add lib/features/detail/ lib/providers/detail_providers.dart test/features/detail/result_tab_test.dart
git commit -m "feat: add recording detail screen with info/upload/ai/result tabs"
```

---

## Task 22: Settings screen + pipeline server section

**Files:**
- Modify: `lib/features/settings/settings_screen.dart`
- Create: `lib/features/settings/pipeline_server_section.dart`
- Create: `lib/providers/settings_providers.dart`
- Test: `test/features/settings/pipeline_server_section_test.dart`

**Interfaces:**
- Consumes: `settingsDaoProvider`, `currentUserIdProvider`, `pipelineClientProvider`, `authServiceProvider`.
- Produces: `settingsProvider` (`StreamProvider<UserSettingsTableData?>` for current user). `PipelineServerSection` with a URL `TextField` (saves to settings) and a "Test connection" button that calls `pipelineClient.health()` and shows ✅/❌. `SettingsScreen` lists Account (sign out), Pipeline Server, and navigation to Modes/Skills.

- [ ] **Step 1: Write the failing widget test**

```dart
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/features/settings/pipeline_server_section.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  testWidgets('test-connection shows success with healthy mock', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await db.settingsDao.ensure('u1');
    await tester.pumpWidget(ProviderScope(
      overrides: [
        databaseProvider.overrideWithValue(db),
        currentUserIdProvider.overrideWith((ref) => 'u1'),
      ],
      child: const MaterialApp(home: Scaffold(body: PipelineServerSection())),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Test connection'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Connected'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/settings/pipeline_server_section_test.dart`
Expected: FAIL — section not defined.

- [ ] **Step 3: Write `lib/providers/settings_providers.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import 'providers.dart';

final settingsProvider = StreamProvider<UserSettingsTableData?>((ref) {
  final uid = ref.watch(currentUserIdProvider);
  if (uid == null) return const Stream.empty();
  final dao = ref.watch(settingsDaoProvider);
  return dao.watch(uid);
});
```

- [ ] **Step 4: Write `lib/features/settings/pipeline_server_section.dart`**

```dart
import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';
import '../../providers/settings_providers.dart';

class PipelineServerSection extends ConsumerStatefulWidget {
  const PipelineServerSection({super.key});
  @override
  ConsumerState<PipelineServerSection> createState() => _State();
}

class _State extends ConsumerState<PipelineServerSection> {
  final _url = TextEditingController();
  String? _testResult;
  bool _loaded = false;

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    settings.whenData((s) {
      if (!_loaded && s != null) {
        _url.text = s.pipelineServerUrl;
        _loaded = true;
      }
    });
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Pipeline Server', style: TextStyle(fontWeight: FontWeight.bold)),
          TextField(
            controller: _url,
            decoration: const InputDecoration(hintText: 'http://192.168.1.42:8000'),
            onChanged: (v) {
              final uid = ref.read(currentUserIdProvider);
              if (uid != null) {
                ref.read(settingsDaoProvider).update(UserSettingsTableCompanion(
                    userId: Value(uid), pipelineServerUrl: Value(v)));
              }
            },
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              OutlinedButton(
                onPressed: () async {
                  final ok = await ref.read(pipelineClientProvider).health();
                  setState(() => _testResult = ok ? 'Connected ✅' : 'Unreachable ❌');
                },
                child: const Text('Test connection'),
              ),
              const SizedBox(width: 12),
              if (_testResult != null) Text(_testResult!),
            ],
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 5: Replace `lib/features/settings/settings_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/providers.dart';
import 'pipeline_server_section.dart';
import 'modes_section.dart';
import 'skills_section.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.go('/')),
      ),
      body: ListView(
        children: [
          const PipelineServerSection(),
          const Divider(),
          ListTile(
            title: const Text('Modes'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const ModesSection())),
          ),
          ListTile(
            title: const Text('Skills'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SkillsSection())),
          ),
          const Divider(),
          ListTile(
            title: const Text('Sign out'),
            onTap: () => ref.read(authServiceProvider).signOut(),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `flutter test test/features/settings/pipeline_server_section_test.dart`
Expected: PASS. (Modes/Skills sections are created in Task 23; if compilation fails on those imports, create empty placeholder widgets first, then complete in Task 23.)

- [ ] **Step 7: Commit**

```bash
git add lib/features/settings/ lib/providers/settings_providers.dart test/features/settings/pipeline_server_section_test.dart
git commit -m "feat: add settings screen with pipeline server test-connection"
```

---

## Task 23: Modes & Skills management screens

**Files:**
- Create: `lib/features/settings/modes_section.dart`, `mode_edit_screen.dart`, `skills_section.dart`, `skill_edit_screen.dart`
- Test: `test/features/settings/skill_edit_screen_test.dart`

**Interfaces:**
- Consumes: `skillDaoProvider`, `modeDaoProvider`.
- Produces: `ModesSection` (list of modes, set default, tap to edit), `ModeEditScreen` (name, icon, multi-select skills), `SkillsSection` (list of skills, tap to edit, add), `SkillEditScreen` (output intent fields + transcription intent + Advanced JSON `pipelineParams` editor). Saving a skill writes via `skillDao.upsert`.

- [ ] **Step 1: Write the failing widget test**

```dart
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/features/settings/skill_edit_screen.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  testWidgets('saving a new skill persists it', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await tester.pumpWidget(ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: const MaterialApp(home: SkillEditScreen()),
    ));
    await tester.enterText(find.byKey(const Key('skill-name')), 'Risks');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    final all = await db.skillDao.all();
    expect(all.any((s) => s.name == 'Risks'), true);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/settings/skill_edit_screen_test.dart`
Expected: FAIL — `SkillEditScreen` not defined.

- [ ] **Step 3: Write `lib/features/settings/skill_edit_screen.dart`**

```dart
import 'dart:convert';
import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';

class SkillEditScreen extends ConsumerStatefulWidget {
  const SkillEditScreen({super.key, this.existing});
  final Skill? existing;
  @override
  ConsumerState<SkillEditScreen> createState() => _State();
}

class _State extends ConsumerState<SkillEditScreen> {
  late final _name = TextEditingController(text: widget.existing?.name ?? '');
  late final _focus = TextEditingController(text: widget.existing?.focusArea ?? '');
  late final _instructions =
      TextEditingController(text: widget.existing?.additionalInstructions ?? '');
  late final _pipelineParams = TextEditingController(
      text: widget.existing?.pipelineParams == null
          ? ''
          : jsonEncode(widget.existing!.pipelineParams));
  String _outputType = 'summary';
  bool _identifySpeakers = false;

  @override
  void initState() {
    super.initState();
    _outputType = widget.existing?.outputType ?? 'summary';
    _identifySpeakers = widget.existing?.identifySpeakers ?? false;
  }

  Future<void> _save() async {
    Map<String, dynamic>? params;
    if (_pipelineParams.text.trim().isNotEmpty) {
      params = (jsonDecode(_pipelineParams.text) as Map).cast<String, dynamic>();
    }
    await ref.read(skillDaoProvider).upsert(SkillsCompanion(
      id: Value(widget.existing?.id ?? const Uuid().v4()),
      name: Value(_name.text.trim()),
      outputType: Value(_outputType),
      focusArea: Value(_focus.text.trim().isEmpty ? null : _focus.text.trim()),
      identifySpeakers: Value(_identifySpeakers),
      additionalInstructions:
          Value(_instructions.text.trim().isEmpty ? null : _instructions.text.trim()),
      pipelineParams: Value(params),
      createdAt: Value(widget.existing?.createdAt ?? DateTime.now()),
    ));
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.existing == null ? 'New Skill' : 'Edit Skill')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            key: const Key('skill-name'),
            controller: _name,
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _outputType,
            decoration: const InputDecoration(labelText: 'Output type'),
            items: const ['summary', 'tasks', 'both', 'custom']
                .map((v) => DropdownMenuItem(value: v, child: Text(v)))
                .toList(),
            onChanged: (v) => setState(() => _outputType = v ?? 'summary'),
          ),
          TextField(controller: _focus, decoration: const InputDecoration(labelText: 'Focus area')),
          SwitchListTile(
            title: const Text('Identify speakers'),
            value: _identifySpeakers,
            onChanged: (v) => setState(() => _identifySpeakers = v),
          ),
          TextField(
            controller: _instructions,
            decoration: const InputDecoration(labelText: 'Additional instructions'),
            maxLines: 3,
          ),
          const Divider(),
          const Text('Advanced (pipeline params JSON)'),
          TextField(
            controller: _pipelineParams,
            decoration: const InputDecoration(hintText: '{"num_speakers": 2}'),
            maxLines: 3,
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _save, child: const Text('Save')),
        ],
      ),
    );
  }
}
```

- [ ] **Step 4: Write `lib/features/settings/skills_section.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';
import 'skill_edit_screen.dart';

class SkillsSection extends ConsumerWidget {
  const SkillsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Skills')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.of(context)
            .push(MaterialPageRoute(builder: (_) => const SkillEditScreen())),
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<Skill>>(
        future: ref.watch(skillDaoProvider).all(),
        builder: (context, snap) {
          final skills = snap.data ?? const [];
          return ListView(
            children: [
              for (final s in skills)
                ListTile(
                  title: Text(s.name),
                  subtitle: Text(s.outputType),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => SkillEditScreen(existing: s))),
                ),
            ],
          );
        },
      ),
    );
  }
}
```

- [ ] **Step 5: Write `lib/features/settings/modes_section.dart` and `mode_edit_screen.dart`**

```dart
// modes_section.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';
import 'mode_edit_screen.dart';

class ModesSection extends ConsumerWidget {
  const ModesSection({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Modes')),
      body: FutureBuilder<List<Mode>>(
        future: ref.watch(modeDaoProvider).allModes(),
        builder: (context, snap) {
          final modes = snap.data ?? const [];
          return ListView(
            children: [
              for (final m in modes)
                ListTile(
                  leading: Text(m.icon, style: const TextStyle(fontSize: 24)),
                  title: Text(m.name),
                  trailing: m.isDefault
                      ? const Icon(Icons.star, color: Colors.amber)
                      : IconButton(
                          icon: const Icon(Icons.star_border),
                          onPressed: () async {
                            await ref.read(modeDaoProvider).setDefault(m.id);
                            ref.invalidate(modeDaoProvider);
                          },
                        ),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => ModeEditScreen(mode: m))),
                ),
            ],
          );
        },
      ),
    );
  }
}
```
```dart
// mode_edit_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';

class ModeEditScreen extends ConsumerStatefulWidget {
  const ModeEditScreen({super.key, required this.mode});
  final Mode mode;
  @override
  ConsumerState<ModeEditScreen> createState() => _State();
}

class _State extends ConsumerState<ModeEditScreen> {
  Set<String> _selected = {};
  List<Skill> _all = [];
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    _all = await ref.read(skillDaoProvider).all();
    _selected = (await ref.read(modeDaoProvider).skillIdsFor(widget.mode.id)).toSet();
    setState(() => _loaded = true);
  }

  Future<void> _save() async {
    await ref.read(modeDaoProvider).setSkills(widget.mode.id, _selected.toList());
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      appBar: AppBar(title: Text('${widget.mode.icon} ${widget.mode.name}')),
      body: ListView(
        children: [
          for (final s in _all)
            CheckboxListTile(
              title: Text(s.name),
              value: _selected.contains(s.id),
              onChanged: (v) => setState(() =>
                  v == true ? _selected.add(s.id) : _selected.remove(s.id)),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _save, icon: const Icon(Icons.check), label: const Text('Save'),
      ),
    );
  }
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `flutter test test/features/settings/skill_edit_screen_test.dart`
Expected: PASS.

- [ ] **Step 7: Run the full test suite**

Run: `flutter test`
Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add lib/features/settings/ test/features/settings/skill_edit_screen_test.dart
git commit -m "feat: add modes and skills management screens"
```

---

## Task 24: Full-app smoke test + analyzer clean

**Files:**
- Test: `test/app_smoke_test.dart`

**Interfaces:**
- Consumes: everything.
- Produces: a smoke test that boots the app with an in-memory DB and a logged-in user override, and asserts the recordings screen renders.

- [ ] **Step 1: Write the smoke test**

```dart
import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigami/app.dart';
import 'package:sorigami/data/db/database.dart';
import 'package:sorigami/data/seed/seed_data.dart';
import 'package:sorigami/providers/providers.dart';

void main() {
  testWidgets('logged-in user sees recordings screen', (tester) async {
    final db = AppDatabase(NativeDatabase.memory());
    await seedIfEmpty(db);
    await tester.pumpWidget(ProviderScope(
      overrides: [
        databaseProvider.overrideWithValue(db),
        currentUserIdProvider.overrideWith((ref) => 'u1'),
      ],
      child: const SorigamiApp(),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Sorigami'), findsOneWidget); // app bar title
    expect(find.text('Record'), findsOneWidget);    // FAB
  });
}
```

- [ ] **Step 2: Run the smoke test**

Run: `flutter test test/app_smoke_test.dart`
Expected: PASS.

- [ ] **Step 3: Run the analyzer**

Run: `flutter analyze`
Expected: "No issues found!" Fix any reported issues (unused imports, missing trailing commas) and re-run until clean.

- [ ] **Step 4: Run the full suite once more**

Run: `flutter test`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add test/app_smoke_test.dart
git commit -m "test: add full-app smoke test for logged-in flow"
```

---

## Notes for the implementer

- Run `dart run build_runner build --delete-conflicting-outputs` after any change to a Drift table or DAO annotation; the `*.g.dart` files are generated, never hand-edited.
- The `MockPipelineClient` is the only pipeline implementation in Milestone 1. Milestone 2 adds an `HttpPipelineClient implements PipelineClient` and overrides `pipelineClientProvider` — no UI or controller changes required.
- Firebase requires a real project (`flutterfire configure`) before auth works on a device; tests inject mocks and never hit the network.
- Background recording (foreground service) hardening is intentionally minimal here (the `record` package handles short backgrounding); robust long-session background service is a follow-up within Milestone 1 if field testing shows drops.

## Deliberate simplifications vs. spec (hardening follow-ups within Milestone 1)

These are scoped out of the task list above to keep the first cut shippable; each is a self-contained follow-up, not a redesign:

- **Pause/resume UI** (spec §6): `RecordingService` already exposes `pause()`/`resume()`; `RecordingControlScreen` wires only Stop. Adding a Pause/Resume button is a small UI follow-up — surface a toggle that calls the existing service methods.
- **Persistent upload queue + backoff** (spec §7): Task 19's `UploadController` uploads synchronously with manual retry (re-tap) and sets `failed` on error. The `workmanager` dependency is added but the persistent cross-restart queue with exponential backoff (30s → 2m → 10m) is a follow-up: wrap `UploadController.upload` in a WorkManager task keyed by `recordingId`, enqueued when offline and on `failed`.
- **Secure storage**: `driveRefreshToken` is omitted from `UserSettingsTable` because `google_sign_in` manages Drive credentials internally — the app never holds the raw refresh token, so `flutter_secure_storage` is unused in M1. Remove the dependency if no other secret appears, or keep it for M2's `HttpPipelineClient` auth.
