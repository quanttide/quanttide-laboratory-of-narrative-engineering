"""
统计工具 — 实验数据分析所需指标。

封装 numpy / scipy / sklearn 的计算，统一接口。
"""
import numpy as np
from scipy import stats as sp_stats


def cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Cohen's d — 两组独立样本的标准化效应量。"""
    n1, n2 = len(x), len(y)
    s1, s2 = np.var(x, ddof=1), np.var(y, ddof=1)
    pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    return (np.mean(x) - np.mean(y)) / pooled


def icc(data: np.ndarray) -> float:
    """ICC(2,1) — 绝对一致性的组内相关系数（Shrout & Fleiss 模型 2）。

    参数：
        data: shape (targets, raters) 的矩阵
    返回：
        ICC 值
    """
    n, k = data.shape
    msr = np.var(data.mean(axis=1), ddof=1) * k
    msw = np.sum((data - data.mean(axis=1, keepdims=True)) ** 2) / (n * (k - 1))
    msr_ = np.var(data.mean(axis=0), ddof=1) * n
    mse = (msw + (msr_ - msw) / k) / n if msr_ > msw else msw
    return (msr - msw) / (msr + (k - 1) * msw + k * (mse - msw) / n)


def spearman_rho(x: list, y: list) -> float:
    """Spearman 秩相关系数。"""
    return sp_stats.spearmanr(x, y).statistic


def kendall_tau(x: list, y: list) -> float:
    """Kendall τ 秩相关系数。"""
    return sp_stats.kendalltau(x, y).statistic


def bootstrap_ci(data: np.ndarray, statistic=np.mean, n_resamples: int = 1000, ci: float = 0.95):
    """Bootstrapping 估计统计量的置信区间。

    返回：
        (lower, upper) 置信区间边界
    """
    result = sp_stats.bootstrap(
        (data,),
        statistic,
        n_resamples=n_resamples,
        confidence_level=ci,
        method="BCa",
    )
    return result.confidence_interval.low, result.confidence_interval.high
