import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/db/database.dart';
import '../../providers/providers.dart';

class SkillEditorScreen extends ConsumerStatefulWidget {
  const SkillEditorScreen({super.key, required this.skillId});
  final String skillId;

  @override
  ConsumerState<SkillEditorScreen> createState() => _SkillEditorScreenState();
}

class _SkillEditorScreenState extends ConsumerState<SkillEditorScreen> {
  bool? _requireReview;
  String? _name;
  String? _loadError;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_requireReview == null && _loadError == null) _load();
  }

  Future<void> _load() async {
    try {
      final dao = ref.read(skillDaoProvider);
      final all = await dao.getAllSkills();
      final match = all.where((s) => s.id == widget.skillId).firstOrNull;
      if (!mounted) return;
      if (match == null) {
        setState(() => _loadError = 'Skill not found.');
        return;
      }
      setState(() {
        _requireReview = match.requireReview;
        _name = match.name;
      });
    } catch (e) {
      if (mounted) setState(() => _loadError = 'Failed to load skill.');
    }
  }

  Future<void> _toggleRequireReview(bool value) async {
    final previous = _requireReview;
    setState(() => _requireReview = value);
    try {
      await ref.read(skillDaoProvider).updateRequireReview(widget.skillId, value);
    } catch (e) {
      if (mounted) {
        setState(() => _requireReview = previous);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not save. Please try again.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loadError != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Edit Skill')),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_loadError!),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () {
                  setState(() => _loadError = null);
                  _load();
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }
    if (_requireReview == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(title: Text(_name ?? widget.skillId)),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Require review before actions fire'),
            subtitle: const Text(
              'Hermes will pause and show you results before sending to Slack, Linear, or webhooks.',
            ),
            value: _requireReview!,
            onChanged: _toggleRequireReview,
          ),
        ],
      ),
    );
  }
}
