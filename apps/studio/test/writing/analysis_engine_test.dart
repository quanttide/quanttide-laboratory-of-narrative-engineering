import 'package:flutter_test/flutter_test.dart';
import 'package:docs_agent/writing/models/analysis.dart';
import 'package:docs_agent/writing/services/analysis_engine.dart';

void main() {
  group('AnalysisEngine.analyze', () {
    test('returns empty result for empty text', () {
      final result = AnalysisEngine.analyze('');
      expect(result.gaps, isEmpty);
      expect(result.styles, hasLength(3));
      expect(result.avgScore, 10.0);
      expect(result.emotionHits, isEmpty);
    });

    test('detects time jump gaps', () {
      const text = '他打开门走了出去。\n第二天，他回到了这里。\n他坐了下来。';
      final result = AnalysisEngine.analyze(text);
      expect(result.gaps.any((g) => g.type == GapType.timeJump), isTrue);
      expect(result.gaps.any((g) => g.label == '时间跳跃'), isTrue);
    });

    test('detects dialog gaps', () {
      const text = '"你好"\n她笑了笑说"再见"\n"你还好吗"';
      final result = AnalysisEngine.analyze(text);
      expect(result.gaps.any((g) => g.type == GapType.dialogGap), isTrue);
    });

    test('detects action gaps', () {
      const text = '他推开窗户\n她推开门\n他坐了下来';
      final result = AnalysisEngine.analyze(text);
      expect(result.gaps.any((g) => g.type == GapType.actionGap), isTrue);
    });

    test('detects transition compression gaps', () {
      const text = '他站在窗前。\n不知不觉间，天已经亮了。\n他转身离开。';
      final result = AnalysisEngine.analyze(text);
      expect(result.gaps.any((g) => g.type == GapType.transitionCompression), isTrue);
    });

    test('detects emotion hits', () {
      const text = '她悲伤地看着他。\n他开心地笑了。';
      final result = AnalysisEngine.analyze(text);
      expect(result.emotionHits, hasLength(2));
      expect(result.emotionHits[0].word, '悲伤地');
      expect(result.emotionHits[1].word, '开心地');
    });

    test('calculates style scores', () {
      const text = '他走了出去。\n她走了进来。\n他们拥抱在一起。';
      final result = AnalysisEngine.analyze(text);
      expect(result.styles, hasLength(3));
      expect(result.styles[0].name, '对话→动作');
      expect(result.avgScore, greaterThan(0));
    });

    test('generates situations for high-score gaps', () {
      const text = '他打开门走了出去。\n第二天，他回到了这里。';
      final result = AnalysisEngine.analyze(text);
      expect(result.situations, isNotEmpty);
      expect(result.situations.every((s) => s.line > 0), isTrue);
    });

    test('generates rewrite suggestions for emotion hits', () {
      const text = '他悲伤地看着她。\n她开心地回应。';
      final result = AnalysisEngine.analyze(text);
      expect(result.rewrites, isNotEmpty);
      expect(result.rewrites.any((r) => r.location.contains('情绪标签')), isTrue);
    });

    test('generates state-end rewrite suggestion', () {
      const text = '他走了过去。\n她看了他一眼。\n他们都沉默了。';
      final result = AnalysisEngine.analyze(text);
      expect(result.rewrites, isNotEmpty);
    });

    test('generates dialog-heavy rewrite suggestion', () {
      const text = '"你好吗"\n"我很好"\n"那就好"\n"嗯"\n"再见"\n"再见"';
      final result = AnalysisEngine.analyze(text);
      expect(result.rewrites.any((r) => r.location.contains('对话偏多')), isTrue);
    });

    test('avgScore is average of three style scores', () {
      const text = '他走了出去。\n第二天，他又来了。\n她悲伤地看着他。';
      final result = AnalysisEngine.analyze(text);
      expect(result.styles, hasLength(3));
      final expectedAvg =
          result.styles.fold(0.0, (sum, s) => sum + s.score) / 3;
      expect(result.avgScore, closeTo(expectedAvg, 0.01));
    });

    test('handles sample text without errors', () {
      const sample =
          '# 咖啡厅重逢\n\n春天的一个工作日的下午，咖啡店外下着淅淅沥沥的小雨。\n\n'
          '他愣神看着窗外的雨水沿着屋檐滑落到地面上。\n\n'
          '她拉着行李箱走出车站。\n\n'
          '她轻轻推开了咖啡店的门。\n\n'
          '不知不觉间，他的手已经伸了出去。\n\n'
          '他忘不了，也不想忘。';
      final result = AnalysisEngine.analyze(sample);
      expect(result.gaps, isNotEmpty);
      expect(result.styles, hasLength(3));
      expect(result.avgScore, greaterThan(0));
    });
  });
}
