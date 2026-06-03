import 'package:flutter/material.dart';
import '../bloc/writing_review_cubit.dart';

class WritingAppBar extends StatelessWidget {
  final WritingReviewCubit cubit;

  const WritingAppBar({super.key, required this.cubit});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(bottom: BorderSide(color: colors.outline)),
      ),
      child: Row(
        children: [
          Text(
            '✎ 写作云',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: colors.primary,
              fontSize: 13,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '合成工作台',
            style: TextStyle(
              color: colors.onSurfaceVariant,
              fontSize: 11,
            ),
          ),
          const Spacer(),
          _AppBarButton(
            label: '▶ 评审',
            isPrimary: true,
            onPressed: () => cubit.runReview(),
          ),
          const SizedBox(width: 6),
          _AppBarButton(
            label: '🧠 深度分析',
            isPrimary: false,
            onPressed: () => cubit.runDeepAnalysis(),
          ),
          const SizedBox(width: 6),
          _AppBarButton(
            label: '加载样本',
            isPrimary: false,
            onPressed: () => cubit.loadSample(),
          ),
        ],
      ),
    );
  }
}

class _AppBarButton extends StatelessWidget {
  final String label;
  final bool isPrimary;
  final VoidCallback onPressed;

  const _AppBarButton({
    required this.label,
    required this.isPrimary,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
        decoration: BoxDecoration(
          color: isPrimary ? colors.primary : colors.surfaceContainerHigh,
          border: Border.all(color: isPrimary ? colors.primary : colors.outline),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: isPrimary ? colors.onPrimary : colors.onSurface,
          ),
        ),
      ),
    );
  }
}
