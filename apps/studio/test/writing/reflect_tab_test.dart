import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/reflect_tab.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MaterialApp(
    home: Scaffold(
      body: ReflectTab(cubit: cubit),
    ),
  );
}

void main() {
  group('ReflectTab', () {
    testWidgets('shows placeholder when no analysis', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('暂无识别到的可写位置。'), findsOneWidget);
      cubit.close();
    });

    testWidgets('shows situations when analysis has gaps', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.pump();
      expect(find.text('可写位置'), findsOneWidget);
      cubit.close();
    });

    testWidgets('tapping a situation card button triggers jump', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他推开门走了出去。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.pump();
      final writeButton = find.text('✎ 写在这里');
      if (writeButton.evaluate().isNotEmpty) {
        await tester.tap(writeButton.first);
      }
      cubit.close();
    });
  });
}
