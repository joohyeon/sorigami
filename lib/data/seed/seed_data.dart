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
