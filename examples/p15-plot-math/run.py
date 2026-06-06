#!/usr/bin/env python3
"""p15 — 情节结构的数学形式化"""

import json
import os

SCENES = ["S1_咖啡厅重逢", "S2_酒吧表白"]
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

def main():
    print(f"p15: 情节结构的数学形式化")
    print(f"验证 p12 概念 → 因果图/密度函数/贝叶斯惊奇的映射一致性")
    print(f"目标场景: {', '.join(SCENES)}")

if __name__ == "__main__":
    main()
