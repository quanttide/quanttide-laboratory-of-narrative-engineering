import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/blocs/writing_review_cubit.dart';

void main() {
  group('WritingReviewCubit deep analysis', () {
    test('runDeepAnalysis with no service sets error', () async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('test text');
      await cubit.runDeepAnalysis();
      expect(cubit.state.deepError, contains('未配置'));
      expect(cubit.state.isDeepAnalyzing, isFalse);
      cubit.close();
    });

    test('runDeepAnalysis with empty text does nothing', () async {
      final cubit = WritingReviewCubit();
      await cubit.runDeepAnalysis();
      expect(cubit.state.deepAnalysis, isNull);
      expect(cubit.state.deepError, isNull);
      cubit.close();
    });

    test('initial deep analysis state is null', () {
      final cubit = WritingReviewCubit();
      expect(cubit.state.deepAnalysis, isNull);
      expect(cubit.state.isDeepAnalyzing, isFalse);
      expect(cubit.state.deepError, isNull);
      cubit.close();
    });
  });
}
