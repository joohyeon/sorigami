import 'package:drift/drift.dart';
import 'open_connection.dart';
import 'converters.dart';
import 'daos/mode_dao.dart';
import 'daos/skill_dao.dart';
import 'daos/recording_dao.dart';

part 'database.g.dart';

class Recordings extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get memo => text().nullable()();
  TextColumn get tags => text().map(const StringListConverter())
      .withDefault(const Constant('[]'))();
  TextColumn get category => text().nullable()();
  TextColumn get language => text().withDefault(const Constant('auto'))();
  TextColumn get modeId => text().nullable()();
  TextColumn get audioFilePath => text()();
  IntColumn get audioDurationMs => integer().nullable()();
  IntColumn get audioFileSize => integer().nullable()();
  TextColumn get uploadStatus =>
      text().withDefault(const Constant('none'))();
  TextColumn get driveFileId => text().nullable()();
  TextColumn get jobId => text().nullable()();
  TextColumn get jobStatus =>
      text().withDefault(const Constant('none'))();
  TextColumn get jobError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Modes extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get icon => text()();
  BoolColumn get isDefault => boolean().withDefault(const Constant(false))();
  BoolColumn get isSeeded => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Skills extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();
  TextColumn get language => text().withDefault(const Constant('auto'))();
  BoolColumn get identifySpeakers =>
      boolean().withDefault(const Constant(true))();
  TextColumn get vocabularyHints => text().map(const StringListConverter())
      .withDefault(const Constant('[]'))();
  TextColumn get outputType =>
      text().withDefault(const Constant('summary'))();
  TextColumn get focusArea => text().nullable()();
  TextColumn get tone => text().withDefault(const Constant('concise'))();
  TextColumn get outputLanguage =>
      text().withDefault(const Constant('auto'))();
  TextColumn get additionalInstructions => text().nullable()();
  BoolColumn get requireReview =>
      boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class ModeSkills extends Table {
  TextColumn get modeId => text()();
  TextColumn get skillId => text()();
  IntColumn get sortOrder => integer()();

  @override
  Set<Column> get primaryKey => {modeId, skillId};
}

@DriftDatabase(
  tables: [Recordings, Modes, Skills, ModeSkills],
  daos: [RecordingDao, ModeDao, SkillDao],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  /// Convenience constructor for production.
  AppDatabase.open() : super(openConnection());

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.addColumn(skills, skills.requireReview);
          }
        },
      );
}
