import 'package:go_router/go_router.dart';
import '../features/recordings/recordings_screen.dart';
import '../features/skills/skill_editor_screen.dart';
import '../features/pipeline/skill_review_screen.dart';

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
        final checkpoint = state.extra as Map<String, dynamic>? ?? {};
        return SkillReviewScreen(
          checkpoint: checkpoint,
          onApprove: () => context.pop(),
          onSkip: () => context.pop(),
        );
      },
    ),
  ],
);
