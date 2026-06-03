import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/review_tab.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MaterialApp(
    home: Scaffold(
      body: ReviewTab(cubit: cubit),
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
  });
}
