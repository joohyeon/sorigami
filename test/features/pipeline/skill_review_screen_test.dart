import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/features/pipeline/skill_review_screen.dart';

Widget _wrap(Map<String, dynamic> checkpoint, {
  Future<void> Function()? onApprove,
  Future<void> Function()? onSkip,
}) =>
    MaterialApp(
      home: SkillReviewScreen(
        checkpoint: checkpoint,
        onApprove: onApprove ?? () async {},
        onSkip: onSkip ?? () async {},
      ),
    );

void main() {
  testWidgets('displays skill name and output', (tester) async {
    await tester.pumpWidget(_wrap({
      'skill_name': 'Action Items',
      'output_markdown': '- Buy milk\n- Call John',
    }));
    expect(find.text('Review: Action Items'), findsOneWidget);
    expect(find.textContaining('Buy milk'), findsOneWidget);
  });

  testWidgets('approve button calls onApprove', (tester) async {
    var approved = false;
    await tester.pumpWidget(_wrap(
      {'skill_name': 'Summary', 'output_markdown': 'A short summary.'},
      onApprove: () async => approved = true,
    ));
    await tester.tap(find.text('Approve & Continue'));
    await tester.pumpAndSettle();
    expect(approved, isTrue);
  });

  testWidgets('skip button calls onSkip', (tester) async {
    var skipped = false;
    await tester.pumpWidget(_wrap(
      {'skill_name': 'Summary', 'output_markdown': 'A short summary.'},
      onSkip: () async => skipped = true,
    ));
    await tester.tap(find.text('Skip'));
    await tester.pumpAndSettle();
    expect(skipped, isTrue);
  });

  testWidgets('shows snackbar and stays on screen when callback throws', (tester) async {
    await tester.pumpWidget(_wrap(
      {'skill_name': 'Summary', 'output_markdown': 'Content.'},
      onApprove: () async => throw Exception('network error'),
    ));
    await tester.tap(find.text('Approve & Continue'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Failed to save decision'), findsOneWidget);
    // Screen should still be visible
    expect(find.text('Review: Summary'), findsOneWidget);
  });

  testWidgets('buttons are disabled while loading', (tester) async {
    final completer = Completer<void>();
    await tester.pumpWidget(_wrap(
      {'skill_name': 'Summary', 'output_markdown': 'Content.'},
      onApprove: () => completer.future,
    ));
    await tester.tap(find.text('Approve & Continue'));
    await tester.pump();
    // Buttons should be disabled (null onPressed) while loading
    final approveBtn = tester.widget<FilledButton>(find.byType(FilledButton));
    expect(approveBtn.onPressed, isNull);
    // Resolve so no pending futures
    completer.complete();
    await tester.pumpAndSettle();
  });
}
