import 'package:go_router/go_router.dart';
import '../features/recordings/recordings_screen.dart';
import '../features/results/results_screen.dart';
import '../features/skills/skill_editor_screen.dart';
import '../features/pipeline/skill_review_screen.dart';
import '../data/api/pipeline_client.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const RecordingsScreen()),
    GoRoute(
      path: '/skills/:id/edit',
      builder: (context, state) =>
          SkillEditorScreen(skillId: state.pathParameters['id']!),
    ),
    GoRoute(
      path: '/jobs/:id/skill-review',
      builder: (context, state) {
        final jobId = state.pathParameters['id']!;
        final checkpoint = state.extra as Map<String, dynamic>? ?? {};
        final client = PipelineClient();
        return SkillReviewScreen(
          checkpoint: checkpoint,
          onApprove: () async {
            await client.resolveCheckpoint(jobId, skipped: false);
            context.pop();
          },
          onSkip: () async {
            await client.resolveCheckpoint(jobId, skipped: true);
            context.pop();
          },
        );
      },
    ),
    GoRoute(
      path: '/jobs/:id/results',
      builder: (context, state) {
        final extra = state.extra as Map<String, dynamic>? ?? {};
        return ResultsScreen(
          qualityJson: (extra['quality_json'] as Map<String, dynamic>?) ?? {},
          skillResults: (extra['skill_results'] as List?)?.cast<Map<String, dynamic>>() ?? [],
        );
      },
    ),
  ],
);
