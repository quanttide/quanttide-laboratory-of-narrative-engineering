import 'dart:math';
import '../models/analysis.dart';

class AnalysisEngine {
  static final _timeRE = RegExp(r'第二天|过了一会儿|不久之后|次日');
  static final _dialogRE = RegExp(r'["「『]');
  static final _dialogCRE = RegExp(r'[」』"]');
  static final _transRE =
      RegExp(r'(不知不觉|恍然|猛然|突然).{0,6}(间|地)|回过神来');
  static final _actRE = RegExp(
      r'推开|走进|走出|坐下|站起|转身|拿起|放下|打开|关上|递|接|碰|触|擦|抹|伸|拉|走|站|坐');
  static final _emotionRE = RegExp(
      r'(欣喜|悲伤|愤怒|尴尬|开心|难过|激动|焦虑|平静|紧张|兴奋|失望|沮丧|羞怯|沉重|胆怯|燥热)地');
  static final _stateEndRE = RegExp(r'忘不了|还没|不$|…|……|突然');

  static AnalysisResult analyze(String text) {
    final lines = text.split('\n');
    final gaps = <Gap>[];
    var act = 0;
    var dia = 0;
    final emotionHits = <EmotionHit>[];

    for (var i = 0; i < lines.length; i++) {
      final s = lines[i].trim();
      if (s.isEmpty) continue;
      final ln = i + 1;

      if (_timeRE.hasMatch(s)) {
        gaps.add(Gap(
          line: ln,
          score: 3,
          type: GapType.timeJump,
          label: '时间跳跃',
        ));
      }

      if (_dialogRE.hasMatch(s)) {
        dia++;
        for (var j = i - 1; j >= max(0, i - 6); j--) {
          final p = lines[j].trim();
          if (p.isEmpty) continue;
          if (_dialogCRE.hasMatch(p) && !_actRE.hasMatch(s)) {
            gaps.add(Gap(
              line: ln,
              score: 2,
              type: GapType.dialogGap,
              label: '对话间隙',
            ));
          }
          break;
        }
      }

      if (_actRE.hasMatch(s)) {
        act++;
        for (var j = i - 1; j >= max(0, i - 6); j--) {
          final p = lines[j].trim();
          if (p.isEmpty) continue;
          if (_actRE.hasMatch(p)) {
            gaps.add(Gap(
              line: ln,
              score: 3,
              type: GapType.actionGap,
              label: '动作空隙',
            ));
          }
          break;
        }
      }

      if (_transRE.hasMatch(s)) {
        gaps.add(Gap(
          line: ln,
          score: 2,
          type: GapType.transitionCompression,
          label: '过渡压缩',
        ));
      }

      final em = _emotionRE.firstMatch(s);
      if (em != null) {
        emotionHits.add(EmotionHit(
          line: ln,
          text: s.length > 40 ? s.substring(0, 40) : s,
          word: em.group(0)!,
        ));
      }
    }

    final total = lines.where((l) => l.trim().isNotEmpty).length;
    final actPct = total > 0 ? (act / total * 100).round() : 0;

    final styles = [
      StyleScore(
          name: '对话→动作', score: min(100, actPct * 2).toDouble()),
      StyleScore(
        name: '状态句结尾',
        score: _stateEndRE.hasMatch(
                lines.skip(max(0, lines.length - 3)).join(''))
            ? 100
            : 30,
      ),
      StyleScore(
          name: '半秒钟密度',
          score: min(100, gaps.length * 20).toDouble()),
    ];

    final avg = styles.fold(0.0, (sum, s) => sum + s.score) / styles.length;

    final situations = _genSits(gaps);
    final rewrites = _genRewrites(text, emotionHits, act, dia);

    return AnalysisResult(
      gaps: gaps,
      styles: styles,
      avgScore: avg,
      emotionHits: emotionHits,
      situations: situations,
      rewrites: rewrites,
      actCount: act,
      dialogCount: dia,
    );
  }

  static List<Situation> _genSits(List<Gap> gaps) {
    return gaps
        .where((g) => g.score >= 2)
        .map((g) => Situation(
              line: g.line,
              type: g.type,
              label: g.label,
              guide: 'L${g.line} ${g.type.guide}',
            ))
        .toList();
  }

  static List<RewriteSuggestion> _genRewrites(
    String text,
    List<EmotionHit> emotionHits,
    int act,
    int dia,
  ) {
    final suggestions = <RewriteSuggestion>[];

    for (final e in emotionHits) {
      suggestions.add(RewriteSuggestion(
        line: e.line,
        location: 'L${e.line} · 情绪标签',
        original: '"${e.text}"',
        suggestion:
            '用身体动作替代「${e.word}」：试试删除这个副词，让读者从动作中感受情绪。',
      ));
    }

    final lines = text.split('\n');
    final last3 = lines.skip(max(0, lines.length - 3)).where((l) => l.trim().isNotEmpty).join('');
    if (!_stateEndRE.hasMatch(last3)) {
      suggestions.add(RewriteSuggestion(
        line: max(1, lines.length),
        location: '结尾 · 状态句',
        original: last3.length > 30 ? last3.substring(0, 30) : last3,
        suggestion:
            '结尾落在情节推进上。试试停在更紧张的时刻——用一个未化解的动作或感受收束。',
      ));
    }

    final total = act + dia;
    if (total > 0 && act / total < 0.4) {
      suggestions.add(RewriteSuggestion(
        line: 1,
        location: '全文 · 对话偏多',
        original: '动作 $act 行 / 对话 $dia 行',
        suggestion:
            '对话占比偏高。找一处纯对白段落，在角色说话之间插入一个身体动作。',
      ));
    }

    return suggestions;
  }
}
