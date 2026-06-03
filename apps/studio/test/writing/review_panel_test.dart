import 'package:flutter/material.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/review_panel.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MaterialApp(
    home: Scaffold(
      body: BlocProvider.value(
        value: cubit,
        child: const ReviewPanel(),
      ),
    ),
  );
}

void main() {
  group('ReviewPanel', () {
    testWidgets('shows phase bar and tabs', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.text('Review'), findsOneWidget);
      expect(find.text('轮次'), findsOneWidget);
      expect(find.text('评分'), findsOneWidget);
      expect(find.text('📋 评审'), findsOneWidget);
      expect(find.text('🎯 情境'), findsOneWidget);
      expect(find.text('✏️ 改写'), findsOneWidget);
      cubit.close();
    });
  });
}
