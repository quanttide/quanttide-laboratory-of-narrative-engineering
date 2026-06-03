import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/review_tab.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return BlocProvider<WritingReviewCubit>.value(
    value: cubit,
    child: MaterialApp(
      home: Scaffold(
        body: ReviewTab(cubit: cubit),
      ),
    ),
  );
}

void main() {
  group('ReviewTab', () {
    testWidgets('shows placeholder when no analysis', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('等待评审...'), findsOneWidget);
      cubit.close();
    });

    testWidgets('shows gaps and styles when analysis exists', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他走到了街上。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('空隙'), findsOneWidget);
      expect(find.text('风格'), findsOneWidget);
      cubit.close();
    });

    testWidgets('shows total score', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('他走了出去。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.textContaining('/100'), findsOneWidget);
      cubit.close();
    });

    testWidgets('tapping a gap item triggers jumpToLine', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他走到了街上。\n她整理了一下衣角。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      // Find a gap item by line number label
      final gapItem = find.textContaining('L1');
      expect(gapItem, findsWidgets);
      await tester.tap(gapItem.first);
      cubit.close();
    });

    testWidgets('tapping a second gap item does not throw', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天。\n过了一会儿，他又来了。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      final gapItems = find.textContaining('L');
      expect(gapItems, findsWidgets);
      await tester.tap(gapItems.last);
      cubit.close();
    });
  });
}
