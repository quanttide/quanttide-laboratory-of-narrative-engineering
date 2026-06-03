# 写作云 Lab

写作云 3R 写作工作台的原型实验项目。

## 快速启动

```bash
# Web
flutter run -d chrome

# Linux 桌面
flutter run -d linux
```

## 测试

```bash
# 单元测试
flutter test

# 集成测试 (需 Linux 桌面)
flutter test -d linux integration_test/
```

## 项目结构

```
lib/
├── main.dart                     # 入口
├── writing/
│   ├── bloc/
│   │   └── writing_review_cubit  # 3R 状态管理
│   ├── models/
│   │   └── analysis.dart         # 空隙/风格/改写等数据模型
│   ├── services/
│   │   └── analysis_engine.dart  # 叙事空隙正则分析引擎
│   ├── theme/
│   │   └── writing_theme.dart    # 设计令牌 → ThemeData
│   └── widgets/
│       ├── writing_workbench     # 三栏主工作台
│       ├── writing_app_bar       # 顶栏
│       ├── draft_panel           # 左栏 - 底稿列表
│       ├── editor_panel          # 中栏 - 编辑器 + 空隙标记
│       ├── gap_markers_column    # 空隙标记圆点
│       ├── review_panel          # 右栏 - 3R 面板容器
│       ├── review_tab            # 评审标签页
│       ├── reflect_tab           # 情境标签页
│       ├── rewrite_tab           # 改写标签页
│       ├── guide_card            # 引导卡片
│       ├── style_bar             # 风格进度条
│       ├── status_bar            # 底栏
│       └── draggable_divider     # 可拖拽分隔条
├── cubits/                       # (原文档智能体)
├── services/                     # (原文档智能体)
└── ui/                           # (原文档智能体)
```
