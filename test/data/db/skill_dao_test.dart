import 'package:drift/drift.dart' hide isNull;
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import '../../helpers/test_database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = newTestDatabase());
  tearDown(() => db.close());

  SkillsCompanion _skill(String id, String name) => SkillsCompanion.insert(
        id: id,
        name: name,
        createdAt: DateTime(2026, 1, 1),
      );

  test('requireReview defaults to false on insert', () async {
    await db.skillDao.insertSkill(_skill('s1', 'Summary'));
    final skills = await db.skillDao.watchAllSkills().first;
    expect(skills.first.requireReview, isFalse);
  });

  test('updateRequireReview sets the flag', () async {
    await db.skillDao.insertSkill(_skill('s1', 'Summary'));
    await db.skillDao.updateRequireReview('s1', true);
    final skills = await db.skillDao.watchAllSkills().first;
    expect(skills.first.requireReview, isTrue);
  });
}
