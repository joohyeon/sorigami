import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:drift/native.dart';
import 'package:sorigamis/data/db/database.dart';
import 'package:sorigamis/features/skills/skill_editor_screen.dart';
import 'package:sorigamis/providers/providers.dart';

AppDatabase _db() => AppDatabase(NativeDatabase.memory());

Widget _wrap(AppDatabase db, String skillId) => ProviderScope(
      overrides: [databaseProvider.overrideWithValue(db)],
      child: MaterialApp(
        home: SkillEditorScreen(skillId: skillId),
      ),
    );

void main() {
  testWidgets('shows require review toggle defaulting to off', (tester) async {
    final db = _db();
    await db.skillDao.insertSkill(SkillsCompanion.insert(
      id: 's1',
      name: 'Summary',
      createdAt: DateTime(2026, 1, 1),
    ));
    await tester.pumpWidget(_wrap(db, 's1'));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Require review before actions fire'), findsOneWidget);
    final toggle = tester.widget<Switch>(find.byType(Switch));
    expect(toggle.value, isFalse);
    await db.close();
  });

  testWidgets('shows error when skill id is not found', (tester) async {
    final db = _db();
    await tester.pumpWidget(_wrap(db, 'nonexistent-id'));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Skill not found.'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
    await db.close();
  });

  testWidgets('toggling require_review saves to Drift', (tester) async {
    final db = _db();
    await db.skillDao.insertSkill(SkillsCompanion.insert(
      id: 's1',
      name: 'Summary',
      createdAt: DateTime(2026, 1, 1),
    ));
    await tester.pumpWidget(_wrap(db, 's1'));
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byType(Switch));
    await tester.pump(const Duration(milliseconds: 100));

    final skills = await tester.runAsync(() => db.skillDao.getAllSkills());
    expect(skills!.first.requireReview, isTrue);
    await db.close();
  });
}
