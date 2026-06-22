import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/seed/seed_data.dart';
import '../../helpers/test_database.dart';

void main() {
  test('seeds 5 modes with General as default, and is idempotent', () async {
    final db = newTestDatabase();
    addTearDown(db.close);

    await seedIfEmpty(db);
    var modes = await db.modeDao.watchAllModes().first;
    expect(modes.length, 5);

    final general = modes.firstWhere((m) => m.name == 'General');
    expect(general.isDefault, isTrue);
    expect(general.icon, '📝');

    // Each seed mode links at least one skill.
    final skills = await db.skillDao.watchAllSkills().first;
    expect(skills, isNotEmpty);

    // Running again does not duplicate.
    await seedIfEmpty(db);
    modes = await db.modeDao.watchAllModes().first;
    expect(modes.length, 5);
  });
}
