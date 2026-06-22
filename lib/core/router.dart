import 'package:go_router/go_router.dart';
import '../features/recordings/recordings_screen.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const RecordingsScreen()),
  ],
);
