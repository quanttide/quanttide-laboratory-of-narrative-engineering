import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/models/analysis.dart';
import 'package:docs_agent/writing/widgets/guide_card.dart';

void main() {
  group('GuideCard.situation', () {
    testWidgets('renders situation card with location and guide', (tester) async {
      final situation = Situation(
        line: 5,
        type: GapType.timeJump,
        label: '时间跳跃',
        guide: 'L5 跳过了这段时间。',
      );

      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: GuideCard.situation(situation, onJumpTo: () {}),
        ),
      ));

      expect(find.text('L5 · 时间跳跃'), findsOneWidget);
      expect(find.text('L5 跳过了这段时间。'), findsOneWidget);
      expect(find.text('✎ 写在这里'), findsOneWidget);
    });

    testWidgets('calls onJumpTo when button is tapped', (tester) async {
      var jumped = false;
      final situation = Situation(
        line: 3,
        type: GapType.dialogGap,
        label: '对话间隙',
        guide: 'L3 对白之间有一段沉默。',
      );

      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: GuideCard.situation(situation, onJumpTo: () => jumped = true),
        ),
      ));

      await tester.tap(find.text('✎ 写在这里'));
      expect(jumped, isTrue);
    });
  });

  group('GuideCard.rewrite', () {
    testWidgets('renders rewrite card with location and suggestion', (tester) async {
      final suggestion = RewriteSuggestion(
        line: 10,
        location: 'L10 · 情绪标签',
        original: '"he looked at her"',
        suggestion: '用身体动作替代这个副词。',
      );

      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: GuideCard.rewrite(suggestion, onJumpTo: () {}),
        ),
      ));

      expect(find.text('L10 · 情绪标签'), findsOneWidget);
      expect(find.textContaining('用身体动作替代'), findsOneWidget);
      expect(find.text('✎ 定位到此处'), findsOneWidget);
    });

    testWidgets('calls onJumpTo when button is tapped', (tester) async {
      var jumped = false;
      final suggestion = RewriteSuggestion(
        line: 7,
        location: 'L7 · 情绪标签',
        original: 'test',
        suggestion: 'test suggestion',
      );

      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: GuideCard.rewrite(suggestion, onJumpTo: () => jumped = true),
        ),
      ));

      await tester.tap(find.text('✎ 定位到此处'));
      expect(jumped, isTrue);
    });
  });
}
