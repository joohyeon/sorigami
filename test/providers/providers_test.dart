import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/seed/seed_data.dart';
import 'package:sorigamis/providers/providers.dart';
import '../helpers/test_database.dart';

void main() {
  test('allModesProvider exposes seeded modes via the overridden db',
      () async {
    final db = newTestDatabase();
    await seedIfEmpty(db);
    addTearDown(db.close);

    final container = ProviderContainer(
      overrides: [databaseProvider.overrideWithValue(db)],
    );
    addTearDown(container.dispose);

    final modes = await container.read(allModesProvider.future);
    expect(modes.length, 5);
  });
}
