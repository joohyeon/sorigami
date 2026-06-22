import 'package:drift/native.dart';
import 'package:sorigamis/data/db/database.dart';

/// Fresh in-memory database for each test.
AppDatabase newTestDatabase() => AppDatabase(NativeDatabase.memory());
