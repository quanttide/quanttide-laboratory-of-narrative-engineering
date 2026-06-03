import 'package:flutter_bloc/flutter_bloc.dart';
import '../models/analysis.dart';
import '../services/analysis_engine.dart';

enum ReviewPanelTab { review, reflect, rewrite }

class WritingReviewState {
  final String text;
  final AnalysisResult? analysis;
  final ReviewPanelTab currentTab;
  final int round;
  final bool isLoading;
  final String? error;
  final int? pendingJumpLine;

  const WritingReviewState({
    this.text = '',
    this.analysis,
    this.currentTab = ReviewPanelTab.review,
    this.round = 1,
    this.isLoading = false,
    this.error,
    this.pendingJumpLine,
  });

  WritingReviewState copyWith({
    String? text,
    AnalysisResult? analysis,
    ReviewPanelTab? currentTab,
    int? round,
    bool? isLoading,
    String? error,
    bool clearError = false,
    int? pendingJumpLine,
    bool clearPendingJump = false,
  }) {
    return WritingReviewState(
      text: text ?? this.text,
      analysis: analysis ?? this.analysis,
      currentTab: currentTab ?? this.currentTab,
      round: round ?? this.round,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      pendingJumpLine:
          clearPendingJump ? null : (pendingJumpLine ?? this.pendingJumpLine),
    );
  }

  int get charCount => text.length;
  int get gapCount => analysis?.gaps.length ?? 0;
  double get avgScore => analysis?.avgScore ?? 0;
}

class WritingReviewCubit extends Cubit<WritingReviewState> {
  WritingReviewCubit() : super(const WritingReviewState());

  void textChanged(String text) {
    emit(state.copyWith(text: text));
  }

  void runReview() {
    if (state.text.trim().isEmpty) return;
    emit(state.copyWith(isLoading: true, clearError: true));
    try {
      final result = AnalysisEngine.analyze(state.text);
      emit(state.copyWith(analysis: result, isLoading: false));
    } catch (e) {
      emit(state.copyWith(
        isLoading: false,
        error: '分析失败: $e',
      ));
    }
  }

  void loadSample() {
    emit(state.copyWith(
      text: _sampleText,
      isLoading: true,
      clearError: true,
    ));
    try {
      final result = AnalysisEngine.analyze(_sampleText);
      emit(state.copyWith(analysis: result, isLoading: false));
    } catch (e) {
      emit(state.copyWith(isLoading: false, error: '分析失败: $e'));
    }
  }

  void switchTab(ReviewPanelTab tab) {
    emit(state.copyWith(currentTab: tab));
  }

  void jumpToLine(int line) {
    emit(state.copyWith(pendingJumpLine: line));
  }

  void clearPendingJump() {
    emit(state.copyWith(clearPendingJump: true));
  }

  static const _sampleText = '''# 咖啡厅重逢

春天的一个工作日的下午，咖啡店外下着淅淅沥沥的小雨。

他愣神看着窗外的雨水沿着屋檐滑落到地面上。

他又想起了她了。

自从毕业以后，他们的交集渐渐地少了。

他打开手机相册里那个常打开的星标相簿，又翻到了她的那张照片。

那是他存了十年的照片。

他看着窗外时下时停的雨。透过去，他看到了十年前自己在雨中见过的她的背影。

她拉着行李箱走出车站，抬头望了望头上忽晴忽阴的天空。

她看到前面有家咖啡厅，似乎是在院落里。

她想要推门地手顿住了。真的是他，

滑轮的声音摩擦着地面。她轻轻推开了咖啡店的门。

听到门口的声响，他本能地转过头。

看到眼前窈窕的身影，他愣住了。

不是梦。

他看了看她湿漉漉的头发，从书包里掏出刚在超市买的毛巾。

不知不觉间，他的手已经伸了出去，轻轻地擦了擦她的头发。

擦了两下，他回过神来。赶忙停下来，把毛巾递给她。

她也不舍地回过神，慢慢伸手接过毛巾。

窗外的雨停了又下，下了又停。

他忘不了，也不想忘。''';
}
