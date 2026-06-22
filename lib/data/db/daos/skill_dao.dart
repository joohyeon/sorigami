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
