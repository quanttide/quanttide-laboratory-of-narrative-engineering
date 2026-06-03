# TODO — 按 ROADMAP 优先级分解

## P0: Provider 深度分析入口（当前）

- [ ] lab 端新建 `services/deep_analysis_service.dart` — HTTP 调用 provider `POST /review`
- [ ] lab 端新建 `models/deep_analysis.dart` — provider 返回的 ReviewOut 模型（ParagraphReview、Comparison、Suggestion）
- [ ] 右栏新增"深度分析"按钮（在"评审"按钮旁边或下方）
- [ ] 点击后调 provider API，加载态显示 loading
- [ ] 在右栏"评审"标签页下方展示 provider 结果区域
  - [ ] summary 文本展示
  - [ ] 每段起/承/转/合标签 + 分析文本
  - [ ] suggestions 列表
  - [ ] style comparison 结果（如果有）
- [ ] provider URL 通过 `--dart-define` 注入，默认 `http://localhost:9000`
- [ ] 单元测试：假 provider 服务 + Cubit 状态变化
- [ ] 集成测试：点击"深度分析"→ 状态更新

---

## P0: Provider 端修复

- [ ] 阅读 `quanttide_agent` 的 `LLM` 类文档，明确 `.complete()` / `.chat()` 方法签名
- [ ] `app/services/llm.py` 补齐 4 个缺失函数：
  - [ ] `_build_analyze_prompt(paragraph, position, total, article_tag)` → 返回 prompt 字符串
  - [ ] `_parse_analyze_response(response_content, paragraph)` → 从 LLM 回复中提取 `{original, analysis, tag}`
  - [ ] `_build_compare_prompt(paragraph, tag, style_examples)` → 风格对比 prompt
  - [ ] `_parse_compare_response(response_content)` → 提取 `Comparison` 或 None
- [ ] 修复方法名：`_get_client().chat(...)` → `_get_client().complete(...)`
- [ ] `app/services/review.py` 解开 `style_examples = []` 硬编码，改为从 `StyleStore` 读取
- [ ] `app/store.py` 确认 `StyleStore` 的线程安全（FastAPI 异步需注意）
- [ ] 编写 pytest 测试覆盖完整 LLM 流程（mock LLM 返回值）
- [ ] 手动启动 provider，用 `curl` 验证 `POST /review` 返回正确结构

---

## P1: 起承转合结构展示

- [ ] 右栏新增"结构"标签页（第 4 个 tab）
- [ ] 展示 provider 返回的每段 起/承/转/合 标签
- [ ] 可视化叙事流：色块横条（起=蓝→承=绿→转=橙→合=紫）
- [ ] 点击某段标签 → 跳转到编辑器对应段落
- [ ] 无 provider 数据时显示"等待深度分析"

---

## P1: 风格对比可视化

- [ ] provider 返回 `is_style_available=true` 且某段有 `comparison` 时展示
- [ ] "好/坏"对比卡片：原文 vs 建议改写（diff 风格）
- [ ] 统计面板：多少段落属于"坏"风格，主要问题分布

---

## P2: 评分趋势图

- [ ] Cubit 中维护 `List<double> scoreHistory`（每轮评审追加）
- [ ] 底栏或右栏展示迷你折线图（可用 `fl_chart` 或自定义 CustomPainter）
- [ ] 趋势标注：↑↓ 箭头 + 差值
