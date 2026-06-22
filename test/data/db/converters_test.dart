import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/converters.dart';

void main() {
  final converter = const StringListConverter();

  test('round-trips a non-empty list through SQL form', () {
    const input = ['Fixli', 'OKR', 'standup'];
    final sql = converter.toSql(input);
    expect(converter.fromSql(sql), input);
  });

  test('maps an empty list to an empty list, not null', () {
    expect(converter.fromSql(converter.toSql(const [])), const <String>[]);
  });
}
