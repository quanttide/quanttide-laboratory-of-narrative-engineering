import 'package:flutter/material.dart';
import '../themes/writing_theme.dart';

class StyleBar extends StatelessWidget {
  final String name;
  final double score;

  const StyleBar({super.key, required this.name, required this.score});

  @override
  Widget build(BuildContext context) {
    final barColor = score >= 70
        ? WritingColors.accent2
        : score >= 40
            ? WritingColors.accent3
            : WritingColors.red;

    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(
            name,
            style: const TextStyle(fontSize: 12, color: WritingColors.textDim),
          ),
        ),
        Expanded(
          child: Container(
            height: 6,
            decoration: BoxDecoration(
              color: WritingColors.surface2,
              borderRadius: BorderRadius.circular(3),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: score / 100,
              child: Container(
                decoration: BoxDecoration(
                  color: barColor,
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 6),
        SizedBox(
          width: 24,
          child: Text(
            '${score.round()}',
            style: const TextStyle(fontSize: 12, color: WritingColors.textDim),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    );
  }
}
