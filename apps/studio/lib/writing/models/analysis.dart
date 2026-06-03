enum GapType { timeJump, dialogGap, actionGap, transitionCompression }

extension GapTypeX on GapType {
  String get label {
    switch (this) {
      case GapType.timeJump:
        return '时间跳跃';
      case GapType.dialogGap:
        return '对话间隙';
      case GapType.actionGap:
        return '动作空隙';
      case GapType.transitionCompression:
        return '过渡压缩';
    }
  }

  String get guide {
    switch (this) {
      case GapType.timeJump:
        return '跳过了这段时间。\n房间里有什么声音？光线有变化吗？角色在这段时间里做了什么？';
      case GapType.dialogGap:
        return '对白之间有一段沉默。\n说话的人在开口前做了什么？吞咽了一下？看向了别处？沉默不是空白——它是角色正在处理情绪的物理时间。';
      case GapType.actionGap:
        return '两个动作之间缺少过渡。\n第一个动作结束时，角色的手在哪？呼吸节奏怎样？半秒钟——够一个人改变主意，也够一个人下定决心。';
      case GapType.transitionCompression:
        return '时间被压缩了。\n把它展开，让读者体验每一秒——发生了什么细节？';
    }
  }
}

class Gap {
  final int line;
  final int score;
  final GapType type;
  final String label;
  Gap({
    required this.line,
    required this.score,
    required this.type,
    required this.label,
  });
}

class StyleScore {
  final String name;
  final double score;
  StyleScore({required this.name, required this.score});
}

class EmotionHit {
  final int line;
  final String text;
  final String word;
  EmotionHit({required this.line, required this.text, required this.word});
}

class Situation {
  final int line;
  final GapType type;
  final String label;
  final String guide;
  Situation({
    required this.line,
    required this.type,
    required this.label,
    required this.guide,
  });
}

class RewriteSuggestion {
  final int line;
  final String location;
  final String original;
  final String suggestion;
  RewriteSuggestion({
    required this.line,
    required this.location,
    required this.original,
    required this.suggestion,
  });
}

class AnalysisResult {
  final List<Gap> gaps;
  final List<StyleScore> styles;
  final double avgScore;
  final List<EmotionHit> emotionHits;
  final List<Situation> situations;
  final List<RewriteSuggestion> rewrites;
  final int actCount;
  final int dialogCount;

  AnalysisResult({
    required this.gaps,
    required this.styles,
    required this.avgScore,
    required this.emotionHits,
    required this.situations,
    required this.rewrites,
    required this.actCount,
    required this.dialogCount,
  });
}
