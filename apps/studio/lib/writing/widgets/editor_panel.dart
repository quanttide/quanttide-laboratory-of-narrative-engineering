import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
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
  var _isPreview = false;

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
        _buildToolbar(),
        Expanded(child: _buildBody()),
      ],
    );
  }

  Widget _buildToolbar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: WritingColors.surface,
        border: Border(bottom: BorderSide(color: WritingColors.border)),
      ),
      child: Row(
        children: [
          if (!_isPreview)
            Row(
              children: [
                Text('空隙 ',
                    style: TextStyle(
                        fontSize: 11, color: WritingColors.textDim)),
                Text('${widget.cubit.state.gapCount}',
                    style: const TextStyle(
                        fontSize: 11, color: WritingColors.text)),
              ],
            ),
          const Spacer(),
          _ModeToggle(
            isPreview: _isPreview,
            onToggle: () => setState(() => _isPreview = !_isPreview),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_isPreview) {
      return Container(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 14),
        color: WritingColors.bg,
        child: Markdown(
          data: _textCtrl.text,
          shrinkWrap: false,
          styleSheet: _markdownStyle(),
        ),
      );
    }

    return Row(
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
            spellCheckConfiguration:
                const SpellCheckConfiguration.disabled(),
          ),
        ),
      ],
    );
  }

  MarkdownStyleSheet _markdownStyle() {
    return MarkdownStyleSheet(
      h1: const TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: WritingColors.text),
      h2: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: WritingColors.text),
      h3: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: WritingColors.text),
      p: const TextStyle(
          fontSize: 14, height: 1.8, color: WritingColors.text),
      a: const TextStyle(color: WritingColors.accent),
      blockquoteDecoration: BoxDecoration(
        border: Border(
            left: BorderSide(color: WritingColors.accent, width: 3)),
        color: WritingColors.surface2,
      ),
      blockquotePadding: const EdgeInsets.fromLTRB(12, 4, 12, 4),
      code: const TextStyle(
          fontSize: 12, color: WritingColors.accent3, fontFamily: 'monospace'),
      codeblockDecoration: BoxDecoration(
        color: WritingColors.surface2,
        borderRadius: BorderRadius.circular(4),
      ),
      codeblockPadding: const EdgeInsets.all(12),
      horizontalRuleDecoration: BoxDecoration(
        border: Border(top: BorderSide(color: WritingColors.border)),
      ),
      listBullet: const TextStyle(color: WritingColors.textDim),
      listBulletPadding: const EdgeInsets.only(right: 8),
      tableHead: const TextStyle(fontWeight: FontWeight.w600),
      tableBody: const TextStyle(color: WritingColors.text),
      tableBorder: TableBorder.all(color: WritingColors.border),
      tableColumnWidth: const FlexColumnWidth(),
      del: const TextStyle(
          decoration: TextDecoration.lineThrough,
          color: WritingColors.textDim),
      em: const TextStyle(fontStyle: FontStyle.italic),
      strong: const TextStyle(fontWeight: FontWeight.w700),
    );
  }
}

class _ModeToggle extends StatelessWidget {
  final bool isPreview;
  final VoidCallback onToggle;

  const _ModeToggle({
    required this.isPreview,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onToggle,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          color: WritingColors.surface2,
          border: Border.all(color: WritingColors.border),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _Tab(label: '编辑', active: !isPreview),
            Container(
              width: 1,
              height: 12,
              color: WritingColors.border,
              margin: const EdgeInsets.symmetric(horizontal: 4),
            ),
            _Tab(label: '预览', active: isPreview),
          ],
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  final String label;
  final bool active;

  const _Tab({required this.label, required this.active});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: TextStyle(
        fontSize: 11,
        fontWeight: active ? FontWeight.w600 : FontWeight.normal,
        color: active ? WritingColors.accent : WritingColors.textDim,
      ),
    );
  }
}
