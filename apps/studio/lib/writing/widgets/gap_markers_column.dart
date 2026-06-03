import 'package:flutter/material.dart';
import '../theme/writing_theme.dart';
import '../models/analysis.dart';

class GapMarkersColumn extends StatelessWidget {
  final List<Gap> gaps;
  final int lineCount;
  final void Function(int line) onJumpTo;

  static const double lineHeight = 25.2;

  const GapMarkersColumn({
    super.key,
    required this.gaps,
    required this.lineCount,
    required this.onJumpTo,
  });

  @override
  Widget build(BuildContext context) {
    final bestPerLine = <int, int>{};
    for (final g in gaps) {
      final existing = bestPerLine[g.line] ?? 0;
      if (g.score > existing) bestPerLine[g.line] = g.score;
    }

    return SizedBox(
      width: 18,
      child: Stack(
        children: [
          for (final entry in bestPerLine.entries)
            Positioned(
              top: 14.0 + (entry.key - 1) * lineHeight + 4,
              left: 0,
              right: 0,
              child: GestureDetector(
                onTap: () => onJumpTo(entry.key),
                child: Container(
                  height: 7,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _colorForScore(entry.value),
                    boxShadow: [
                      BoxShadow(
                        color: _colorForScore(entry.value).withValues(alpha: 0.4),
                        blurRadius: 2,
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Color _colorForScore(int score) {
    switch (score) {
      case 3:
        return WritingColors.accent;
      case 2:
        return WritingColors.accent3;
      default:
        return WritingColors.red;
    }
  }
}
