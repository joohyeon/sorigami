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
