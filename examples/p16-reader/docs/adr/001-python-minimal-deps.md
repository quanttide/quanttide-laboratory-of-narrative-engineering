# 1. 使用 Python + 最小增量依赖

**Status**: Accepted

**Date**: 2026-06-07

## Context

p16-reader（E4 模拟读者系统）需要执行以下实验：
- E4-0：文本 embedding 聚类（轮廓系数）
- E4-1/2：统计检验（Cohen's d、ICC、Spearman ρ、Kendall τ）
- E4-4：线性回归、bootstrapping 置信区间
- E4-5：ANOVA

现有 PoC（p03–p15）全部使用独立 `run.py`，技术栈仅有 `requests` + `pyyaml`，无任何科学计算库。p09 手动实现了 Spearman 相关系数以避开 scipy。

p16 的统计需求远超出前序 PoC——手动实现 ICC、bootstrapping、silhouette score 既不可靠也耗时。

## Decision

- **语言**：Python（与已有 9 个 PoC 一致）
- **LLM 调用**：`requests` + DeepSeek `deepseek-chat`（与现有模式一致）
- **Embedding**：`sentence-transformers`（`all-MiniLM-L6-v2`，本地推理，无额外 API 成本）
- **统计**：`numpy` + `scipy` + `scikit-learn`
- **不做**：不引入 pandas、matplotlib、pytorch、openai SDK
- **自包含**：p16 自身维护 `requirements.txt`，不向项目根目录或其他 PoC 引入依赖

新增依赖表：

| 包 | 用途 | 替代方案（否决原因） |
|---|---|---|
| `numpy` | 数值计算、bootstrapping | 纯 Python 手算不现实 |
| `scipy` | ICC、Cohen's d、Kendall τ、ANOVA | p09 手动 Spearman 的做法不可扩展 |
| `scikit-learn` | 轮廓系数、逻辑回归分类器 | sklearn 是社区标准，无更轻量化替代 |
| `sentence-transformers` | 本地文本 embedding | OpenAI embedding（额外 API 成本 + 网络依赖） |

## Consequences

**Positive**:
- 统计计算可靠、可复现、有社区验证的实现
- 本地 embedding 无 API 成本、无网络依赖
- 不污染其他 PoC 的运行环境

**Negative**:
- 首次为项目引入科学计算依赖，打破"纯 requests"的简单性
- 需要 `pip install` 额外包才能运行，不再零配置

**Neutral**:
- `sentence-transformers` 首次运行需下载约 80MB 模型缓存
