import 'package:flutter_test/flutter_test.dart';
import '../../helpers/test_database.dart';

void main() {
  test('opens an in-memory database at schema version 2', () async {
    final db = newTestDatabase();
    expect(db.schemaVersion, 2);
    // Querying a table forces schema creation without error.
    expect(await db.select(db.modes).get(), isEmpty);
    await db.close();
  });
}
