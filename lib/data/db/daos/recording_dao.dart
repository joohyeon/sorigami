import 'package:drift/drift.dart';
import '../database.dart';

part 'recording_dao.g.dart';

@DriftAccessor(tables: [Recordings])
class RecordingDao extends DatabaseAccessor<AppDatabase>
    with _$RecordingDaoMixin {
  RecordingDao(super.db);

  Future<int> insertRecording(RecordingsCompanion entry) =>
      into(recordings).insert(entry);

  Stream<List<Recording>> watchAllRecordings() {
    return (select(recordings)
          ..orderBy([
            (r) => OrderingTerm(
                expression: r.createdAt, mode: OrderingMode.desc),
          ]))
        .watch();
  }
}
