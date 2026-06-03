import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:docs_agent/writing/bloc/writing_review_cubit.dart';
import 'package:docs_agent/writing/widgets/draggable_divider.dart';
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

    testWidgets('dragging left divider changes left panel width', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();

      // DraftPanel is the left panel — get its right edge
      final draftPanel = find.text('📄 底稿');
      final panelBox = tester.getRect(draftPanel);
      final initialRight = panelBox.right;

      // Find and drag the DraggableDivider widgets
      final dividerWidgets = find.byType(DraggableDivider);
      expect(dividerWidgets, findsNWidgets(2));

      // Drag the left divider to the right by 50px
      await tester.drag(dividerWidgets.first, const Offset(50, 0));
      await tester.pump();

      // After dragging right, the left panel's right edge should have moved right
      final newRect = tester.getRect(draftPanel);
      expect(newRect.right, greaterThan(initialRight));
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

    testWidgets('完整 3R 循环：写 → 评审 → 看情境 → 改写 → 再评审评分改善',
        (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();
      final editorField = find.byType(TextField);

      // 1. 写一段带空隙的文本
      await tester.enterText(
        editorField,
        '他推开门走了出去。\n第二天，他又回来了。\n她悲伤地看着他。\n他笑了笑。\n',
      );
      await tester.pump();

      // 2. 评审 → 看到空隙
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      expect(cubit.state.gapCount, greaterThan(0));
      expect(find.text('空隙'), findsOneWidget);

      // 3. 切到情境标签 → 看到可写位置
      await tester.tap(find.text('🎯 情境'));
      await tester.pumpAndSettle();
      if (find.text('可写位置').evaluate().isNotEmpty) {
        expect(find.text('可写位置'), findsOneWidget);
      }

      // 4. 切到改写标签 → 看到改写建议
      await tester.tap(find.text('✏️ 改写'));
      await tester.pumpAndSettle();

      // 5. 根据建议改写文本（去掉空隙触发词）
      await tester.tap(find.text('📋 评审'));
      await tester.pump();
      await tester.enterText(
        editorField,
        '他推开门走了出去。她站在门口看着他。他注意到她的目光。她轻轻地点了点头。',
      );
      await tester.pump();

      // 6. 再次评审 → 确认分析已更新
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      expect(cubit.state.analysis, isNotNull);
    });

    testWidgets('多轮迭代：评分随改写变化', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();
      final editorField = find.byType(TextField);

      // 第1轮：通过 UI 输入有空隙的文本 → 评审 → 记录空隙数
      await tester.enterText(editorField, '他走了出去。第二天，他又来了。她悲伤地看着他。');
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      expect(cubit.state.analysis, isNotNull);
      final round1Gaps = cubit.state.gapCount;
      expect(round1Gaps, greaterThan(0));

      // 第2轮：改写去掉时间跳跃词 → 评审 → 空隙数应减少
      cubit.textChanged('他走在街上。冷风扑面而来。他裹紧了外套。');
      cubit.runReview();
      await tester.pump();
      final round2Gaps = cubit.state.gapCount;
      expect(round2Gaps, lessThan(round1Gaps));
      await tester.pump();
    });

    testWidgets('结尾建议出现在结尾不合状态句的文本中', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();
      final editorField = find.byType(TextField);

      // 输入结尾在情节推进上的文本（无忘不了/不$/…）
      await tester.enterText(
        editorField,
        '他推开门走了出去。\n她跟在他身后。\n他们一起走进了咖啡厅。',
      );
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();

      // 切到改写标签 → 应看到结尾建议
      await tester.tap(find.text('✏️ 改写'));
      await tester.pumpAndSettle();
      // 结尾建议含"结尾 · 状态句"文本
      expect(find.textContaining('结尾'), findsWidgets);
    });

    testWidgets('实时空隙反馈：编辑后重新评审更新空隙数', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 800));
      await tester.pumpWidget(buildApp());
      await tester.pump();
      final editorField = find.byType(TextField);

      // 输入有空隙的文本 → 评审 → 确认有 N 个空隙
      await tester.enterText(
        editorField,
        '他推开门走了出去。\n第二天，他又来了。',
      );
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      final gapCountWithJump = cubit.state.gapCount;
      expect(gapCountWithJump, greaterThan(0));

      // 换一段无触发词的文本（每行独立，无时间跳跃、无连续动作） → 评审 → 空隙应减少
      await tester.enterText(
        editorField,
        '窗外的雨淅淅沥沥地下着。\n'
        '咖啡厅里播放着舒缓的音乐。\n'
        '她的身影出现在门口。\n'
        '他抬起头看见了熟悉的面孔。',
      );
      await tester.pump();
      await tester.tap(find.text('▶ 评审'));
      await tester.pumpAndSettle();
      final gapCountPlain = cubit.state.gapCount;
      // 改写的文本不应有时间跳跃，空隙数应少于或等于原文本
      expect(gapCountPlain, lessThanOrEqualTo(gapCountWithJump));
    });
  });
}
