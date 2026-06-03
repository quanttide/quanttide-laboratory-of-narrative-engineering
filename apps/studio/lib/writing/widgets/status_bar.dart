import 'package:flutter/material.dart';
import '../bloc/writing_review_cubit.dart';
import '../theme/writing_theme.dart';

class StatusBar extends StatelessWidget {
  final WritingReviewCubit cubit;

  const StatusBar({super.key, required this.cubit});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 26,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: WritingColors.surface,
        border: Border(top: BorderSide(color: WritingColors.border)),
      ),
      child: Row(
        children: [
          Text(
            '字数 ',
            style: TextStyle(fontSize: 11, color: WritingColors.textDim),
          ),
          Text(
            '${cubit.state.charCount}',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.text,
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '空隙 ',
            style: TextStyle(fontSize: 11, color: WritingColors.textDim),
          ),
          Text(
            '${cubit.state.gapCount}',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.text,
            ),
          ),
        ],
      ),
    );
  }
}
