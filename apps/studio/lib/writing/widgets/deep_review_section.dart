import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/writing_review_cubit.dart';
import '../models/deep_analysis.dart';
import '../theme/writing_theme.dart';

class DeepReviewSection extends StatelessWidget {
  const DeepReviewSection({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<WritingReviewCubit, WritingReviewState>(
      builder: (context, state) {
        if (state.isDeepAnalyzing) {
          return const Padding(
            padding: EdgeInsets.all(16),
            child: Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text('深度分析中...',
                      style: TextStyle(
                          fontSize: 12, color: WritingColors.textDim)),
                ],
              ),
            ),
          );
        }
        if (state.deepError != null) {
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Text(state.deepError!,
                style: const TextStyle(fontSize: 12, color: WritingColors.red)),
          );
        }
        if (state.deepAnalysis == null) return const SizedBox.shrink();
        return _DeepReviewContent(review: state.deepAnalysis!);
      },
    );
  }
}

class _DeepReviewContent extends StatelessWidget {
  final DeepReview review;
  const _DeepReviewContent({required this.review});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '深度分析',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.textDim,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            review.summary,
            style: const TextStyle(fontSize: 12, color: WritingColors.text, height: 1.5),
          ),
          const SizedBox(height: 8),
          if (review.paragraphs.isNotEmpty) ...[
            const Text(
              '段落结构',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: WritingColors.textDim,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: 6),
            ...review.paragraphs.map((p) => _ParaCard(p: p)),
          ],
          if (review.suggestions.isNotEmpty) ...[
            const SizedBox(height: 8),
            const Text(
              '改进建议',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: WritingColors.textDim,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: 6),
            ...review.suggestions.map((s) => _SuggestionItem(s: s)),
          ],
        ],
      ),
    );
  }
}

class _ParaCard extends StatelessWidget {
  final DeepParagraphReview p;
  const _ParaCard({required this.p});

  Color _tagColor(String tag) {
    switch (tag) {
      case '起':
        return WritingColors.accent;
      case '承':
        return WritingColors.accent2;
      case '转':
        return WritingColors.accent3;
      case '合':
        return WritingColors.red;
      default:
        return WritingColors.textDim;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tagColor = _tagColor(p.tag);
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: WritingColors.surface2,
        borderRadius: BorderRadius.circular(6),
        border: Border(left: BorderSide(color: tagColor, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: tagColor.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: Text(
                  p.tag,
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: tagColor),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  p.original.length > 60
                      ? '${p.original.substring(0, 60)}…'
                      : p.original,
                  style: const TextStyle(fontSize: 11, color: WritingColors.textDim),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            p.analysis,
            style: const TextStyle(fontSize: 11, color: WritingColors.text, height: 1.5),
          ),
          if (p.comparison != null && p.comparison!.type == 'bad') ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: WritingColors.red.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '问题: ${p.comparison!.issue ?? ""}\n示范: ${p.comparison!.demo ?? ""}',
                style: const TextStyle(fontSize: 10, color: WritingColors.red, height: 1.4),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _SuggestionItem extends StatelessWidget {
  final DeepSuggestion s;
  const _SuggestionItem({required this.s});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: WritingColors.surface2,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: WritingColors.accent.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(3),
            ),
            child: Text(
              'P${s.priority}',
              style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: WritingColors.accent),
            ),
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.action,
                  style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: WritingColors.text),
                ),
                Text(
                  s.detail,
                  style: const TextStyle(
                      fontSize: 11, color: WritingColors.textDim),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
