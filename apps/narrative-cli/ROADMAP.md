# narrative-cli ROADMAP

## v0.1 ✅ 已完成

- [x] `extract` — 母题提取 (p05)，可选覆盖率对照
- [x] `review` — 风格评审 (p09)，可选两步交叉诊断 (p10)
- [x] `inspire` — 母题缝隙分析 + 6 方向建议生成 (p08)
- [x] LLM 调用层 (DeepSeek, synchronous reqwest)
- [x] YAML 合同模型 (MotifProfile, StyleProfile)
- [x] Prompt 构建与命令逻辑分离
- [x] JSON 解析 3 次重试
- [x] 两步诊断拆分（自由推断 → 母题匹配），消除确认偏误
- [x] 空白行段落边界保留（与 Python 版对齐）

## v0.2

- [ ] `inspire --compare` — pairwise blind 改法排序 (p10)
- [ ] 集成测试（mock LLM，每个子命令 happy path）
- [ ] `extract` 母题覆盖率改用语义匹配（非子串）
- [ ] `inspire` JSON 温度从 0.7 降至 0.4
- [ ] `review --motif-profile` 输出新增 `style_motif_mapping` 字段

## v0.3

- [ ] `export` 命令 — 将场景转换为 gallery 格式 (style.yaml + samples/)
- [ ] 异步 LLM 调用（tokio + reqwest async）
- [ ] 多场景批量处理（`--scene-dir`）
- [ ] 跨系列转移测试（都市审美评校园）

## v1.0

- [ ] Pipeline 命令 — 串联 extract → review → inspire 全流程
- [ ] `--model` 支持多 LLM 后端（DeepSeek / GPT-4o-mini）
- [ ] 输出格式支持 YAML（与 gallery 格式互操作）
- [ ] 完整的错误诊断（API key 缺失、YAML 格式错误、网络超时）
