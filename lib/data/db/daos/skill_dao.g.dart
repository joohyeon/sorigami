// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'skill_dao.dart';

// ignore_for_file: type=lint
mixin _$SkillDaoMixin on DatabaseAccessor<AppDatabase> {
  $SkillsTable get skills => attachedDatabase.skills;
  $ModeSkillsTable get modeSkills => attachedDatabase.modeSkills;
  SkillDaoManager get managers => SkillDaoManager(this);
}

class SkillDaoManager {
  final _$SkillDaoMixin _db;
  SkillDaoManager(this._db);
  $$SkillsTableTableManager get skills =>
      $$SkillsTableTableManager(_db.attachedDatabase, _db.skills);
  $$ModeSkillsTableTableManager get modeSkills =>
      $$ModeSkillsTableTableManager(_db.attachedDatabase, _db.modeSkills);
}
