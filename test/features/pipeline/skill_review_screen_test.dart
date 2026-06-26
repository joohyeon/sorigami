import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/features/pipeline/skill_review_screen.dart';

Widget _wrap(Map<String, dynamic> checkpoint, {
  void Function()? onApprove,
  void Function()? onSkip,
}) =>
    MaterialApp(
      home: SkillReviewScreen(
        checkpoint: checkpoint,
        onApprove: onApprove ?? () {},
        onSkip: onSkip ?? () {},
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
      onApprove: () => approved = true,
    ));
    await tester.tap(find.text('Approve & Continue'));
    await tester.pump();
    expect(approved, isTrue);
  });

  testWidgets('skip button calls onSkip', (tester) async {
    var skipped = false;
    await tester.pumpWidget(_wrap(
      {'skill_name': 'Summary', 'output_markdown': 'A short summary.'},
      onSkip: () => skipped = true,
    ));
    await tester.tap(find.text('Skip'));
    await tester.pump();
    expect(skipped, isTrue);
  });
}
