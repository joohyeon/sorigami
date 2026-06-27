import 'package:flutter/material.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({
    super.key,
    required this.qualityJson,
    this.skillResults = const [],
  });

  final Map<String, dynamic> qualityJson;
  final List<Map<String, dynamic>> skillResults;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Results')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _QualityCard(quality: qualityJson),
          const SizedBox(height: 16),
          ...skillResults.map((r) => Card(
                child: ListTile(
                  title: Text(r['skill_name'] as String? ?? ''),
                  subtitle: Text(r['output_markdown'] as String? ?? ''),
                ),
              )),
        ],
      ),
    );
  }
}

class _QualityCard extends StatefulWidget {
  const _QualityCard({required this.quality});
  final Map<String, dynamic> quality;

  @override
  State<_QualityCard> createState() => _QualityCardState();
}

class _QualityCardState extends State<_QualityCard> {
  bool _expanded = false;

  Color _scoreColor(String score) => switch (score) {
        'good' => Colors.green,
        'fair' => Colors.orange,
        _ => Colors.red,
      };

  String _scoreLabel(String score) => switch (score) {
        'good' => 'Good',
        'fair' => 'Fair',
        _ => 'Poor',
      };

  @override
  Widget build(BuildContext context) {
    if (widget.quality.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Text('Quality data unavailable'),
        ),
      );
    }

    final score = widget.quality['transcript_score'] as String? ?? 'poor';
    final degraded = widget.quality['diarization_degraded'] as bool? ?? false;
    final lowCount = widget.quality['low_confidence_count'] as int? ?? 0;
    final lowSegs = (widget.quality['low_confidence_segments'] as List?)
            ?.cast<Map<String, dynamic>>() ??
        [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Chip(
                label: Text(_scoreLabel(score)),
                backgroundColor: _scoreColor(score).withValues(alpha: 0.15),
                labelStyle: TextStyle(color: _scoreColor(score), fontWeight: FontWeight.bold),
              ),
              const SizedBox(width: 8),
              Text(degraded ? 'Single-speaker fallback' : 'Multi-speaker',
                  style: Theme.of(context).textTheme.bodySmall),
            ]),
            if (lowCount > 0) ...[
              const SizedBox(height: 8),
              GestureDetector(
                onTap: () => setState(() => _expanded = !_expanded),
                child: Text(
                  '$lowCount low-confidence segment${lowCount == 1 ? '' : 's'}',
                  style: TextStyle(color: Colors.orange[700], decoration: TextDecoration.underline),
                ),
              ),
              if (_expanded)
                ...lowSegs.map((s) => Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        '${s['text']} (${s['avg_logprob']})',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    )),
            ],
          ],
        ),
      ),
    );
  }
}
