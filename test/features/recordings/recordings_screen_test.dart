import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/data/db/database.dart';
import 'package:sorigamis/features/recordings/recordings_screen.dart';
import 'package:sorigamis/providers/providers.dart';

void main() {
  testWidgets('shows mode chips and an empty-recordings message', (tester) async {
    // Stub providers directly: avoids Drift background-isolate pump hang.
    final fakeModes = [
      Mode(
        id: '1',
        name: 'General',
        icon: '📝',
        isDefault: true,
        isSeeded: true,
        createdAt: DateTime(2026, 1, 1),
      ),
      Mode(
        id: '2',
        name: 'Team Meeting',
        icon: '🗓',
        isDefault: false,
        isSeeded: true,
        createdAt: DateTime(2026, 1, 1),
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          allModesProvider.overrideWith(
            (ref) => Stream.value(fakeModes),
          ),
          allRecordingsProvider.overrideWith(
            (ref) => Stream.value(const <Recording>[]),
          ),
        ],
        child: const MaterialApp(home: RecordingsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('General'), findsOneWidget);
    expect(find.text('Team Meeting'), findsOneWidget);
    expect(find.text('No recordings yet'), findsOneWidget);
  });
}
