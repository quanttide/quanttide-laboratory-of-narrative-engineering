#!/usr/bin/env python3
"""p14 — 片段内部情节建议实验"""

import json
import os

SCENES = ["1_1", "8_2"]
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

def main():
    print(f"p14: 片段内部情节建议实验")
    print(f"目标场景: {', '.join(SCENES)}")
    print(f"结果目录: {RESULTS_DIR}")

if __name__ == "__main__":
    main()
