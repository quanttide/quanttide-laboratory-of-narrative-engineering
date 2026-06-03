class DeepParagraphReview {
  final String original;
  final String analysis;
  final String tag;
  final DeepComparison? comparison;

  DeepParagraphReview({
    required this.original,
    required this.analysis,
    required this.tag,
    this.comparison,
  });

  factory DeepParagraphReview.fromJson(Map<String, dynamic> json) {
    return DeepParagraphReview(
      original: json['original'],
      analysis: json['analysis'],
      tag: json['tag'],
      comparison: json['comparison'] != null
          ? DeepComparison.fromJson(json['comparison'])
          : null,
    );
  }
}

class DeepComparison {
  final String type;
  final String? issue;
  final String? demo;

  DeepComparison({required this.type, this.issue, this.demo});

  factory DeepComparison.fromJson(Map<String, dynamic> json) {
    return DeepComparison(
      type: json['type'],
      issue: json['issue'],
      demo: json['demo'],
    );
  }
}

class DeepSuggestion {
  final int priority;
  final String action;
  final String detail;

  DeepSuggestion({required this.priority, required this.action, required this.detail});

  factory DeepSuggestion.fromJson(Map<String, dynamic> json) {
    return DeepSuggestion(
      priority: json['priority'],
      action: json['action'],
      detail: json['detail'],
    );
  }
}

class DeepReview {
  final String articleTitle;
  final String author;
  final String tag;
  final String summary;
  final List<DeepParagraphReview> paragraphs;
  final bool isStyleAvailable;
  final List<DeepSuggestion> suggestions;

  DeepReview({
    required this.articleTitle,
    required this.author,
    required this.tag,
    required this.summary,
    required this.paragraphs,
    required this.isStyleAvailable,
    required this.suggestions,
  });

  factory DeepReview.fromJson(Map<String, dynamic> json) {
    return DeepReview(
      articleTitle: json['article_title'],
      author: json['author'],
      tag: json['tag'],
      summary: json['summary'],
      paragraphs: (json['paragraphs'] as List)
          .map((p) => DeepParagraphReview.fromJson(p))
          .toList(),
      isStyleAvailable: json['is_style_available'],
      suggestions: (json['suggestions'] as List)
          .map((s) => DeepSuggestion.fromJson(s))
          .toList(),
    );
  }
}
