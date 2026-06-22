import 'package:flutter/material.dart';
import 'core/router.dart';

class SorigamisApp extends StatelessWidget {
  const SorigamisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Sorigamis',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      routerConfig: appRouter,
    );
  }
}
