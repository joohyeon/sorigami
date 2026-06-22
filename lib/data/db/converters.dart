import 'dart:convert';
import 'package:drift/drift.dart';

/// Stores a `List<String>` as a JSON-encoded text column.
class StringListConverter extends TypeConverter<List<String>, String> {
  const StringListConverter();

  @override
  String toSql(List<String> value) => jsonEncode(value);

  @override
  List<String> fromSql(String fromDb) =>
      (jsonDecode(fromDb) as List<dynamic>).cast<String>();
}
