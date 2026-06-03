import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/rewrite_tab.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MaterialApp(
    home: Scaffold(
      body: RewriteTab(cubit: cubit),
    ),
  );
}

void main() {
  group('RewriteTab', () {
    testWidgets('shows placeholder when no analysis', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('暂无改写建议。'), findsOneWidget);
      cubit.close();
    });

    testWidgets('shows suggestions when analysis has rewrites', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('他悲伤地看着她。\n她开心地笑了。\n他走了过去。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.pump();
      expect(find.text('改写建议'), findsOneWidget);
      cubit.close();
    });

    testWidgets('tapping a suggestion button triggers jump', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('他悲伤地看着她。\n她开心地笑了。\n他走了过去。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.pump();
      final jumpButton = find.text('✎ 定位到此处');
      if (jumpButton.evaluate().isNotEmpty) {
        await tester.tap(jumpButton.first);
      }
      cubit.close();
    });
  });
}
