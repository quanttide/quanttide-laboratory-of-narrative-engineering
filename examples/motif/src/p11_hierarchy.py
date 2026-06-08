#!/usr/bin/env python3
"""
p11 — 母题层级结构发现

基于 p06 相似度矩阵做层次聚类，探索母题的天然层级结构。
验证 gallery 的 6 个母题是否是扁平的，是否存在粒度不统一的问题。
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import squareform

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_DIR

P06_RESULTS = DATA_DIR / "p06"
RESULTS_DIR = DATA_DIR / "p11"


def load_similarity_matrix() -> list[dict]:
    path = P06_RESULTS / "similarity_matrix.json"
    return json.loads(path.read_text("utf-8"))


def extract_scene_names(data: list[dict]) -> list[str]:
    names = set()
    for r in data:
        names.add(r["pair_a"])
        names.add(r["pair_b"])
    return sorted(names)


def build_distance_matrix(data: list[dict], scenes: list[str]) -> np.ndarray:
    n = len(scenes)
    dist = np.zeros((n, n))
    lookup = {s: i for i, s in enumerate(scenes)}
    for r in data:
        i = lookup[r["pair_a"]]
        j = lookup[r["pair_b"]]
        sim = r["similarity"]
        dist[i][j] = 1.0 - sim
        dist[j][i] = 1.0 - sim
    # fill diagonal with 0 (self-distance already 0)
    # fill missing pairs (no direct similarity measured) with 1.0 (maximum distance)
    for i in range(n):
        for j in range(n):
            if i != j and dist[i][j] == 0:
                dist[i][j] = 1.0
    return dist


def parse_scene_label(label: str) -> tuple[str, str, str]:
    parts = label.split("_", 2)
    motif = parts[0] if len(parts) > 0 else "?"
    series = parts[1] if len(parts) > 1 else "?"
    scene = parts[2] if len(parts) > 2 else "?"
    return motif, series, scene


def print_ascii_dendrogram(Z: np.ndarray, labels: list[str]):
    print("\n层次聚类 Dendrogram（ASCII）：\n")
    # Use scipy's dendrogram to compute coordinates, print simplified version
    dn = dendrogram(Z, labels=labels, no_plot=True)
    icoord = dn["icoord"]
    dcoord = dn["dcoord"]
    ivl = dn["ivl"]

    # print ordered labels
    print("  叶子节点顺序（从左到右）：")
    for i, label in enumerate(ivl):
        motif, series, scene = parse_scene_label(label)
        print(f"    {i+1}. {motif} | {series} | {scene}")

    print(f"\n  合并层级：")
    for i, (x, y, dist, count) in enumerate(Z):
        l = int(x)
        r = int(y)
        l_label = ivl[l] if l < len(ivl) else f"cluster@{l}"
        r_label = ivl[r] if r < len(ivl) else f"cluster@{r}"
        print(f"    层级 {i+1}: {l_label} + {r_label}  @ dist={dist:.3f}  ({int(count)} 个成员)")


def report(scenes: list[str], dist_matrix: np.ndarray, Z: np.ndarray, flat_clusters: np.ndarray):
    print("=" * 60)
    print("p11 母题层级结构发现报告")
    print("=" * 60)

    n = len(scenes)

    # 距离矩阵统计
    triu_dist = dist_matrix[np.triu_indices(n, k=1)]
    print(f"\n## 距离矩阵概况")
    print(f"  场景数: {n}")
    print(f"   最小距离: {triu_dist.min():.3f}")
    print(f"   最大距离: {triu_dist.max():.3f}")
    print(f"   平均距离: {triu_dist.mean():.3f}")

    # 分组情况
    n_clusters = len(set(flat_clusters))
    print(f"\n## 层次聚类分组（在 distance=0.5 处切割）")
    print(f"  共 {n_clusters} 个簇：")
    for cid in sorted(set(flat_clusters)):
        members = [scenes[i] for i in range(n) if flat_clusters[i] == cid]
        motifs_in_cluster = [parse_scene_label(m)[0] for m in members]
        print(f"    簇 {cid}: {len(members)} 个成员")
        for m in members:
            motif, series, scene = parse_scene_label(m)
            print(f"      - {motif} ({series}, {scene})")
        unique_motifs = set(motifs_in_cluster)
        if len(unique_motifs) == 1:
            print(f"      ✅ 完全对应母题: {list(unique_motifs)[0]}")
        else:
            print(f"      ⚠️ 跨母题混合: {unique_motifs}")

    # 跨母题混合分析
    print(f"\n## 母题混合分析")
    mixed_count = 0
    for cid in sorted(set(flat_clusters)):
        members = [scenes[i] for i in range(n) if flat_clusters[i] == cid]
        motifs_in_cluster = {parse_scene_label(m)[0] for m in members}
        if len(motifs_in_cluster) > 1:
            mixed_count += 1
            print(f"  ⚠️ 簇 {cid} 混合了以下母题: {motifs_in_cluster}")
    if mixed_count == 0:
        print(f"  ✅ 所有簇均不跨母题——LLM 相似度与 gallery 分类完全一致")
    else:
        print(f"  ❌ 存在 {mixed_count} 个跨母题簇——母题间有语义重叠")

    print(f"\n## 母题间距矩阵（平均簇间距离）")
    motif_names = sorted(set(parse_scene_label(s)[0] for s in scenes))
    print(f"  {'':<16}", end="")
    for m2 in motif_names:
        print(f" {m2:<10}", end="")
    print()
    for m1 in motif_names:
        print(f"  {m1:<16}", end="")
        idxs1 = [i for i, s in enumerate(scenes) if parse_scene_label(s)[0] == m1]
        for m2 in motif_names:
            idxs2 = [i for i, s in enumerate(scenes) if parse_scene_label(s)[0] == m2]
            vals = [dist_matrix[i][j] for i in idxs1 for j in idxs2 if i != j]
            avg = np.mean(vals) if vals else 0
            print(f" {avg:<10.3f}", end="")
        print()


def main():
    print("=" * 60)
    print("p11 — 母题层级结构发现")
    print("=" * 60)

    RESULTS_DIR.mkdir(exist_ok=True)

    data = load_similarity_matrix()
    print(f"  加载相似度矩阵: {len(data)} 对")

    scenes = extract_scene_names(data)
    print(f"  唯一场景: {len(scenes)}")
    for s in scenes:
        motif, series, scene = parse_scene_label(s)
        print(f"    {s}")

    dist_matrix = build_distance_matrix(data, scenes)
    condensed = dist_matrix[np.triu_indices(len(scenes), k=1)]

    # 层次聚类（平均链接）
    Z = linkage(condensed, method="average")

    # 在 distance=0.5 处切割（对应 similarity=0.5）
    flat_clusters = fcluster(Z, t=0.5, criterion="distance")

    print_ascii_dendrogram(Z, scenes)
    report(scenes, dist_matrix, Z, flat_clusters)

    # 保存结果
    result = {
        "scenes": scenes,
        "distance_matrix": dist_matrix.tolist(),
        "linkage": Z.tolist(),
        "flat_clusters": flat_clusters.tolist(),
    }
    (RESULTS_DIR / "hierarchy_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"\n结果已保存到: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
