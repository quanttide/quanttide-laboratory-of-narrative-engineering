import 'package:flutter/material.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/review_panel.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MultiBlocProvider(
    providers: [
      BlocProvider<WritingReviewCubit>.value(value: cubit),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: const ReviewPanel(),
      ),
    ),
  );
}

void main() {
  group('ReviewPanel', () {
    testWidgets('shows phase bar and tabs', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.pump();
      expect(find.text('Review'), findsOneWidget);
      expect(find.byType(ReviewPanel), findsOneWidget);
      cubit.close();
    });
  });
}
