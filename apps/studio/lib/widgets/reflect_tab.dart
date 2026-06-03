import 'package:flutter/material.dart';
import '../blocs/writing_review_cubit.dart';
import '../themes/writing_theme.dart';
import 'guide_card.dart';

class ReflectTab extends StatelessWidget {
  final WritingReviewCubit cubit;

  const ReflectTab({super.key, required this.cubit});

  @override
  Widget build(BuildContext context) {
    final situations = cubit.state.analysis?.situations ?? [];
    if (situations.isEmpty) {
      return const Center(
        child: Text(
          '暂无识别到的可写位置。',
          style: TextStyle(fontSize: 12, color: WritingColors.textDim),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(10),
      children: [
        const Text(
          '可写位置',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: WritingColors.textDim,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 8),
        ...situations.map((s) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: GuideCard.situation(
                s,
                onJumpTo: () => cubit.jumpToLine(s.line),
              ),
            )),
      ],
    );
  }
}
