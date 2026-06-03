import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/status_bar.dart';
import 'package:docs_agent/writing/widgets/writing_workbench.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MultiBlocProvider(
    providers: [
      BlocProvider<WritingReviewCubit>.value(value: cubit),
    ],
    child: MaterialApp(
      home: const WritingWorkbench(),
    ),
  );
}

void main() {
  group('WritingWorkbench', () {
    testWidgets('renders all panels', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('✎ 写作云'), findsOneWidget);
      expect(find.text('▶ 评审'), findsOneWidget);
      expect(find.text('加载样本'), findsOneWidget);
      expect(find.text('📄 底稿'), findsOneWidget);
      expect(find.text('Review'), findsOneWidget);
      expect(find.byType(StatusBar), findsOneWidget);
      cubit.close();
    });

    testWidgets('load sample button triggers loadSample', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.byType(TextField), findsOneWidget);
      await tester.tap(find.text('加载样本'));
      await tester.pump();
      expect(cubit.state.text, isNotEmpty);
      cubit.close();
    });

    testWidgets('review button triggers analysis', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他来了。');
      await tester.pumpWidget(_buildApp(cubit));
      await tester.tap(find.text('▶ 评审'));
      await tester.pump();
      expect(cubit.state.analysis, isNotNull);
      cubit.close();
    });

    testWidgets('switches review tabs', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.tap(find.text('🎯 情境'));
      await tester.pump();
      expect(cubit.state.currentTab, ReviewPanelTab.reflect);
      await tester.tap(find.text('✏️ 改写'));
      await tester.pump();
      expect(cubit.state.currentTab, ReviewPanelTab.rewrite);
      cubit.close();
    });

    testWidgets('shows status bar with counts', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text(cubit.state.charCount.toString()), findsWidgets);
      cubit.close();
    });
  });
}
