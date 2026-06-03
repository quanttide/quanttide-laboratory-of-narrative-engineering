import 'package:flutter/material.dart';
import '../themes/writing_theme.dart';
import '../models/analysis.dart';

class GuideCard extends StatelessWidget {
  final String location;
  final String guide;
  final String buttonLabel;
  final Color accentColor;
  final VoidCallback onAction;

  const GuideCard({
    super.key,
    required this.location,
    required this.guide,
    required this.buttonLabel,
    required this.accentColor,
    required this.onAction,
  });

  factory GuideCard.situation(Situation s, {required VoidCallback onJumpTo}) {
    return GuideCard(
      location: 'L${s.line} · ${s.label}',
      guide: s.guide,
      buttonLabel: '✎ 写在这里',
      accentColor: WritingColors.accent2,
      onAction: onJumpTo,
    );
  }

  factory GuideCard.rewrite(RewriteSuggestion r, {required VoidCallback onJumpTo}) {
    return GuideCard(
      location: r.location,
      guide: '${r.original}\n${r.suggestion}',
      buttonLabel: '✎ 定位到此处',
      accentColor: WritingColors.accent3,
      onAction: onJumpTo,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: WritingColors.surface2,
        borderRadius: BorderRadius.circular(8),
        border: Border(left: BorderSide(color: accentColor, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            location,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: accentColor,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            guide,
            style: const TextStyle(
              fontSize: 12,
              height: 1.6,
              color: WritingColors.text,
            ),
          ),
          const SizedBox(height: 6),
          GestureDetector(
            onTap: onAction,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 5),
              decoration: BoxDecoration(
                border: Border.all(color: accentColor),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                buttonLabel,
                style: TextStyle(fontSize: 11, color: accentColor),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
