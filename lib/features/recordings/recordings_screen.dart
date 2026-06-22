import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/providers.dart';

class RecordingsScreen extends ConsumerWidget {
  const RecordingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final modes = ref.watch(allModesProvider);
    final recordings = ref.watch(allRecordingsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Recordings')),
      body: Column(
        children: [
          SizedBox(
            height: 56,
            child: modes.when(
              data: (list) => ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: list.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (context, i) {
                  final m = list[i];
                  return Center(
                    child: Chip(
                      avatar: Text(m.icon),
                      label: Text(m.name),
                    ),
                  );
                },
              ),
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: recordings.when(
              data: (list) => list.isEmpty
                  ? const Center(child: Text('No recordings yet'))
                  : ListView.builder(
                      itemCount: list.length,
                      itemBuilder: (context, i) =>
                          ListTile(title: Text(list[i].title)),
                    ),
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {}, // RecordingInfoSheet — Plan 2
        child: const Icon(Icons.fiber_manual_record),
      ),
    );
  }
}
