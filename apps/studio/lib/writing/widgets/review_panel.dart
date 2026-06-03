import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/writing_review_cubit.dart';
import '../theme/writing_theme.dart';
import 'review_tab.dart';
import 'reflect_tab.dart';
import 'rewrite_tab.dart';

class ReviewPanel extends StatelessWidget {
  const ReviewPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<WritingReviewCubit, WritingReviewState>(
      builder: (context, state) {
        final c = context.read<WritingReviewCubit>();
        final tabNames = {
          ReviewPanelTab.review: '📋 评审',
          ReviewPanelTab.reflect: '🎯 情境',
          ReviewPanelTab.rewrite: '✏️ 改写',
        };

        return Container(
          width: 300,
          color: WritingColors.surface,
          child: Column(
            children: [
              _PhaseBar(cubit: c, state: state),
              _TabBar(cubit: c, currentTab: state.currentTab, tabNames: tabNames),
              Expanded(
                child: _TabContent(cubit: c, currentTab: state.currentTab),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _PhaseBar extends StatelessWidget {
  final WritingReviewCubit cubit;
  final WritingReviewState state;

  const _PhaseBar({required this.cubit, required this.state});

  @override
  Widget build(BuildContext context) {
    final phaseLabel = 'Review';
    final phaseColor = WritingColors.accent;
    final bgColor = const Color(0xFF2b3a5e);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: WritingColors.border)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              phaseLabel,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: phaseColor,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '轮次 ',
            style: TextStyle(fontSize: 11, color: WritingColors.textDim),
          ),
          Text(
            '${state.round}',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.text,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '评分 ',
            style: TextStyle(fontSize: 11, color: WritingColors.textDim),
          ),
          Text(
            state.analysis != null ? '${state.avgScore.round()}' : '—',
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

class _TabBar extends StatelessWidget {
  final WritingReviewCubit cubit;
  final ReviewPanelTab currentTab;
  final Map<ReviewPanelTab, String> tabNames;

  const _TabBar({
    required this.cubit,
    required this.currentTab,
    required this.tabNames,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: WritingColors.border)),
      ),
      child: Row(
        children: ReviewPanelTab.values.map((t) {
          final isActive = t == currentTab;
          return Expanded(
            child: GestureDetector(
              onTap: () => cubit.switchTab(t),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: isActive ? WritingColors.accent : Colors.transparent,
                      width: 2,
                    ),
                  ),
                ),
                  child: Text(
                    tabNames[t]!,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isActive ? WritingColors.accent : WritingColors.textDim,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _TabContent extends StatelessWidget {
  final WritingReviewCubit cubit;
  final ReviewPanelTab currentTab;

  const _TabContent({required this.cubit, required this.currentTab});

  @override
  Widget build(BuildContext context) {
    switch (currentTab) {
      case ReviewPanelTab.review:
        return ReviewTab(cubit: cubit);
      case ReviewPanelTab.reflect:
        return ReflectTab(cubit: cubit);
      case ReviewPanelTab.rewrite:
        return RewriteTab(cubit: cubit);
    }
  }
}
