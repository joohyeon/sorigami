import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import '../../helpers/test_database.dart';

void main() {
  late AppDatabase db;
  setUp(() => db = newTestDatabase());
  tearDown(() => db.close());

  test('watchAllRecordings emits newest first', () async {
    await db.recordingDao.insertRecording(RecordingsCompanion.insert(
      id: 'old', title: 'Old', audioFilePath: '/tmp/old.m4a',
      createdAt: DateTime(2026, 1, 1), updatedAt: DateTime(2026, 1, 1),
    ));
    await db.recordingDao.insertRecording(RecordingsCompanion.insert(
      id: 'new', title: 'New', audioFilePath: '/tmp/new.m4a',
      createdAt: DateTime(2026, 6, 1), updatedAt: DateTime(2026, 6, 1),
    ));

    final rows = await db.recordingDao.watchAllRecordings().first;
    expect(rows.map((r) => r.id).toList(), ['new', 'old']);
  });
}
