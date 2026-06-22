// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mode_dao.dart';

// ignore_for_file: type=lint
mixin _$ModeDaoMixin on DatabaseAccessor<AppDatabase> {
  $ModesTable get modes => attachedDatabase.modes;
  ModeDaoManager get managers => ModeDaoManager(this);
}

class ModeDaoManager {
  final _$ModeDaoMixin _db;
  ModeDaoManager(this._db);
  $$ModesTableTableManager get modes =>
      $$ModesTableTableManager(_db.attachedDatabase, _db.modes);
}
