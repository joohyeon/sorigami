import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sorigamis/features/results/results_screen.dart';

final _goodQuality = {
  'transcript_score': 'good',
  'avg_logprob': -0.42,
  'low_confidence_count': 0,
  'low_confidence_segments': <Map<String, dynamic>>[],
  'diarization_degraded': false,
  'segment_count': 87,
  'duration_sec': 3421.0,
};

final _poorQuality = {
  'transcript_score': 'poor',
  'avg_logprob': -0.95,
  'low_confidence_count': 3,
  'low_confidence_segments': [
    {'start_sec': 10.0, 'end_sec': 12.0, 'text': 'unclear speech', 'avg_logprob': -1.6},
  ],
  'diarization_degraded': true,
  'segment_count': 20,
  'duration_sec': 600.0,
};

Widget _wrap(Map<String, dynamic> quality, {List<Map<String, dynamic>> skillResults = const []}) =>
    MaterialApp(
      home: ResultsScreen(qualityJson: quality, skillResults: skillResults),
    );

void main() {
  testWidgets('shows Good quality chip', (tester) async {
    await tester.pumpWidget(_wrap(_goodQuality));
    expect(find.text('Good'), findsOneWidget);
    expect(find.text('Multi-speaker'), findsOneWidget);
  });

  testWidgets('shows Poor quality chip with diarization warning', (tester) async {
    await tester.pumpWidget(_wrap(_poorQuality));
    expect(find.text('Poor'), findsOneWidget);
    expect(find.text('Single-speaker fallback'), findsOneWidget);
  });

  testWidgets('expands to show low confidence segments', (tester) async {
    await tester.pumpWidget(_wrap(_poorQuality));
    await tester.tap(find.text('3 low-confidence segments'));
    await tester.pumpAndSettle();
    expect(find.textContaining('unclear speech'), findsOneWidget);
  });

  testWidgets('shows no low confidence section when count is 0', (tester) async {
    await tester.pumpWidget(_wrap(_goodQuality));
    expect(find.text('0 low-confidence segments'), findsNothing);
  });

  testWidgets('shows unavailable message when qualityJson is empty', (tester) async {
    await tester.pumpWidget(_wrap({}));
    expect(find.text('Quality data unavailable'), findsOneWidget);
    expect(find.text('Good'), findsNothing);
  });
}
