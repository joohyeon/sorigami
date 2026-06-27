import 'package:flutter/material.dart';

class SkillReviewScreen extends StatefulWidget {
  const SkillReviewScreen({
    super.key,
    required this.checkpoint,
    required this.onApprove,
    required this.onSkip,
  });

  final Map<String, dynamic> checkpoint;
  final Future<void> Function() onApprove;
  final Future<void> Function() onSkip;

  @override
  State<SkillReviewScreen> createState() => _SkillReviewScreenState();
}

class _SkillReviewScreenState extends State<SkillReviewScreen> {
  bool _loading = false;

  Future<void> _handle(Future<void> Function() action) async {
    setState(() => _loading = true);
    try {
      await action();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to save decision: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final skillName = widget.checkpoint['skill_name'] as String? ?? '';
    final markdown = widget.checkpoint['output_markdown'] as String? ?? '';
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
                    onPressed: _loading ? null : () => _handle(widget.onSkip),
                    child: const Text('Skip'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _loading ? null : () => _handle(widget.onApprove),
                    child: _loading
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Approve & Continue'),
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
