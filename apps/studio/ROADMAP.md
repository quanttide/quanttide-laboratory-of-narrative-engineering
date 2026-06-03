# ROADMAP — 写作云 3R 工作台 Lab

## 这是什么

写作云 3R 工作台的 Flutter 原型。把 p02 HTML PoC 翻译成 Flutter，用 BLoC 管理状态，用正则引擎做本地叙事分析，验证 3R（Review → Reflect → Rewrite）写作辅助循环的交互体验。

## 当前状态

- 三栏工作台：底稿列表 | 编辑器+空隙标记 | 3R 分析面板
- Markdown 编辑/预览切换
- 正则分析引擎：4 类空隙检测 + 3 项风格评分 + 引导问题 + 改写建议
- 3R 标签页：评审（空隙列表+风格条）/ 情境（引导卡片）/ 改写（建议卡片）
- 3R 循环闭环：写 → 评审 → 看情境 → 改写 → 再评审
- 多轮迭代：文本变化后空隙数/评分随之变化
- 空隙标记点击 / 标签项点击 → 编辑器跳转（`pendingJumpLine` 机制）
- 设计令牌暗色主题
- 用户文档：README + 使用指南
- 单元测试 121 个，集成测试 9 个

## 下一步

优先级从高到低：

1. **Provider 深度分析入口** — 右栏加"深度分析"按钮，调用修复后的 provider API，结果展示在现有 3R 面板下方或新标签页
2. **Provider 端修复** — 补齐 `_build_analyze_prompt` / `_parse_analyze_response` 等缺失函数，修复 `style_examples` 硬编码，使 LLM 分析真正可用
3. **起承转合结构展示** — provider 返回段落级叙事标签后，在右栏展示"结构"视图
4. **风格对比可视化** — provider 的 style comparison 结果展示为差异对比
5. **评分趋势图** — 多轮迭代间评分变化折线

## 不做

- 不接入 OpenCode 对话（那个在 doc_agent 模式里）
- 不做用户系统 / 多文档管理
- 不重构原 doc_agent 代码
