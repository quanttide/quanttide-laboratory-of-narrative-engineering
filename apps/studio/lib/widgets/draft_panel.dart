import 'package:flutter/material.dart';
import '../themes/writing_theme.dart';

class DraftPanel extends StatelessWidget {
  final VoidCallback onLoadSample;
  final bool hasContent;

  const DraftPanel({
    super.key,
    required this.onLoadSample,
    required this.hasContent,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      color: WritingColors.surface,
      child: Column(
        children: [
          _Section(
            title: '📄 底稿',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _ArticleItem(
                  icon: '✎',
                  name: '咖啡厅重逢',
                  status: hasContent ? '当前' : null,
                  isActive: true,
                ),
                const SizedBox(height: 8),
                GestureDetector(
                  onTap: onLoadSample,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 5),
                    decoration: BoxDecoration(
                      color: WritingColors.surface2,
                      border: Border.all(color: WritingColors.border),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      '加载测试底稿',
                      style: TextStyle(fontSize: 11, color: WritingColors.text),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final Widget child;

  const _Section({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: WritingColors.textDim,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 6),
          child,
        ],
      ),
    );
  }
}

class _ArticleItem extends StatelessWidget {
  final String icon;
  final String name;
  final String? status;
  final bool isActive;

  const _ArticleItem({
    required this.icon,
    required this.name,
    this.status,
    required this.isActive,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(icon, style: const TextStyle(fontSize: 12, color: WritingColors.text)),
        const SizedBox(width: 6),
        Text(
          name,
          style: TextStyle(
            fontSize: 12,
            color: isActive ? WritingColors.accent : WritingColors.text,
            fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
        if (status != null) ...[
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 5),
            decoration: BoxDecoration(
              color: WritingColors.surface2,
              borderRadius: BorderRadius.circular(3),
            ),
            child: Text(
              status!,
              style: const TextStyle(fontSize: 10, color: WritingColors.textDim),
            ),
          ),
        ],
      ],
    );
  }
}
