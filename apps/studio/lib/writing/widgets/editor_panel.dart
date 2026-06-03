import 'package:flutter/material.dart';
import '../bloc/writing_review_cubit.dart';
import '../theme/writing_theme.dart';
import 'gap_markers_column.dart';

class EditorPanel extends StatefulWidget {
  final WritingReviewCubit cubit;

  const EditorPanel({super.key, required this.cubit});

  @override
  State<EditorPanel> createState() => _EditorPanelState();
}

class _EditorPanelState extends State<EditorPanel> {
  late TextEditingController _textCtrl;
  late ScrollController _scrollCtrl;
  int _lineCount = 0;

  @override
  void initState() {
    super.initState();
    _textCtrl = TextEditingController(text: widget.cubit.state.text);
    _scrollCtrl = ScrollController();
    widget.cubit.stream.listen((state) {
      if (_textCtrl.text != state.text) {
        _textCtrl.text = state.text;
      }
      _updateLineCount(state.text);
    });
    _updateLineCount(widget.cubit.state.text);
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _updateLineCount(String text) {
    final count = '\n'.allMatches(text).length + 1;
    if (count != _lineCount) {
      setState(() => _lineCount = count);
    }
  }

  void _onChanged(String text) {
    widget.cubit.textChanged(text);
    _updateLineCount(text);
  }

  void _jumpToLine(int line) {
    final offset = (line - 1) * GapMarkersColumn.lineHeight - 60;
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(
        offset.clamp(0.0, _scrollCtrl.position.maxScrollExtent),
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOut,
      );
    }
    final lines = _textCtrl.text.split('\n');
    var pos = 0;
    for (var i = 0; i < (line - 1).clamp(0, lines.length); i++) {
      pos += lines[i].length + 1;
    }
    _textCtrl.selection = TextSelection.collapsed(offset: pos);
    widget.cubit.jumpToLine(line);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: WritingColors.surface,
            border: Border(bottom: BorderSide(color: WritingColors.border)),
          ),
          child: Row(
            children: [
              Text(
                '空隙 ',
                style: TextStyle(fontSize: 11, color: WritingColors.textDim),
              ),
              Text(
                '${widget.cubit.state.gapCount}',
                style: const TextStyle(fontSize: 11, color: WritingColors.text),
              ),
            ],
          ),
        ),
        Expanded(
          child: Row(
            children: [
              Container(
                width: 18,
                color: WritingColors.surface,
                child: GapMarkersColumn(
                  gaps: widget.cubit.state.analysis?.gaps ?? [],
                  lineCount: _lineCount,
                  onJumpTo: _jumpToLine,
                ),
              ),
              Container(width: 1, color: WritingColors.border),
              Expanded(
                child: TextField(
                  controller: _textCtrl,
                  scrollController: _scrollCtrl,
                  maxLines: null,
                  expands: true,
                  textAlignVertical: TextAlignVertical.top,
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.fromLTRB(18, 14, 18, 14),
                    hintText: '在此输入文本...',
                  ),
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.8,
                    color: WritingColors.text,
                  ),
                  onChanged: _onChanged,
                  spellCheckConfiguration: const SpellCheckConfiguration.disabled(),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
