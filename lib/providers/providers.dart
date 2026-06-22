import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/db/database.dart';
import '../data/db/daos/mode_dao.dart';
import '../data/db/daos/skill_dao.dart';
import '../data/db/daos/recording_dao.dart';

/// Overridden in main() with a concrete AppDatabase.
final databaseProvider = Provider<AppDatabase>(
  (ref) => throw UnimplementedError('databaseProvider must be overridden'),
);

final recordingDaoProvider =
    Provider<RecordingDao>((ref) => ref.watch(databaseProvider).recordingDao);
final modeDaoProvider =
    Provider<ModeDao>((ref) => ref.watch(databaseProvider).modeDao);
final skillDaoProvider =
    Provider<SkillDao>((ref) => ref.watch(databaseProvider).skillDao);

final allModesProvider = StreamProvider<List<Mode>>(
    (ref) => ref.watch(modeDaoProvider).watchAllModes());
final allRecordingsProvider = StreamProvider<List<Recording>>(
    (ref) => ref.watch(recordingDaoProvider).watchAllRecordings());
