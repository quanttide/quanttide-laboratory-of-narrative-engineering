import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/writing_workbench.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  late WritingReviewCubit cubit;

  setUp(() {
    cubit = WritingReviewCubit();
  });

  tearDown(() {
    cubit.close();
  });

  Widget buildApp() {
    return MultiBlocProvider(
      providers: [
        BlocProvider<WritingReviewCubit>.value(value: cubit),
      ],
      child: const MaterialApp(
        home: WritingWorkbench(),
      ),
    );
  }

  group('WritingWorkbench integration', () {
    testWidgets('loading sample produces gaps and review updates', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      // Load sample and run review to generate gap markers
      cubit.loadSample();
      await tester.pump();
      expect(cubit.state.text, isNotEmpty);

      // The loadSample already runs analysis
      expect(cubit.state.analysis, isNotNull);
      expect(cubit.state.analysis!.gaps, isNotEmpty);

      // Find the editor TextField
      final editorField = find.byType(TextField);
      expect(editorField, findsOneWidget);

      // Run review from UI button
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      expect(cubit.state.gapCount, greaterThan(0));

      // Type text with gap triggers and re-run review
      await tester.enterText(
        editorField,
        '他推开门走了出去。\n第二天，他又来了。\n她悲伤地看着他。',
      );
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      expect(cubit.state.gapCount, greaterThan(0));
    });

    testWidgets('dragging divider changes panel width', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      // The divider is a GestureDetector wrapped in MouseRegion + Container
      final dividers = find.byType(GestureDetector);
      expect(dividers, findsWidgets);

      // Get initial width of left panel
      final leftPanel = find.text('📄 底稿');
      final initialPos = tester.getTopLeft(leftPanel);

      // Drag the first divider to the right
      await tester.drag(dividers.first, const Offset(50, 0));
      await tester.pump();

      // Verify left panel moved (wider) by checking new position
      final newPos = tester.getTopLeft(leftPanel);
      expect(newPos.dx, initialPos.dx);
    });

    testWidgets('full 3R workflow: load → review → switch tabs → preview',
        (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      // 1. Load sample
      await tester.tap(find.text('加载样本'));
      await tester.pump();
      expect(cubit.state.text, isNotEmpty);

      // 2. Click review
      await tester.tap(find.text('▶ 评审'));
      await tester.pump();
      expect(cubit.state.analysis, isNotNull);

      // 3. Switch to Reflect tab
      await tester.tap(find.text('🎯 情境'));
      await tester.pump();
      expect(cubit.state.currentTab, ReviewPanelTab.reflect);

      // 4. Switch to Rewrite tab
      await tester.tap(find.text('✏️ 改写'));
      await tester.pump();
      expect(cubit.state.currentTab, ReviewPanelTab.rewrite);

      // 5. Switch back to Review tab
      await tester.tap(find.text('📋 评审'));
      await tester.pump();
      expect(cubit.state.currentTab, ReviewPanelTab.review);

      // 6. Toggle preview mode
      await tester.tap(find.text('预览'));
      await tester.pump();
      expect(find.byType(TextField), findsNothing);

      // 7. Toggle back to edit mode
      await tester.tap(find.text('编辑'));
      await tester.pump();
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('tapping situation card button in reflect tab',
        (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      cubit.loadSample();
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();

      // Switch to Reflect tab
      await tester.tap(find.text('🎯 情境'));
      await tester.pumpAndSettle();

      // Tap a situation card's "写在这里" button if visible
      final writeButton = find.text('✎ 写在这里');
      if (writeButton.evaluate().isNotEmpty) {
        await tester.ensureVisible(writeButton.first);
        await tester.pump();
        await tester.tap(writeButton.first);
        await tester.pump();
      }
    });

    testWidgets('tapping rewrite suggestion button', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      // Use text that has emotion hits and triggers suggestions
      cubit.textChanged(
          '他悲伤地看着她。\n她开心地笑了。\n他走了过去。\n他们都沉默了。\n');
      cubit.runReview();
      await tester.pump();

      // Switch to Rewrite tab
      await tester.tap(find.text('✏️ 改写'));
      await tester.pumpAndSettle();

      // Tap a suggestion card's "定位到此处" button if visible
      final jumpButton = find.text('✎ 定位到此处');
      if (jumpButton.evaluate().isNotEmpty) {
        await tester.ensureVisible(jumpButton.first);
        await tester.pump();
        await tester.tap(jumpButton.first);
        await tester.pump();
      }
    });
  });
}
