import 'package:flutter/material.dart';
import '../blocs/writing_review_cubit.dart';
import '../models/analysis.dart';
import '../themes/writing_theme.dart';
import 'deep_review_section.dart';
import 'style_bar.dart';

class ReviewTab extends StatelessWidget {
  final WritingReviewCubit cubit;

  const ReviewTab({super.key, required this.cubit});

  @override
  Widget build(BuildContext context) {
    final analysis = cubit.state.analysis;
    if (analysis == null) {
      return const Center(
        child: Text(
          '等待评审...',
          style: TextStyle(fontSize: 12, color: WritingColors.textDim),
        ),
      );
    }

    final gaps = analysis.gaps;
    final styles = analysis.styles;

    return ListView(
      padding: const EdgeInsets.all(10),
      children: [
        if (gaps.isNotEmpty) ...[
          const Text(
            '空隙',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.textDim,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 4),
          ...gaps.take(10).map((g) => _GapItem(
                gap: g,
                onTap: () => cubit.jumpToLine(g.line),
              )),
          const SizedBox(height: 8),
        ],
        if (styles.isNotEmpty) ...[
          const Text(
            '风格',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.textDim,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 4),
          ...styles.map((s) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: StyleBar(name: s.name, score: s.score),
              )),
        ],
        const SizedBox(height: 8),
        Center(
          child: Text.rich(
            TextSpan(
              text: '${analysis.avgScore.round()} ',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: WritingColors.accent,
              ),
              children: const [
                TextSpan(
                  text: '/100',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w400,
                    color: WritingColors.textDim,
                  ),
                ),
              ],
            ),
          ),
        ),
        const Divider(height: 16, color: WritingColors.border),
        const DeepReviewSection(),
      ],
    );
  }
}

class _GapItem extends StatelessWidget {
  final Gap gap;
  final VoidCallback onTap;

  const _GapItem({required this.gap, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final dot = gap.score == 3
        ? '🟢'
        : gap.score == 2
            ? '🟡'
            : '🔴';
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          children: [
            Text(dot, style: const TextStyle(fontSize: 12)),
            const SizedBox(width: 6),
            SizedBox(
              width: 56,
              child: Text(
                gap.label,
                style: const TextStyle(fontSize: 12, color: WritingColors.textDim),
              ),
            ),
            const Spacer(),
            Text(
              'L${gap.line}',
              style: const TextStyle(fontSize: 11, color: WritingColors.textDim),
            ),
          ],
        ),
      ),
    );
  }
}
