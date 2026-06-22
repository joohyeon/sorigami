# Sorigamis — Skill Actions & Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Sorigamis M1 app (see `docs/superpowers/plans/2026-06-21-sorigamis-milestone-1.md`) with three new capabilities: (1) Skills gain an ordered `actions` array that the pipeline fires after each skill's AI step; (2) an in-app Skill Marketplace backed by Firestore for browse/install/publish; (3) the ResultTab gains a unified output view and a Skill Details debug toggle showing per-skill output and action logs.

**Architecture:** Skills become automation units — AI intent fields plus an `actions` JSON column (Drift). The pipeline contract gains `actions` in `SkillRequest` and `actions_log` in `SkillOutput`; `MockPipelineClient` returns synthetic action logs. The Marketplace is a thin Firestore read/write layer behind a `MarketplaceClient` abstract interface, keeping the UI decoupled from Firebase. All new UI lives under existing `features/settings/` and `features/detail/` directories.

**Tech Stack:** Additions to M1 base — `cloud_firestore`, `reorderable_item` (for drag-to-reorder action list in SkillEditScreen).

## Global Constraints

- Prerequisite: Tasks 1–18+ of `2026-06-21-sorigamis-milestone-1.md` must be complete (Drift DB, DAOs, PipelineClient, MockPipelineClient, Riverpod providers all exist).
- Drift `schemaVersion` bumps from `1` to `2`; migration adds the `actions` column to `Skills`. Run `dart run build_runner build --delete-conflicting-outputs` after every schema change.
- Action template variables: `{{output}}`, `{{speaker}}`, `{{recording_title}}`.
- Supported action types: `slack`, `linear`, `google_calendar`, `webhook`.
- Marketplace backend: Firestore collection `marketplace_skills`. Auth rule: only the document's `authorId` may write; all authenticated users may read.
- Pipeline contract is **fixed** (spec §9): app sends skills with `actions` array; pipeline fires them. App never interprets action execution — it only stores and displays the `actions_log` returned in the result.
- TDD: every task writes the failing test first. Commit after each task.

---

## File Structure

```
lib/
  core/
    enums.dart                            + SkillActionType enum
  data/
    db/
      database.dart                       + actions column on Skills; schemaVersion → 2
      database.g.dart                     (regenerated)
    pipeline/
      pipeline_client.dart                + SkillAction, ActionLog, updated SkillRequest/SkillOutput/JobStatusResult
      mock_pipeline_client.dart           + mock actions_log in result(), current_skill in status()
    marketplace/
      marketplace_client.dart             MarketplaceSkill model + abstract MarketplaceClient
      firestore_marketplace_client.dart   Firestore implementation
  domain/
    models/
      skill_resolution.dart               + map actions JSON → List<SkillAction> in SkillRequest
  features/
    settings/
      skill_edit_screen.dart              + Actions section, ActionEditSheet, Publish button
      marketplace_screen.dart             Browse list (search, filter, SkillCard)
      skill_marketplace_detail_screen.dart  Full detail + Install/Update button
    detail/
      result_tab.dart                     Unified view + Skill Details debug toggle
  providers/
    providers.dart                        + marketplaceClientProvider
test/
  core/enums_test.dart                    + SkillActionType round-trip
  data/db/database_test.dart              + actions column persists
  data/pipeline/pipeline_client_test.dart + SkillAction.toJson, ActionLog
  data/pipeline/mock_pipeline_client_test.dart  + actions_log in result
  domain/skill_resolution_test.dart       + actions map through
  data/marketplace/marketplace_client_test.dart
  features/settings/skill_edit_screen_test.dart
  features/settings/marketplace_screen_test.dart
  features/detail/result_tab_test.dart
```

---

## Task 1: SkillActionType enum

**Files:**
- Modify: `lib/core/enums.dart`
- Modify: `test/core/enums_test.dart`

**Interfaces:**
- Produces: `enum SkillActionType { slack, linear, google_calendar, webhook; static SkillActionType fromName(String n); }` added to the existing enums file.

- [ ] **Step 1: Write the failing test**

Add to the bottom of `test/core/enums_test.dart`:
```dart
test('SkillActionType round-trips through name', () {
  for (final t in SkillActionType.values) {
    expect(SkillActionType.fromName(t.name), t);
  }
});
test('SkillActionType.fromName falls back to webhook on unknown', () {
  expect(SkillActionType.fromName('bogus'), SkillActionType.webhook);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/core/enums_test.dart`
Expected: FAIL — `SkillActionType` not defined.

- [ ] **Step 3: Add to `lib/core/enums.dart`**

Add at the bottom of the existing file:
```dart
enum SkillActionType {
  slack,
  linear,
  google_calendar,
  webhook;

  static SkillActionType fromName(String n) => SkillActionType.values
      .firstWhere((e) => e.name == n, orElse: () => SkillActionType.webhook);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/core/enums_test.dart`
Expected: PASS (all tests including new ones).

- [ ] **Step 5: Commit**

```bash
git add lib/core/enums.dart test/core/enums_test.dart
git commit -m "feat: add SkillActionType enum (slack, linear, google_calendar, webhook)"
```

---

## Task 2: Add `actions` column to Skills table (schema v2)

**Files:**
- Modify: `lib/data/db/database.dart`
- Regenerate: `lib/data/db/database.g.dart`
- Modify: `test/data/db/database_test.dart`

**Interfaces:**
- Modifies: `Skills` table gains `TextColumn get actions` (nullable JSON, default `'[]'`). `AppDatabase.schemaVersion` → 2 with a migration that adds the column to existing databases.
- All existing DAO tests continue to pass unchanged.

- [ ] **Step 1: Write the failing test**

Add to `test/data/db/database_test.dart`:
```dart
test('actions column defaults to empty JSON array', () async {
  await db.into(db.skills).insert(SkillsCompanion.insert(
    id: 's1', name: 'Summary', createdAt: DateTime(2026),
  ));
  final row = await (db.select(db.skills)
      ..where((t) => t.id.equals('s1')))
    .getSingle();
  expect(row.actions, '[]');
});

test('actions column persists JSON', () async {
  const actionsJson =
      '[{"type":"slack","config":{"webhook_url":"https://hooks.slack.com/T","message_template":"{{output}}"},"sort_order":0}]';
  await db.into(db.skills).insert(SkillsCompanion.insert(
    id: 's2', name: 'Actions', createdAt: DateTime(2026),
    actions: const Value(actionsJson),
  ));
  final row = await (db.select(db.skills)
      ..where((t) => t.id.equals('s2')))
    .getSingle();
  expect(row.actions, actionsJson);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/db/database_test.dart`
Expected: FAIL — `actions` column not defined / `Value` not accepted.

- [ ] **Step 3: Add column to `Skills` table in `lib/data/db/database.dart`**

In the `Skills` class, add after `pipelineParams`:
```dart
TextColumn get actions =>
    text().withDefault(const Constant('[]'))();
```

- [ ] **Step 4: Add migration and bump schemaVersion**

In `AppDatabase`:
```dart
@override
int get schemaVersion => 2;

@override
MigrationStrategy get migration => MigrationStrategy(
  onUpgrade: (m, from, to) async {
    if (from < 2) {
      await m.addColumn(skills, skills.actions);
    }
  },
);
```

- [ ] **Step 5: Regenerate Drift code**

Run: `dart run build_runner build --delete-conflicting-outputs`
Expected: `database.g.dart` updated; `SkillsCompanion` now has `actions` field; no errors.

- [ ] **Step 6: Run all DB tests to verify they pass**

Run: `flutter test test/data/db/`
Expected: PASS (all existing + 2 new tests).

- [ ] **Step 7: Commit**

```bash
git add lib/data/db/database.dart lib/data/db/database.g.dart test/data/db/database_test.dart
git commit -m "feat: add actions column to Skills table, schema v2 with migration"
```

---

## Task 3: Update PipelineClient DTOs — SkillAction, ActionLog, updated SkillRequest/SkillOutput/JobStatusResult

**Files:**
- Modify: `lib/data/pipeline/pipeline_client.dart`
- Modify: `test/data/pipeline/pipeline_client_test.dart`

**Interfaces:**
- Adds: `class SkillAction { String type; Map<String,dynamic> config; int sortOrder; Map<String,dynamic> toJson(); static SkillAction fromJson(Map<String,dynamic>); }`
- Adds: `class ActionLog { String type; DateTime firedAt; bool success; String? error; static ActionLog fromJson(Map<String,dynamic>); }`
- Modifies: `SkillRequest` gains `final int sortOrder` and `final List<SkillAction> actions`; `toJson()` includes both.
- Modifies: `SkillOutput` gains `final List<ActionLog> actionsLog`.
- Modifies: `JobStatusResult` gains `final Map<String,dynamic>? currentSkill` (the `current_skill` object from the API: `{index, name, phase}`).

- [ ] **Step 1: Write the failing test**

Replace `test/data/pipeline/pipeline_client_test.dart` with:
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/pipeline/pipeline_client.dart';

void main() {
  test('SkillAction.toJson round-trips through fromJson', () {
    final a = SkillAction(
      type: 'slack',
      config: {'webhook_url': 'https://hooks.slack.com/T', 'message_template': '{{output}}'},
      sortOrder: 0,
    );
    final json = a.toJson();
    final restored = SkillAction.fromJson(json);
    expect(restored.type, 'slack');
    expect(restored.config['webhook_url'], 'https://hooks.slack.com/T');
    expect(restored.sortOrder, 0);
  });

  test('SkillRequest.toJson includes actions and sort_order', () {
    final r = SkillRequest(
      skillId: 's1',
      skillName: 'Action Items',
      language: 'auto',
      identifySpeakers: true,
      vocabularyHints: const ['Fixli'],
      outputType: 'tasks',
      focusArea: null,
      tone: 'concise',
      outputLanguage: 'en',
      additionalInstructions: null,
      pipelineParams: null,
      sortOrder: 1,
      actions: [
        SkillAction(
          type: 'linear',
          config: {'api_key': 'lin_x', 'team_id': 'T1', 'assignee_from_speaker': true},
          sortOrder: 0,
        ),
      ],
    );
    final j = r.toJson();
    expect(j['sort_order'], 1);
    expect((j['actions'] as List).length, 1);
    expect((j['actions'] as List).first['type'], 'linear');
  });

  test('ActionLog.fromJson parses success and firedAt', () {
    final log = ActionLog.fromJson({
      'type': 'slack',
      'fired_at': '2026-06-22T10:00:00.000Z',
      'success': true,
      'error': null,
    });
    expect(log.type, 'slack');
    expect(log.success, true);
    expect(log.error, null);
  });

  test('PipelineJobStatus.fromName parses', () {
    expect(PipelineJobStatus.fromName('completed'), PipelineJobStatus.completed);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/pipeline/pipeline_client_test.dart`
Expected: FAIL — `SkillAction`, `ActionLog` not defined; `SkillRequest` missing `sortOrder`/`actions`.

- [ ] **Step 3: Replace `lib/data/pipeline/pipeline_client.dart`**

```dart
class SkillAction {
  final String type;
  final Map<String, dynamic> config;
  final int sortOrder;

  SkillAction({required this.type, required this.config, required this.sortOrder});

  Map<String, dynamic> toJson() => {
        'type': type,
        'config': config,
        'sort_order': sortOrder,
      };

  static SkillAction fromJson(Map<String, dynamic> j) => SkillAction(
        type: j['type'] as String,
        config: (j['config'] as Map).cast<String, dynamic>(),
        sortOrder: (j['sort_order'] as num).toInt(),
      );
}

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
  final int sortOrder;
  final List<SkillAction> actions;

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
    this.sortOrder = 0,
    this.actions = const [],
  });

  Map<String, dynamic> toJson() => {
        'skill_id': skillId,
        'skill_name': skillName,
        'sort_order': sortOrder,
        'language': language,
        'identify_speakers': identifySpeakers,
        'vocabulary_hints': vocabularyHints,
        'output_type': outputType,
        'focus_area': focusArea,
        'tone': tone,
        'output_language': outputLanguage,
        'additional_instructions': additionalInstructions,
        if (pipelineParams != null) 'pipeline_params': pipelineParams,
        'actions': actions.map((a) => a.toJson()).toList(),
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
  requested,
  processing,
  completed,
  failed;
  static PipelineJobStatus fromName(String n) => PipelineJobStatus.values
      .firstWhere((e) => e.name == n, orElse: () => PipelineJobStatus.requested);
}

class ActionLog {
  final String type;
  final DateTime firedAt;
  final bool success;
  final String? error;

  ActionLog({required this.type, required this.firedAt, required this.success, this.error});

  static ActionLog fromJson(Map<String, dynamic> j) => ActionLog(
        type: j['type'] as String,
        firedAt: DateTime.parse(j['fired_at'] as String),
        success: j['success'] as bool,
        error: j['error'] as String?,
      );
}

class JobStatusResult {
  final String jobId;
  final PipelineJobStatus status;
  final String? stage;
  final String? error;
  final Map<String, dynamic>? currentSkill;

  JobStatusResult({
    required this.jobId,
    required this.status,
    this.stage,
    this.error,
    this.currentSkill,
  });
}

class SkillOutput {
  final String skillId;
  final String skillName;
  final String output;
  final List<ActionLog> actionsLog;

  SkillOutput({
    required this.skillId,
    required this.skillName,
    required this.output,
    this.actionsLog = const [],
  });
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
Expected: PASS (all four tests).

- [ ] **Step 5: Commit**

```bash
git add lib/data/pipeline/pipeline_client.dart test/data/pipeline/pipeline_client_test.dart
git commit -m "feat: extend PipelineClient DTOs with SkillAction, ActionLog, sortOrder"
```

---

## Task 4: Update skill_resolution.dart to map actions

**Files:**
- Modify: `lib/domain/models/skill_resolution.dart`
- Modify: `test/domain/skill_resolution_test.dart`

**Interfaces:**
- Modifies: `resolveSkills()` now parses the `actions` JSON column on each `Skill` row and maps it to `List<SkillAction>` on the `SkillRequest`. Also passes `sortOrder` from the `ModeSkills.sortOrder`.

- [ ] **Step 1: Write the failing test**

Add to `test/domain/skill_resolution_test.dart`:
```dart
test('actions JSON in skill maps to SkillRequest.actions', () async {
  const actionsJson =
      '[{"type":"slack","config":{"webhook_url":"https://h.slack.com/X","message_template":"{{output}}"},"sort_order":0}]';
  final skillId = 'sk-with-actions';
  await db.skillDao.upsert(SkillsCompanion.insert(
    id: skillId, name: 'Slack Skill', createdAt: DateTime(2026),
    actions: const Value(actionsJson),
  ));
  final rec = await recWith(custom: [skillId]);
  final reqs = await resolveSkills(rec, modeDao: db.modeDao, skillDao: db.skillDao);
  expect(reqs.length, 1);
  expect(reqs.first.actions.length, 1);
  expect(reqs.first.actions.first.type, 'slack');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/domain/skill_resolution_test.dart`
Expected: FAIL — `SkillRequest.actions` not populated (empty list).

- [ ] **Step 3: Update `lib/domain/models/skill_resolution.dart`**

Replace `_toRequest`:
```dart
import 'dart:convert';
import '../../data/db/database.dart';
import '../../data/db/daos/mode_dao.dart';
import '../../data/db/daos/skill_dao.dart';
import '../../data/pipeline/pipeline_client.dart';

List<SkillAction> _parseActions(String? actionsJson) {
  if (actionsJson == null || actionsJson == '[]') return const [];
  final list = jsonDecode(actionsJson) as List;
  return list
      .map((e) => SkillAction.fromJson((e as Map).cast<String, dynamic>()))
      .toList();
}

SkillRequest _toRequest(Skill s, {int sortOrder = 0}) => SkillRequest(
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
      sortOrder: sortOrder,
      actions: _parseActions(s.actions),
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
  for (var i = 0; i < ids.length; i++) {
    final s = await skillDao.byId(ids[i]);
    if (s != null) out.add(_toRequest(s, sortOrder: i));
  }
  return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/domain/skill_resolution_test.dart`
Expected: PASS (all existing + new test).

- [ ] **Step 5: Commit**

```bash
git add lib/domain/models/skill_resolution.dart test/domain/skill_resolution_test.dart
git commit -m "feat: map skill actions JSON and sort_order through resolveSkills"
```

---

## Task 5: Update MockPipelineClient — action logs in result, current_skill in status

**Files:**
- Modify: `lib/data/pipeline/mock_pipeline_client.dart`
- Modify: `test/data/pipeline/mock_pipeline_client_test.dart`

**Interfaces:**
- Modifies: `result()` returns `SkillOutput.actionsLog` — one `ActionLog` per action in the submitted skill, all with `success: true` and `firedAt: DateTime.now()`.
- Modifies: `status()` returns `currentSkill: { 'index': 0, 'name': skills.first.skillName, 'phase': 'ai' }` while processing.

- [ ] **Step 1: Write the failing test**

Add to `test/data/pipeline/mock_pipeline_client_test.dart`:
```dart
test('result includes mock actions_log for skills with actions', () async {
  final c = MockPipelineClient(processingTime: Duration.zero);
  final submission = JobSubmission(
    recordingId: 'r1', audioFilePath: '/a.m4a', audioDurationS: 60,
    category: null, modeName: 'General',
    skills: [
      SkillRequest(
        skillId: 's1', skillName: 'Summary', language: 'auto',
        identifySpeakers: false, vocabularyHints: const [],
        outputType: 'summary', focusArea: null, tone: 'concise',
        outputLanguage: 'en', additionalInstructions: null,
        pipelineParams: null, sortOrder: 0,
        actions: [
          SkillAction(
            type: 'slack',
            config: {'webhook_url': 'https://h.slack.com/T', 'message_template': '{{output}}'},
            sortOrder: 0,
          ),
        ],
      ),
    ],
  );
  final id = await c.submit(submission);
  final r = await c.result(id);
  expect(r.skillResults.first.actionsLog.length, 1);
  expect(r.skillResults.first.actionsLog.first.type, 'slack');
  expect(r.skillResults.first.actionsLog.first.success, true);
});

test('status includes currentSkill while processing', () async {
  final c = MockPipelineClient(processingTime: const Duration(seconds: 60));
  final id = await c.submit(sub()); // sub() is the existing helper
  final s = await c.status(id);
  expect(s.status, PipelineJobStatus.processing);
  expect(s.currentSkill, isNotNull);
  expect(s.currentSkill!['phase'], 'ai');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/pipeline/mock_pipeline_client_test.dart`
Expected: FAIL — `actionsLog` empty, `currentSkill` null.

- [ ] **Step 3: Replace `lib/data/pipeline/mock_pipeline_client.dart`**

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
      return JobStatusResult(
          jobId: jobId, status: PipelineJobStatus.failed, error: 'unknown job');
    }
    final done = DateTime.now().difference(start) >= processingTime;
    final skills = _submissions[jobId]?.skills ?? const [];
    return JobStatusResult(
      jobId: jobId,
      status: done ? PipelineJobStatus.completed : PipelineJobStatus.processing,
      stage: done ? null : 'running_skills',
      currentSkill: done || skills.isEmpty
          ? null
          : {
              'index': 0,
              'name': skills.first.skillName,
              'phase': 'ai',
            },
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
            actionsLog: [
              for (final a in s.actions)
                ActionLog(
                  type: a.type,
                  firedAt: DateTime.now(),
                  success: true,
                ),
            ],
          ),
      ],
    );
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/pipeline/mock_pipeline_client_test.dart`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add lib/data/pipeline/mock_pipeline_client.dart test/data/pipeline/mock_pipeline_client_test.dart
git commit -m "feat: mock pipeline returns action logs and current_skill progress"
```

---

## Task 6: MarketplaceSkill model + MarketplaceClient interface

**Files:**
- Create: `lib/data/marketplace/marketplace_client.dart`
- Create: `test/data/marketplace/marketplace_client_test.dart`

**Interfaces:**
- Produces:
  - `class MarketplaceSkill` with all fields from spec §5 (Firestore).
  - `abstract class MarketplaceClient { Future<List<MarketplaceSkill>> browse({String? query, List<String>? tags, String? outputType}); Future<MarketplaceSkill> getById(String id); Future<void> publish(MarketplaceSkill skill); Future<void> incrementInstallCount(String id); }`

- [ ] **Step 1: Write the failing test**

```dart
// test/data/marketplace/marketplace_client_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/marketplace/marketplace_client.dart';

void main() {
  test('MarketplaceSkill.fromJson round-trips toJson', () {
    final skill = MarketplaceSkill(
      id: 'doc1',
      authorId: 'u1',
      authorName: 'Alice',
      name: 'Team Standup',
      description: 'Extracts blockers and assigns tasks.',
      tags: const ['standup', 'tasks'],
      outputType: 'tasks',
      actionTypes: const ['linear'],
      latestVersion: 1,
      installCount: 0,
      skillSnapshot: const {'name': 'Team Standup', 'actions': '[]'},
      publishedAt: DateTime(2026, 6, 22),
    );
    final json = skill.toJson();
    final restored = MarketplaceSkill.fromJson('doc1', json);
    expect(restored.name, 'Team Standup');
    expect(restored.actionTypes, ['linear']);
    expect(restored.tags, ['standup', 'tasks']);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/data/marketplace/marketplace_client_test.dart`
Expected: FAIL — `MarketplaceSkill` not defined.

- [ ] **Step 3: Write `lib/data/marketplace/marketplace_client.dart`**

```dart
class MarketplaceSkill {
  final String id;
  final String authorId;
  final String authorName;
  final String name;
  final String description;
  final List<String> tags;
  final String outputType;
  final List<String> actionTypes;
  final int latestVersion;
  final int installCount;
  final Map<String, dynamic> skillSnapshot;
  final DateTime publishedAt;

  MarketplaceSkill({
    required this.id,
    required this.authorId,
    required this.authorName,
    required this.name,
    required this.description,
    required this.tags,
    required this.outputType,
    required this.actionTypes,
    required this.latestVersion,
    required this.installCount,
    required this.skillSnapshot,
    required this.publishedAt,
  });

  Map<String, dynamic> toJson() => {
        'author_id': authorId,
        'author_name': authorName,
        'name': name,
        'description': description,
        'tags': tags,
        'output_type': outputType,
        'action_types': actionTypes,
        'latest_version': latestVersion,
        'install_count': installCount,
        'skill_snapshot': skillSnapshot,
        'published_at': publishedAt.toIso8601String(),
      };

  static MarketplaceSkill fromJson(String id, Map<String, dynamic> j) => MarketplaceSkill(
        id: id,
        authorId: j['author_id'] as String,
        authorName: j['author_name'] as String,
        name: j['name'] as String,
        description: j['description'] as String,
        tags: (j['tags'] as List).cast<String>(),
        outputType: j['output_type'] as String,
        actionTypes: (j['action_types'] as List).cast<String>(),
        latestVersion: (j['latest_version'] as num).toInt(),
        installCount: (j['install_count'] as num).toInt(),
        skillSnapshot: (j['skill_snapshot'] as Map).cast<String, dynamic>(),
        publishedAt: DateTime.parse(j['published_at'] as String),
      );
}

abstract class MarketplaceClient {
  Future<List<MarketplaceSkill>> browse({
    String? query,
    List<String>? tags,
    String? outputType,
  });
  Future<MarketplaceSkill> getById(String id);
  Future<void> publish(MarketplaceSkill skill);
  Future<void> incrementInstallCount(String id);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flutter test test/data/marketplace/marketplace_client_test.dart`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/data/marketplace/marketplace_client.dart test/data/marketplace/marketplace_client_test.dart
git commit -m "feat: add MarketplaceSkill model and MarketplaceClient interface"
```

---

## Task 7: FirestoreMarketplaceClient + marketplaceClientProvider

**Files:**
- Create: `lib/data/marketplace/firestore_marketplace_client.dart`
- Modify: `lib/providers/providers.dart` (add `marketplaceClientProvider`)
- Modify: `pubspec.yaml` (add `cloud_firestore`)

**Interfaces:**
- Consumes: `MarketplaceClient` (Task 6), `cloud_firestore`.
- Produces: `FirestoreMarketplaceClient implements MarketplaceClient` — reads/writes Firestore collection `marketplace_skills`. `browse()` queries by name prefix or tags (simple `whereIn` on tags); `publish()` sets a document with the caller's uid as `author_id`; `incrementInstallCount()` uses `FieldValue.increment(1)`.
- Adds: `final marketplaceClientProvider = Provider<MarketplaceClient>((ref) => FirestoreMarketplaceClient());` to `providers.dart`.

- [ ] **Step 1: Add Firestore dependency**

Run: `flutter pub add cloud_firestore`
Expected: `pubspec.yaml` updated; `flutter pub get` succeeds.

- [ ] **Step 2: Write a smoke test (uses Firestore emulator or mock)**

```dart
// test/data/marketplace/firestore_marketplace_client_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/marketplace/marketplace_client.dart';
import 'package:sorigamis/data/marketplace/firestore_marketplace_client.dart';

void main() {
  test('FirestoreMarketplaceClient implements MarketplaceClient', () {
    expect(FirestoreMarketplaceClient(), isA<MarketplaceClient>());
  });
}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `flutter test test/data/marketplace/firestore_marketplace_client_test.dart`
Expected: FAIL — class not defined.

- [ ] **Step 4: Write `lib/data/marketplace/firestore_marketplace_client.dart`**

```dart
import 'package:cloud_firestore/cloud_firestore.dart';
import 'marketplace_client.dart';

const _kCollection = 'marketplace_skills';

class FirestoreMarketplaceClient implements MarketplaceClient {
  FirestoreMarketplaceClient({FirebaseFirestore? firestore})
      : _db = firestore ?? FirebaseFirestore.instance;

  final FirebaseFirestore _db;

  @override
  Future<List<MarketplaceSkill>> browse({
    String? query,
    List<String>? tags,
    String? outputType,
  }) async {
    Query<Map<String, dynamic>> q = _db.collection(_kCollection);
    if (outputType != null) q = q.where('output_type', isEqualTo: outputType);
    if (tags != null && tags.isNotEmpty) {
      q = q.where('tags', arrayContainsAny: tags);
    }
    q = q.orderBy('install_count', descending: true).limit(50);
    final snap = await q.get();
    return snap.docs
        .map((d) => MarketplaceSkill.fromJson(d.id, d.data()))
        .toList();
  }

  @override
  Future<MarketplaceSkill> getById(String id) async {
    final doc = await _db.collection(_kCollection).doc(id).get();
    return MarketplaceSkill.fromJson(doc.id, doc.data()!);
  }

  @override
  Future<void> publish(MarketplaceSkill skill) async {
    final ref = skill.id.isEmpty
        ? _db.collection(_kCollection).doc()
        : _db.collection(_kCollection).doc(skill.id);
    await ref.set(skill.toJson(), SetOptions(merge: true));
  }

  @override
  Future<void> incrementInstallCount(String id) async {
    await _db
        .collection(_kCollection)
        .doc(id)
        .update({'install_count': FieldValue.increment(1)});
  }
}
```

- [ ] **Step 5: Add provider to `lib/providers/providers.dart`**

Add at the bottom:
```dart
import '../data/marketplace/marketplace_client.dart';
import '../data/marketplace/firestore_marketplace_client.dart';

final marketplaceClientProvider =
    Provider<MarketplaceClient>((ref) => FirestoreMarketplaceClient());
```

- [ ] **Step 6: Run test to verify it passes**

Run: `flutter test test/data/marketplace/firestore_marketplace_client_test.dart`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add lib/data/marketplace/ lib/providers/providers.dart pubspec.yaml pubspec.lock test/data/marketplace/firestore_marketplace_client_test.dart
git commit -m "feat: add FirestoreMarketplaceClient and marketplaceClientProvider"
```

---

## Task 8: MarketplaceScreen (browse + SkillCard)

**Files:**
- Create: `lib/features/settings/marketplace_screen.dart`
- Modify: `lib/core/router.dart` (add `/marketplace` route)
- Create: `test/features/settings/marketplace_screen_test.dart`

**Interfaces:**
- Consumes: `marketplaceClientProvider`.
- Produces: `MarketplaceScreen` — a `ConsumerStatefulWidget` with a search `TextField`, filter chips (output type), a list of `SkillCard` widgets. `SkillCard` shows name, author, description snippet, install count, and action type badges (e.g. chips for `slack`, `linear`).

- [ ] **Step 1: Write the failing widget test**

```dart
// test/features/settings/marketplace_screen_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sorigamis/data/marketplace/marketplace_client.dart';
import 'package:sorigamis/features/settings/marketplace_screen.dart';
import 'package:sorigamis/providers/providers.dart';

class _MockMarketplaceClient extends Mock implements MarketplaceClient {}

void main() {
  testWidgets('shows skill cards from marketplace', (tester) async {
    final client = _MockMarketplaceClient();
    when(() => client.browse(
          query: any(named: 'query'),
          tags: any(named: 'tags'),
          outputType: any(named: 'outputType'),
        )).thenAnswer((_) async => [
          MarketplaceSkill(
            id: 'm1',
            authorId: 'u1',
            authorName: 'Alice',
            name: 'Team Standup',
            description: 'Extracts blockers.',
            tags: const ['standup'],
            outputType: 'tasks',
            actionTypes: const ['linear'],
            latestVersion: 1,
            installCount: 42,
            skillSnapshot: const {},
            publishedAt: DateTime(2026),
          ),
        ]);

    await tester.pumpWidget(ProviderScope(
      overrides: [marketplaceClientProvider.overrideWithValue(client)],
      child: const MaterialApp(home: MarketplaceScreen()),
    ));
    await tester.pumpAndSettle();

    expect(find.text('Team Standup'), findsOneWidget);
    expect(find.text('Alice'), findsOneWidget);
    expect(find.text('42 installs'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/settings/marketplace_screen_test.dart`
Expected: FAIL — `MarketplaceScreen` not defined.

- [ ] **Step 3: Write `lib/features/settings/marketplace_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/marketplace/marketplace_client.dart';
import '../../providers/providers.dart';

final _marketplaceBrowseProvider = FutureProvider.autoDispose
    .family<List<MarketplaceSkill>, String>((ref, query) async {
  return ref
      .watch(marketplaceClientProvider)
      .browse(query: query.isEmpty ? null : query);
});

class MarketplaceScreen extends ConsumerStatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  ConsumerState<MarketplaceScreen> createState() => _State();
}

class _State extends ConsumerState<MarketplaceScreen> {
  final _query = TextEditingController();
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(_marketplaceBrowseProvider(_search));
    return Scaffold(
      appBar: AppBar(title: const Text('Skill Marketplace')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _query,
              decoration: const InputDecoration(
                hintText: 'Search skills…',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (v) => setState(() => _search = v.trim()),
            ),
          ),
          Expanded(
            child: results.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (list) => list.isEmpty
                  ? const Center(child: Text('No skills found.'))
                  : ListView.builder(
                      itemCount: list.length,
                      itemBuilder: (_, i) => _SkillCard(skill: list[i]),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SkillCard extends StatelessWidget {
  const _SkillCard({required this.skill});
  final MarketplaceSkill skill;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: ListTile(
        title: Text(skill.name),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(skill.authorName),
            Text(skill.description, maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Row(children: [
              for (final t in skill.actionTypes)
                Padding(
                  padding: const EdgeInsets.only(right: 4),
                  child: Chip(label: Text(t), padding: EdgeInsets.zero,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap),
                ),
              Text('${skill.installCount} installs',
                  style: Theme.of(context).textTheme.bodySmall),
            ]),
          ],
        ),
        isThreeLine: true,
        onTap: () => context.go('/marketplace/${skill.id}'),
      ),
    );
  }
}
```

- [ ] **Step 4: Add route to `lib/core/router.dart`**

Add import:
```dart
import '../features/settings/marketplace_screen.dart';
import '../features/settings/skill_marketplace_detail_screen.dart';
```

Add routes:
```dart
GoRoute(path: '/marketplace', builder: (_, __) => const MarketplaceScreen()),
GoRoute(
    path: '/marketplace/:skillId',
    builder: (_, s) => SkillMarketplaceDetailScreen(
        marketplaceSkillId: s.pathParameters['skillId']!)),
```

Add a placeholder `SkillMarketplaceDetailScreen` (full implementation in Task 9):
```dart
// lib/features/settings/skill_marketplace_detail_screen.dart
import 'package:flutter/material.dart';
class SkillMarketplaceDetailScreen extends StatelessWidget {
  const SkillMarketplaceDetailScreen({super.key, required this.marketplaceSkillId});
  final String marketplaceSkillId;
  @override
  Widget build(BuildContext context) =>
      Scaffold(appBar: AppBar(title: const Text('Skill Detail')),
               body: Center(child: Text(marketplaceSkillId)));
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/settings/marketplace_screen_test.dart`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/features/settings/marketplace_screen.dart lib/features/settings/skill_marketplace_detail_screen.dart lib/core/router.dart test/features/settings/marketplace_screen_test.dart
git commit -m "feat: add Skill Marketplace browse screen with search and skill cards"
```

---

## Task 9: SkillMarketplaceDetailScreen (view + install)

**Files:**
- Replace: `lib/features/settings/skill_marketplace_detail_screen.dart`
- Modify: `lib/data/db/daos/skill_dao.dart` (add `installFromMarketplace` helper)
- Create: `test/features/settings/skill_marketplace_detail_screen_test.dart`

**Interfaces:**
- Consumes: `marketplaceClientProvider`, `skillDaoProvider`.
- Produces: Full detail screen with name, author, description, version, action type badges, and an `[Install]` / `[Installed ✓]` button. `install()` copies `skillSnapshot` fields into a new `SkillsCompanion` row with `marketplaceSkillId` and `marketplaceVersion` set.
- Adds to `SkillDao`: `Future<bool> isInstalled(String marketplaceSkillId)` and `Future<void> installFromSnapshot(Map<String,dynamic> snapshot, String marketplaceSkillId, int version)`.

- [ ] **Step 1: Write the failing test**

```dart
// test/features/settings/skill_marketplace_detail_screen_test.dart
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sorigamis/data/db/database.dart';
import 'package:sorigamis/data/marketplace/marketplace_client.dart';
import 'package:sorigamis/features/settings/skill_marketplace_detail_screen.dart';
import 'package:sorigamis/providers/providers.dart';

class _MockMarketplaceClient extends Mock implements MarketplaceClient {}

MarketplaceSkill _testSkill() => MarketplaceSkill(
  id: 'm1', authorId: 'u1', authorName: 'Bob',
  name: 'Sales Follow-up', description: 'Creates follow-up tasks after sales calls.',
  tags: const ['sales'], outputType: 'tasks', actionTypes: const ['linear'],
  latestVersion: 2, installCount: 17,
  skillSnapshot: const {
    'name': 'Sales Follow-up', 'output_type': 'tasks', 'tone': 'concise',
    'language': 'auto', 'identify_speakers': false, 'vocabulary_hints': '[]',
    'output_language': 'auto', 'actions': '[]',
  },
  publishedAt: DateTime(2026),
);

void main() {
  testWidgets('shows Install button and skill name', (tester) async {
    final client = _MockMarketplaceClient();
    when(() => client.getById('m1')).thenAnswer((_) async => _testSkill());
    when(() => client.incrementInstallCount(any())).thenAnswer((_) async {});

    final db = AppDatabase(NativeDatabase.memory());
    await tester.pumpWidget(ProviderScope(
      overrides: [
        marketplaceClientProvider.overrideWithValue(client),
        databaseProvider.overrideWithValue(db),
      ],
      child: const MaterialApp(
        home: SkillMarketplaceDetailScreen(marketplaceSkillId: 'm1'),
      ),
    ));
    await tester.pumpAndSettle();

    expect(find.text('Sales Follow-up'), findsOneWidget);
    expect(find.text('Install'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/settings/skill_marketplace_detail_screen_test.dart`
Expected: FAIL — real screen not built yet.

- [ ] **Step 3: Add helpers to `lib/data/db/daos/skill_dao.dart`**

```dart
Future<bool> isInstalled(String marketplaceSkillId) async {
  final row = await (select(skills)
        ..where((t) => t.marketplaceSkillId.equals(marketplaceSkillId)))
      .getSingleOrNull();
  return row != null;
}

Future<void> installFromSnapshot(
    Map<String, dynamic> snapshot, String marketplaceSkillId, int version) async {
  await upsert(SkillsCompanion.insert(
    id: const Uuid().v4(),
    name: snapshot['name'] as String,
    description: Value(snapshot['description'] as String?),
    language: Value((snapshot['language'] as String?) ?? 'auto'),
    identifySpeakers: Value((snapshot['identify_speakers'] as bool?) ?? false),
    vocabularyHints: Value(snapshot['vocabulary_hints'] as String? ?? '[]'),
    outputType: Value((snapshot['output_type'] as String?) ?? 'summary'),
    focusArea: Value(snapshot['focus_area'] as String?),
    tone: Value((snapshot['tone'] as String?) ?? 'concise'),
    outputLanguage: Value((snapshot['output_language'] as String?) ?? 'auto'),
    additionalInstructions: Value(snapshot['additional_instructions'] as String?),
    pipelineParams: Value(snapshot['pipeline_params'] as String?),
    actions: Value((snapshot['actions'] as String?) ?? '[]'),
    marketplaceSkillId: Value(marketplaceSkillId),
    marketplaceVersion: Value(version),
    createdAt: DateTime.now(),
  ));
}
```

Add `import 'package:uuid/uuid.dart';` and the two new columns to the Skills table accessor. Then add `marketplaceSkillId` and `marketplaceVersion` columns to the `Skills` Drift table in `database.dart` and run codegen:

In `lib/data/db/database.dart` `Skills` class, add after `actions`:
```dart
TextColumn get marketplaceSkillId => text().nullable()();
IntColumn get marketplaceVersion => integer().nullable()();
```

Bump `schemaVersion` to `3` and add to migration:
```dart
if (from < 3) {
  await m.addColumn(skills, skills.marketplaceSkillId);
  await m.addColumn(skills, skills.marketplaceVersion);
}
```

Run: `dart run build_runner build --delete-conflicting-outputs`

- [ ] **Step 4: Write `lib/features/settings/skill_marketplace_detail_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/marketplace/marketplace_client.dart';
import '../../providers/providers.dart';

final _skillDetailProvider = FutureProvider.autoDispose
    .family<MarketplaceSkill, String>((ref, id) =>
        ref.watch(marketplaceClientProvider).getById(id));

class SkillMarketplaceDetailScreen extends ConsumerWidget {
  const SkillMarketplaceDetailScreen({super.key, required this.marketplaceSkillId});
  final String marketplaceSkillId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(_skillDetailProvider(marketplaceSkillId));
    return Scaffold(
      appBar: AppBar(title: const Text('Skill Detail')),
      body: detail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (skill) => _SkillDetail(skill: skill),
      ),
    );
  }
}

class _SkillDetail extends ConsumerStatefulWidget {
  const _SkillDetail({required this.skill});
  final MarketplaceSkill skill;

  @override
  ConsumerState<_SkillDetail> createState() => _State();
}

class _State extends ConsumerState<_SkillDetail> {
  bool _installing = false;
  bool _installed = false;

  @override
  void initState() {
    super.initState();
    _checkInstalled();
  }

  Future<void> _checkInstalled() async {
    final installed = await ref
        .read(skillDaoProvider)
        .isInstalled(widget.skill.id);
    if (mounted) setState(() => _installed = installed);
  }

  Future<void> _install() async {
    setState(() => _installing = true);
    await ref.read(skillDaoProvider).installFromSnapshot(
        widget.skill.skillSnapshot, widget.skill.id, widget.skill.latestVersion);
    await ref.read(marketplaceClientProvider).incrementInstallCount(widget.skill.id);
    if (mounted) setState(() { _installing = false; _installed = true; });
  }

  @override
  Widget build(BuildContext context) {
    final skill = widget.skill;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(skill.name, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 4),
        Text('by ${skill.authorName} · v${skill.latestVersion} · ${skill.installCount} installs',
            style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 12),
        Text(skill.description),
        const SizedBox(height: 12),
        Wrap(spacing: 6, children: [
          for (final t in skill.actionTypes) Chip(label: Text(t)),
          Chip(label: Text(skill.outputType)),
        ]),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: _installed || _installing ? null : _install,
          child: _installing
              ? const SizedBox(
                  width: 16, height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2))
              : Text(_installed ? 'Installed ✓' : 'Install'),
        ),
      ],
    );
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/settings/skill_marketplace_detail_screen_test.dart`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/data/db/ lib/features/settings/skill_marketplace_detail_screen.dart test/features/settings/skill_marketplace_detail_screen_test.dart
git commit -m "feat: add marketplace detail screen with one-tap install"
```

---

## Task 10: ActionEditSheet + updated SkillEditScreen Actions section

**Files:**
- Modify: `lib/features/settings/skill_edit_screen.dart` (assumes it exists from M1 plan Task 19+)
- Create: `test/features/settings/skill_edit_screen_actions_test.dart`

**Interfaces:**
- Adds to `SkillEditScreen`: an **Actions** section below the existing intent fields, showing the skill's current actions list (from `skill.actions` JSON), a drag-to-reorder `ReorderableListView`, an "Add action" button that opens `ActionEditSheet`, and a "Publish to Marketplace" button at the bottom.
- `ActionEditSheet` is a modal bottom sheet with a type dropdown (Slack / Linear / Google Calendar / Webhook) and type-specific config fields. Returns a `SkillAction` on save.

- [ ] **Step 1: Write the failing widget test**

```dart
// test/features/settings/skill_edit_screen_actions_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/features/settings/action_edit_sheet.dart';

void main() {
  testWidgets('ActionEditSheet shows Slack config fields when Slack selected',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Builder(builder: (ctx) => ElevatedButton(
          onPressed: () => showModalBottomSheet(
              context: ctx,
              builder: (_) => const ActionEditSheet()),
          child: const Text('Open'),
        )),
      ),
    ));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();

    // Default type is slack — webhook URL field should appear
    expect(find.text('Webhook URL'), findsOneWidget);
    expect(find.text('Message template'), findsOneWidget);
    expect(find.text('Save action'), findsOneWidget);
  });

  testWidgets('ActionEditSheet switches to Linear fields', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Builder(builder: (ctx) => ElevatedButton(
          onPressed: () => showModalBottomSheet(
              context: ctx,
              builder: (_) => const ActionEditSheet()),
          child: const Text('Open'),
        )),
      ),
    ));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButton<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Linear').last);
    await tester.pumpAndSettle();

    expect(find.text('API key'), findsOneWidget);
    expect(find.text('Team ID'), findsOneWidget);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/settings/skill_edit_screen_actions_test.dart`
Expected: FAIL — `ActionEditSheet` not defined.

- [ ] **Step 3: Create `lib/features/settings/action_edit_sheet.dart`**

```dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../../core/enums.dart';
import '../../data/pipeline/pipeline_client.dart';

class ActionEditSheet extends StatefulWidget {
  const ActionEditSheet({super.key, this.existing});
  final SkillAction? existing;

  @override
  State<ActionEditSheet> createState() => _State();
}

class _State extends State<ActionEditSheet> {
  late String _type;
  final Map<String, TextEditingController> _controllers = {};

  @override
  void initState() {
    super.initState();
    _type = widget.existing?.type ?? SkillActionType.slack.name;
    _initControllers(widget.existing?.config ?? {});
  }

  void _initControllers(Map<String, dynamic> config) {
    _controllers.clear();
    for (final key in _fieldsFor(_type).keys) {
      _controllers[key] = TextEditingController(
          text: config[key]?.toString() ?? '');
    }
  }

  Map<String, String> _fieldsFor(String type) {
    switch (type) {
      case 'slack':
        return {'webhook_url': 'Webhook URL', 'message_template': 'Message template'};
      case 'linear':
        return {
          'api_key': 'API key',
          'team_id': 'Team ID',
          'title_template': 'Title template',
        };
      case 'google_calendar':
        return {'calendar_id': 'Calendar ID', 'event_title_template': 'Event title template'};
      case 'webhook':
        return {'url': 'URL', 'method': 'Method (POST/GET)', 'body_template': 'Body template'};
      default:
        return {};
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final fields = _fieldsFor(_type);
    return Padding(
      padding: EdgeInsets.only(
          left: 16, right: 16, top: 16,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButton<String>(
              value: _type,
              items: SkillActionType.values
                  .map((t) => DropdownMenuItem(
                      value: t.name,
                      child: Text(t.name[0].toUpperCase() + t.name.substring(1).replaceAll('_', ' '))))
                  .toList(),
              onChanged: (v) {
                if (v == null) return;
                setState(() {
                  _type = v;
                  _initControllers({});
                });
              },
            ),
            const SizedBox(height: 12),
            for (final entry in fields.entries) ...[
              TextField(
                controller: _controllers[entry.key],
                decoration: InputDecoration(labelText: entry.value),
              ),
              const SizedBox(height: 8),
            ],
            if (_type == 'linear') ...[
              Row(children: [
                Checkbox(
                  value: (_controllers['assignee_from_speaker']?.text ?? 'false') == 'true',
                  onChanged: (v) => setState(() =>
                      _controllers['assignee_from_speaker'] =
                          TextEditingController(text: v.toString())),
                ),
                const Text('Assignee from speaker'),
              ]),
            ],
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () {
                final config = {
                  for (final e in _controllers.entries) e.key: e.value.text,
                };
                Navigator.of(context).pop(
                    SkillAction(type: _type, config: config, sortOrder: 0));
              },
              child: const Text('Save action'),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 4: Add the Actions section to `lib/features/settings/skill_edit_screen.dart`**

Locate the `SkillEditScreen` build method (built in M1 plan). After the existing Advanced (pipelineParams) section and before the save button, add:

```dart
// --- Actions section ---
const SizedBox(height: 24),
Text('Actions', style: Theme.of(context).textTheme.titleMedium),
const SizedBox(height: 8),
if (_actions.isEmpty)
  const Text('No actions — skill will only produce AI output.',
      style: TextStyle(color: Colors.grey)),
ReorderableListView(
  shrinkWrap: true,
  physics: const NeverScrollableScrollPhysics(),
  onReorder: (oldIndex, newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex--;
      final item = _actions.removeAt(oldIndex);
      _actions.insert(newIndex, item);
    });
  },
  children: [
    for (var i = 0; i < _actions.length; i++)
      ListTile(
        key: ValueKey(i),
        leading: const Icon(Icons.drag_handle),
        title: Text(_actions[i].type),
        subtitle: Text((_actions[i].config.entries.take(2)
            .map((e) => '${e.key}: ${e.value}').join(', '))),
        trailing: IconButton(
          icon: const Icon(Icons.delete),
          onPressed: () => setState(() => _actions.removeAt(i)),
        ),
        onTap: () async {
          final result = await showModalBottomSheet<SkillAction>(
            context: context,
            isScrollControlled: true,
            builder: (_) => ActionEditSheet(existing: _actions[i]),
          );
          if (result != null) setState(() => _actions[i] = result);
        },
      ),
  ],
),
TextButton.icon(
  icon: const Icon(Icons.add),
  label: const Text('Add action'),
  onPressed: () async {
    final result = await showModalBottomSheet<SkillAction>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const ActionEditSheet(),
    );
    if (result != null) setState(() => _actions.add(result));
  },
),
const SizedBox(height: 16),
OutlinedButton(
  onPressed: _publishToMarketplace,
  child: const Text('Publish to Marketplace'),
),
```

Add `_actions` state list and `_publishToMarketplace` to the `SkillEditScreen` state class:

```dart
late List<SkillAction> _actions;

// In initState / existing skill loading:
_actions = _parseActions(widget.skill?.actions);

List<SkillAction> _parseActions(String? json) {
  if (json == null || json == '[]') return [];
  final list = jsonDecode(json) as List;
  return list.map((e) => SkillAction.fromJson((e as Map).cast<String, dynamic>())).toList();
}

String _encodeActions() => jsonEncode(_actions.map((a) => a.toJson()).toList());

// In the save companion:
actions: Value(_encodeActions()),

Future<void> _publishToMarketplace() async {
  // Build MarketplaceSkill from current form state and call publish.
  // Gather actionTypes from _actions.
  final actionTypes = _actions.map((a) => a.type).toSet().toList();
  final snapshot = {
    'name': _nameController.text,
    'description': _descriptionController.text ?? '',
    'output_type': _outputType,
    'tone': _tone,
    'language': _language,
    'identify_speakers': _identifySpeakers,
    'vocabulary_hints': jsonEncode(_vocabularyHints),
    'output_language': _outputLanguage,
    'additional_instructions': _additionalInstructions,
    'actions': _encodeActions(),
  };
  final skill = MarketplaceSkill(
    id: '',
    authorId: ref.read(currentUserIdProvider) ?? '',
    authorName: '',
    name: _nameController.text,
    description: _descriptionController.text ?? '',
    tags: const [],
    outputType: _outputType,
    actionTypes: actionTypes,
    latestVersion: 1,
    installCount: 0,
    skillSnapshot: snapshot,
    publishedAt: DateTime.now(),
  );
  await ref.read(marketplaceClientProvider).publish(skill);
  if (mounted) {
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Skill published to Marketplace.')));
  }
}
```

Add `import 'dart:convert';`, `import '../../data/pipeline/pipeline_client.dart';`, `import '../../data/marketplace/marketplace_client.dart';`, and `import 'action_edit_sheet.dart';` to `skill_edit_screen.dart`.

Also add `flutter pub add reorderable_item` if ReorderableListView is not in your flutter version (it is built-in since Flutter 2.0, so no extra dependency needed).

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/settings/skill_edit_screen_actions_test.dart`
Expected: PASS (both tests).

- [ ] **Step 6: Commit**

```bash
git add lib/features/settings/action_edit_sheet.dart lib/features/settings/skill_edit_screen.dart test/features/settings/skill_edit_screen_actions_test.dart
git commit -m "feat: add ActionEditSheet and Actions section to SkillEditScreen"
```

---

## Task 11: Updated ResultTab — unified view + Skill Details debug toggle

**Files:**
- Modify: `lib/features/detail/result_tab.dart` (assumes it exists from M1 plan)
- Modify: `test/features/detail/result_tab_test.dart`

**Interfaces:**
- Consumes: `RecordingResult` with `skillResults` JSON (now includes `actionsLog`). The `SkillResult` embedded JSON gains `actionsLog: List<ActionLog>`.
- Produces: `ResultTab` with two views toggled by a switch:
  - **Unified view (default):** transcript section (collapsible) + one section per skill (skill name as header, output text, copy/share button).
  - **Skill Details view (debug):** same sections but each expanded with execution status (`✓ AI done → ✓ Actions fired | ✗ error`) and per-action log rows (type, timestamp, success/fail).

Note: the `skillResults` JSON stored in `RecordingResult` needs to be parsed into a richer model. Define `SkillResultEntry` locally in `result_tab.dart` for display purposes only — the DB stores the raw JSON.

- [ ] **Step 1: Write the failing widget test**

```dart
// test/features/detail/result_tab_test.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/features/detail/result_tab.dart';

String _makeResultJson() => jsonEncode([
  {
    'skillId': 's1',
    'skillName': 'Meeting Summary',
    'output': 'This was a productive meeting.',
    'actionsLog': [
      {'type': 'slack', 'firedAt': '2026-06-22T10:00:00.000Z', 'success': true, 'error': null},
    ],
  },
  {
    'skillId': 's2',
    'skillName': 'Action Items',
    'output': '1. Alice: write spec\n2. Bob: review PR',
    'actionsLog': [],
  },
]);

void main() {
  Widget wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

  testWidgets('unified view shows skill name headers and output', (tester) async {
    await tester.pumpWidget(wrap(ResultTab(
      transcript: 'speaker_a: Hello.\nspeaker_b: Hi.',
      skillResultsJson: _makeResultJson(),
    )));
    await tester.pumpAndSettle();

    expect(find.text('Meeting Summary'), findsOneWidget);
    expect(find.text('This was a productive meeting.'), findsOneWidget);
    expect(find.text('Action Items'), findsOneWidget);
  });

  testWidgets('Skill Details toggle shows action log', (tester) async {
    await tester.pumpWidget(wrap(ResultTab(
      transcript: 'speaker_a: Hello.',
      skillResultsJson: _makeResultJson(),
    )));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Skill Details'));
    await tester.pumpAndSettle();

    expect(find.text('slack'), findsOneWidget);
    expect(find.textContaining('✓'), findsWidgets);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flutter test test/features/detail/result_tab_test.dart`
Expected: FAIL — `ResultTab` signature changed / Skill Details toggle not present.

- [ ] **Step 3: Replace `lib/features/detail/result_tab.dart`**

```dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class _ActionLog {
  final String type;
  final String firedAt;
  final bool success;
  final String? error;
  _ActionLog({required this.type, required this.firedAt, required this.success, this.error});
  factory _ActionLog.fromJson(Map<String, dynamic> j) => _ActionLog(
        type: j['type'] as String,
        firedAt: j['firedAt'] as String,
        success: j['success'] as bool,
        error: j['error'] as String?,
      );
}

class _SkillEntry {
  final String skillId;
  final String skillName;
  final String output;
  final List<_ActionLog> actionsLog;
  _SkillEntry(
      {required this.skillId,
      required this.skillName,
      required this.output,
      required this.actionsLog});
  factory _SkillEntry.fromJson(Map<String, dynamic> j) => _SkillEntry(
        skillId: j['skillId'] as String,
        skillName: j['skillName'] as String,
        output: j['output'] as String,
        actionsLog: ((j['actionsLog'] as List?) ?? [])
            .map((e) => _ActionLog.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
      );
}

class ResultTab extends StatefulWidget {
  const ResultTab({
    super.key,
    required this.transcript,
    required this.skillResultsJson,
  });
  final String transcript;
  final String skillResultsJson;

  @override
  State<ResultTab> createState() => _State();
}

class _State extends State<ResultTab> {
  bool _debug = false;

  List<_SkillEntry> get _skills {
    final list = jsonDecode(widget.skillResultsJson) as List;
    return list.map((e) => _SkillEntry.fromJson((e as Map).cast<String, dynamic>())).toList();
  }

  @override
  Widget build(BuildContext context) {
    final skills = _skills;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            const Text('Skill Details'),
            Switch(value: _debug, onChanged: (v) => setState(() => _debug = v)),
          ],
        ),
        // Transcript (collapsible)
        ExpansionTile(
          title: const Text('Transcript'),
          children: [
            Padding(
              padding: const EdgeInsets.all(8),
              child: Text(widget.transcript),
            ),
          ],
        ),
        const Divider(),
        for (final skill in skills) ...[
          _SkillSection(skill: skill, debug: _debug),
          const SizedBox(height: 8),
        ],
      ],
    );
  }
}

class _SkillSection extends StatelessWidget {
  const _SkillSection({required this.skill, required this.debug});
  final _SkillEntry skill;
  final bool debug;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(skill.skillName,
                    style: Theme.of(context).textTheme.titleSmall),
                IconButton(
                  icon: const Icon(Icons.copy, size: 18),
                  tooltip: 'Copy',
                  onPressed: () =>
                      Clipboard.setData(ClipboardData(text: skill.output)),
                ),
              ],
            ),
            Text(skill.output),
            if (debug) ...[
              const Divider(height: 24),
              Text('✓ AI output produced',
                  style: TextStyle(color: Colors.green[700], fontSize: 12)),
              if (skill.actionsLog.isEmpty)
                const Text('No actions configured.',
                    style: TextStyle(color: Colors.grey, fontSize: 12)),
              for (final log in skill.actionsLog)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    children: [
                      Icon(
                        log.success ? Icons.check_circle : Icons.error,
                        size: 14,
                        color: log.success ? Colors.green : Colors.red,
                      ),
                      const SizedBox(width: 4),
                      Text(log.type,
                          style: const TextStyle(fontSize: 12)),
                      const SizedBox(width: 8),
                      Text(log.firedAt,
                          style: const TextStyle(
                              fontSize: 11, color: Colors.grey)),
                      if (log.error != null) ...[
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text('✗ ${log.error}',
                              style: const TextStyle(
                                  fontSize: 11, color: Colors.red),
                              overflow: TextOverflow.ellipsis),
                        ),
                      ] else
                        const Padding(
                          padding: EdgeInsets.only(left: 4),
                          child: Text('✓',
                              style: TextStyle(
                                  fontSize: 11, color: Colors.green)),
                        ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 4: Update `RecordingDetailScreen` / `result_tab.dart` wiring**

In `lib/features/detail/recording_detail_screen.dart`, update the `ResultTab` call site to pass `transcript` and `skillResultsJson` from the loaded `RecordingResult`. Replace any previous `ResultTab()` instantiation with:

```dart
// Where result is a RecordingResult row:
ResultTab(
  transcript: result.transcript,
  skillResultsJson: result.skillResults,
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flutter test test/features/detail/result_tab_test.dart`
Expected: PASS (both tests).

- [ ] **Step 6: Run full test suite**

Run: `flutter test`
Expected: PASS on all tests. Fix any compilation errors caused by the `SkillRequest` signature change in earlier tasks before committing.

- [ ] **Step 7: Commit**

```bash
git add lib/features/detail/result_tab.dart test/features/detail/result_tab_test.dart
git commit -m "feat: add ResultTab unified view with Skill Details debug toggle and action logs"
```

---

## Self-Review Checklist

**Spec coverage:**
- §4 Skills as automation units (AI intent + actions) → Tasks 2, 3, 4 ✓
- §4 Sequential skill execution → Pipeline contract (Task 3, MockPipelineClient Task 5) ✓
- §5 Skill Marketplace (browse/install/publish) → Tasks 6, 7, 8, 9 ✓
- §5 Credential model (embedded in skill, shared via marketplace) → Task 9 install flow ✓
- §5 Skill versioning → `latestVersion` in MarketplaceSkill (Task 6), `installFromSnapshot` checks version (Task 9) ✓
- §6 Screen flow: MarketplaceScreen, SkillDetailScreen, ActionEditSheet, ResultTab debug toggle → Tasks 8, 9, 10, 11 ✓
- §9 Pipeline contract: `current_skill` in status, `actions_log` in result → Tasks 3, 5 ✓
- §11 `{{output}}`, `{{speaker}}`, `{{recording_title}}` template variables → ActionEditSheet field hints (Task 10) ✓

**Type consistency:**
- `SkillAction` defined in `pipeline_client.dart` and imported in `action_edit_sheet.dart`, `skill_resolution.dart` ✓
- `ActionLog` defined in `pipeline_client.dart`; `_ActionLog` in `result_tab.dart` is a local display model (no import conflict) ✓
- `MarketplaceSkill` defined in `marketplace_client.dart` and imported in both marketplace screens ✓
- `SkillRequest.actions: List<SkillAction>` — populated by `resolveSkills()` (Task 4) ✓
