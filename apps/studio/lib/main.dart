import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'writing/bloc/writing_review_cubit.dart';
import 'writing/services/deep_analysis_service.dart';
import 'writing/theme/writing_theme.dart';
import 'writing/widgets/writing_workbench.dart';

void main() {
  final providerUrl =
      const String.fromEnvironment('PROVIDER_URL', defaultValue: 'http://localhost:9000');
  DeepAnalysisService? deepService;
  if (providerUrl.isNotEmpty) {
    deepService = DeepAnalysisService(providerUrl);
  }
  runApp(LabApp(deepService: deepService));
}

class LabApp extends StatelessWidget {
  final DeepAnalysisService? deepService;
  const LabApp({super.key, this.deepService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '写作云 Lab',
      debugShowCheckedModeBanner: false,
      theme: WritingTheme.dark,
      home: AppShell(deepService: deepService),
    );
  }
}

class AppShell extends StatefulWidget {
  final DeepAnalysisService? deepService;
  const AppShell({super.key, this.deepService});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  late final WritingReviewCubit _writingCubit;

  @override
  void initState() {
    super.initState();
    _writingCubit = WritingReviewCubit(deepService: widget.deepService);
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
