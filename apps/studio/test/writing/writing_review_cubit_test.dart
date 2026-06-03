import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/blocs/writing_review_cubit.dart';

void main() {
  group('WritingReviewCubit', () {
    test('initial state is correct', () {
      final cubit = WritingReviewCubit();
      expect(cubit.state.text, isEmpty);
      expect(cubit.state.analysis, isNull);
      expect(cubit.state.currentTab, ReviewPanelTab.review);
      expect(cubit.state.round, 1);
      expect(cubit.state.isLoading, isFalse);
      expect(cubit.state.charCount, 0);
      expect(cubit.state.gapCount, 0);
      cubit.close();
    });

    test('textChanged updates text', () {
      final cubit = WritingReviewCubit();
      cubit.textChanged('hello world');
      expect(cubit.state.text, 'hello world');
      expect(cubit.state.charCount, 11);
      cubit.close();
    });

    test('textChanged preserves analysis', () {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      expect(cubit.state.analysis, isNotNull);
      final originalScore = cubit.state.avgScore;
      cubit.textChanged('modified text');
      expect(cubit.state.analysis, isNotNull);
      expect(cubit.state.avgScore, originalScore);
      cubit.close();
    });

    test('runReview with empty text does nothing', () {
      final cubit = WritingReviewCubit();
      cubit.runReview();
      expect(cubit.state.analysis, isNull);
      cubit.close();
    });

    test('runReview analyzes text', () {
      final cubit = WritingReviewCubit();
      cubit.textChanged('他推开门走了进去。第二天，他又来了。');
      cubit.runReview();
      expect(cubit.state.analysis, isNotNull);
      expect(cubit.state.gapCount, greaterThan(0));
      expect(cubit.state.avgScore, greaterThan(0));
      expect(cubit.state.isLoading, isFalse);
      cubit.close();
    });

    test('loadSample loads and analyzes sample text', () {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      expect(cubit.state.text, isNotEmpty);
      expect(cubit.state.analysis, isNotNull);
      expect(cubit.state.gapCount, greaterThan(0));
      cubit.close();
    });

    test('switchTab changes current tab', () {
      final cubit = WritingReviewCubit();
      expect(cubit.state.currentTab, ReviewPanelTab.review);
      cubit.switchTab(ReviewPanelTab.reflect);
      expect(cubit.state.currentTab, ReviewPanelTab.reflect);
      cubit.switchTab(ReviewPanelTab.rewrite);
      expect(cubit.state.currentTab, ReviewPanelTab.rewrite);
      cubit.switchTab(ReviewPanelTab.review);
      expect(cubit.state.currentTab, ReviewPanelTab.review);
      cubit.close();
    });

    test('jumpToLine sets pendingJumpLine', () {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      cubit.jumpToLine(5);
      expect(cubit.state.pendingJumpLine, 5);
      cubit.close();
    });

    test('clearPendingJump resets pendingJumpLine', () {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      cubit.jumpToLine(5);
      expect(cubit.state.pendingJumpLine, 5);
      cubit.clearPendingJump();
      expect(cubit.state.pendingJumpLine, isNull);
      cubit.close();
    });

    test('multiple text changes work sequentially', () {
      final cubit = WritingReviewCubit();
      cubit.textChanged('a');
      expect(cubit.state.text, 'a');
      cubit.textChanged('ab');
      expect(cubit.state.text, 'ab');
      cubit.textChanged('abc');
      expect(cubit.state.text, 'abc');
      expect(cubit.state.charCount, 3);
      cubit.close();
    });

    test('loadSample can be called multiple times', () {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      expect(cubit.state.analysis, isNotNull);
      final firstScore = cubit.state.avgScore;
      cubit.textChanged('modified');
      cubit.loadSample();
      expect(cubit.state.analysis, isNotNull);
      expect(cubit.state.avgScore, firstScore);
      cubit.close();
    });
  });
}
