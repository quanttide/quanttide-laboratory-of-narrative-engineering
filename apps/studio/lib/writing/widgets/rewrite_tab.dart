import 'package:flutter/material.dart';
import '../bloc/writing_review_cubit.dart';
import '../theme/writing_theme.dart';
import 'guide_card.dart';

class RewriteTab extends StatelessWidget {
  final WritingReviewCubit cubit;

  const RewriteTab({super.key, required this.cubit});

  @override
  Widget build(BuildContext context) {
    final rewrites = cubit.state.analysis?.rewrites ?? [];
    if (rewrites.isEmpty) {
      return const Center(
        child: Text(
          '暂无改写建议。',
          style: TextStyle(fontSize: 12, color: WritingColors.textDim),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(10),
      children: [
        const Text(
          '改写建议',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: WritingColors.textDim,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 8),
        ...rewrites.map((r) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: GuideCard.rewrite(
                r,
                onJumpTo: () => cubit.jumpToLine(r.line),
              ),
            )),
      ],
    );
  }
}
