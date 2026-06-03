import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/editor_panel.dart';
import 'package:docs_agent/writing/widgets/gap_markers_column.dart';

Widget _buildApp(WritingReviewCubit cubit) {
  return MaterialApp(
    home: Scaffold(
      body: EditorPanel(cubit: cubit),
    ),
  );
}

void main() {
  group('EditorPanel', () {
    testWidgets('shows text field and toolbar', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.byType(TextField), findsOneWidget);
      expect(find.textContaining('空隙'), findsOneWidget);
      expect(find.text('编辑'), findsOneWidget);
      expect(find.text('预览'), findsOneWidget);
      cubit.close();
    });

    testWidgets('shows gap count from analysis', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他来了。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.textContaining('1'), findsWidgets);
      cubit.close();
    });

    testWidgets('switches to preview mode', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.tap(find.text('预览'));
      await tester.pump();
      expect(find.byType(TextField), findsNothing);
      cubit.close();
    });

    testWidgets('switches back to edit mode', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.loadSample();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.tap(find.text('预览'));
      await tester.pump();
      await tester.tap(find.text('编辑'));
      await tester.pump();
      expect(find.byType(TextField), findsOneWidget);
      cubit.close();
    });

    testWidgets('typing text updates cubit', (tester) async {
      final cubit = WritingReviewCubit();
      await tester.pumpWidget(_buildApp(cubit));
      await tester.enterText(find.byType(TextField), 'hello');
      expect(cubit.state.text, 'hello');
      cubit.close();
    });

    testWidgets('hides gap count in preview mode', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('test');
      await tester.pumpWidget(_buildApp(cubit));
      expect(find.textContaining('空隙'), findsOneWidget);
      await tester.tap(find.text('预览'));
      await tester.pump();
      expect(find.textContaining('空隙'), findsNothing);
      cubit.close();
    });

    testWidgets('gap markers column is tappable', (tester) async {
      final cubit = WritingReviewCubit();
      cubit.textChanged('第二天，他走了出去。\n她走了进来。');
      cubit.runReview();
      await tester.pumpWidget(_buildApp(cubit));
      final markers = find.byType(GapMarkersColumn);
      expect(markers, findsOneWidget);
      // Tapping in the gap markers area should not throw
      await tester.tapAt(
        tester.getTopLeft(markers).translate(9, 40),
      );
      cubit.close();
    });
  });
}
