import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/writing_review_cubit.dart';
import '../themes/writing_theme.dart';
import 'writing_app_bar.dart';
import 'draft_panel.dart';
import 'editor_panel.dart';
import 'review_panel.dart';
import 'status_bar.dart';
import 'draggable_divider.dart';

class WritingWorkbench extends StatefulWidget {
  const WritingWorkbench({super.key});

  @override
  State<WritingWorkbench> createState() => _WritingWorkbenchState();
}

class _WritingWorkbenchState extends State<WritingWorkbench> {
  double _leftWidth = 200;
  double _rightWidth = 300;

  void _onLeftDrag(double delta) {
    setState(() {
      _leftWidth = (_leftWidth + delta).clamp(120.0, 400.0);
    });
  }

  void _onRightDrag(double delta) {
    setState(() {
      _rightWidth = (_rightWidth - delta).clamp(180.0, 500.0);
    });
  }

  @override
  Widget build(BuildContext context) {
    final cubit = context.watch<WritingReviewCubit>();

    return Scaffold(
      backgroundColor: WritingColors.bg,
      body: Column(
        children: [
          WritingAppBar(cubit: cubit),
          Expanded(
            child: Row(
              children: [
                DraftPanel(
                  onLoadSample: () => cubit.loadSample(),
                  hasContent: cubit.state.text.isNotEmpty,
                ),
                DraggableDivider(isLeft: true, onDrag: _onLeftDrag),
                Expanded(
                  child: EditorPanel(cubit: cubit),
                ),
                DraggableDivider(isLeft: false, onDrag: _onRightDrag),
                const ReviewPanel(),
              ],
            ),
          ),
          StatusBar(cubit: cubit),
        ],
      ),
    );
  }
}
