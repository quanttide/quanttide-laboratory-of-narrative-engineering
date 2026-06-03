import 'package:flutter/material.dart';
import '../theme/writing_theme.dart';

class DraggableDivider extends StatelessWidget {
  final bool isLeft;
  final ValueChanged<double> onDrag;

  const DraggableDivider({super.key, required this.isLeft, required this.onDrag});

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.resizeColumn,
      child: GestureDetector(
        onPanUpdate: (details) {
          onDrag(details.delta.dx);
        },
        child: Container(
          width: 4,
          color: Colors.transparent,
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 1),
            decoration: BoxDecoration(
              color: WritingColors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
      ),
    );
  }
}
