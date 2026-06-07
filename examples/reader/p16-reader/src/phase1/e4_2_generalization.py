"""E4-2a — 跨文本泛化检验

3-fold CV：在 2 组文本上训练 RandomForestClassifier，在剩余 1 组上预测画像标签。
验证分化效应在未见文本上是否成立。
"""
import sys, json
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

from packages.python.io import load_json, save_json


FEATURES = ["writing_quality", "emotional_impact", "character_realism", "cliche_level", "reading_difficulty"]


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-2a — 跨文本泛化检验")
    print("=" * 60)

    rows = load_json(results_dir / "e4-1_raw.json")
    print(f"加载 {len(rows)} 条 E4-1 记录")

    # 按 text_id 分 fold（6 篇 → 3 组，各 2 篇）
    text_ids = sorted(set(r["text_id"] for r in rows))
    np.random.seed(42)
    np.random.shuffle(text_ids)
    folds = [text_ids[i::3] for i in range(3)]  # [[4.1,10.3], [7.2,1.2], [9.1,2.3]]
    print(f"文本分组: {folds}")

    accuracies = []
    all_true, all_pred = [], []
    importances = []

    for fold_idx, test_texts in enumerate(folds):
        train_texts = [t for t in text_ids if t not in test_texts]
        train_rows = [r for r in rows if r["text_id"] in train_texts]
        test_rows = [r for r in rows if r["text_id"] in test_texts]

        X_train = np.array([[r[f] for f in FEATURES] for r in train_rows], dtype=float)
        y_train = np.array([r["profile"] for r in train_rows])
        X_test = np.array([[r[f] for f in FEATURES] for r in test_rows], dtype=float)
        y_test = np.array([r["profile"] for r in test_rows])

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        accuracies.append(round(float(acc), 4))
        all_true.extend(y_test.tolist())
        all_pred.extend(y_pred.tolist())
        importances.append(clf.feature_importances_)
        print(f"  Fold {fold_idx + 1}: train={train_texts}, test={test_texts}, acc={acc:.2%}")

    mean_acc = float(np.mean(accuracies))
    baseline = 0.20
    passed = mean_acc >= 0.40

    cm = confusion_matrix(all_true, all_pred, labels=sorted(set(all_true)))
    cm_list = cm.tolist()

    result = {
        "accuracy_per_fold": accuracies,
        "mean_accuracy": round(mean_acc, 4),
        "random_baseline": baseline,
        "pass": bool(passed),
        "confusion_matrix": cm_list,
        "feature_importance": dict(zip(FEATURES, [round(float(v), 3) for v in np.mean(importances, axis=0)])),
    }
    save_json(results_dir / "e4-2_generalization.json", result)

    print(f"\n  平均准确率: {mean_acc:.2%} (基线 {baseline:.0%}, 标准 ≥ 40%)")
    print(f"  {'✅' if passed else '❌'} 泛化检验")

    return result


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "reader" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
