import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'writing/bloc/writing_review_cubit.dart';
import 'writing/theme/writing_theme.dart';
import 'writing/widgets/writing_workbench.dart';

void main() {
  runApp(const LabApp());
}

class LabApp extends StatelessWidget {
  const LabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '写作云 Lab',
      debugShowCheckedModeBanner: false,
      theme: WritingTheme.dark,
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final _writingCubit = WritingReviewCubit();

  @override
  void initState() {
    super.initState();
    _writingCubit.loadSample();
  }

  @override
  void dispose() {
    _writingCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _writingCubit,
      child: const WritingWorkbench(),
    );
  }
}
