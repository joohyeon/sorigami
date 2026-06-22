import 'package:drift/drift.dart' hide isNull;
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
