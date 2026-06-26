import 'package:flutter/material.dart';

class SkillReviewScreen extends StatelessWidget {
  const SkillReviewScreen({
    super.key,
    required this.checkpoint,
    required this.onApprove,
    required this.onSkip,
  });

  final Map<String, dynamic> checkpoint;
  final VoidCallback onApprove;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    final skillName = checkpoint['skill_name'] as String? ?? '';
    final markdown = checkpoint['output_markdown'] as String? ?? '';
    return Scaffold(
      appBar: AppBar(title: Text('Review: $skillName')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: SingleChildScrollView(child: Text(markdown))),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onSkip,
                    child: const Text('Skip'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: onApprove,
                    child: const Text('Approve & Continue'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
