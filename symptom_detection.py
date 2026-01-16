from __future__ import annotations

import json
import math
import os
import statistics
from collections import Counter, defaultdict
from typing import Dict, Any, List
import matplotlib.pyplot as plt


RESULTS_PATH = "resultdata.jsonl"
OUTPUT_DIR = "plots"

LIKERT_LABELS = {
    1: "Strongly\ndisagree",
    2: "Disagree",
    3: "Neutral",
    4: "Agree",
    5: "Strongly\nagree",
}

QUESTIONS = [
    ("q1", 2),
    ("q2", 1),
    ("q3", 5),
    ("q4", 1),
    ("q5", 5),
    ("q6", 2),
    ("q7", 2),
    ("q8", 1),
    ("q9", 2),
    ("q10", 4),
    ("q11", 4),
    ("q12", 1),
    ("q13", 1),
    ("q14", 5),
    ("q15", 1),
    ("q16", 1),
    ("q17", 1),
    ("q18", 3),
    ("q19", 2),
    ("q20", 1),
    ("q21", 1),
    ("q22", 1), 
    ("q23", 1), 
    ("q24", 2)
    ]

def read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_no}: {e}") from e
    return rows


def safe_stdev(values: List[int]) -> float:
    """
    Sample standard deviation if n>=2; otherwise return 0.0
    """
    if len(values) < 2:
        return 0.0
    return float(statistics.stdev(values))


def mean(values: List[int]) -> float:
    if not values:
        return float("nan")
    return float(statistics.mean(values))


def median(values: List[int]) -> float:
    if not values:
        return float("nan")
    return float(statistics.median(values))


def collect_answers(rows: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Returns dict: question_id -> list of numeric answers (1..5)
    """
    by_q: Dict[str, List[int]] = defaultdict(list)

    for r in rows:
        answers = r.get("answers", {})
        if not isinstance(answers, dict):
            continue

        for qid, val in answers.items():
            # accept ints 1..5 only
            if isinstance(val, int) and 1 <= val <= 5:
                by_q[str(qid)].append(val)

    return dict(by_q)


def plot_distribution(qid: str, values: List[int], output_dir: str) -> str:
    counts = Counter(values)
    xs = [1, 2, 3, 4, 5]
    ys = [counts.get(x, 0) for x in xs]
    xlabels = [LIKERT_LABELS[x] for x in xs]

    plt.figure()
    plt.bar(xs, ys)
    plt.xticks(xs, xlabels)
    plt.ylabel("Count")
    plt.title(f"Response distribution: {qid}")

    # annotate bar heights
    for x, y in zip(xs, ys):
        plt.text(x, y + 0.02 * max(ys + [1]), str(y), ha="center", va="bottom")

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{qid}.png")
    plt.tight_layout()
    plt.show()
    #plt.savefig(out_path, dpi=200)
    #plt.close()
    return out_path


def main() -> None:
    if not os.path.exists(RESULTS_PATH):
        raise FileNotFoundError(f"Could not find {RESULTS_PATH} in the current folder.")

    rows = read_jsonl(RESULTS_PATH)
    by_q = collect_answers(rows)

    if not by_q:
        print("No valid answers found in results file.")
        return

    print(f"Loaded {len(rows)} runs from {RESULTS_PATH}.")
    print(f"Found {len(by_q)} questions.\n")

    # Optional: stable ordering by qid
    for qid in sorted(by_q.keys()):
        values = by_q[qid]
        n = len(values)

        avg = mean(values)
        med = median(values)
        sd = safe_stdev(values)

        # Distribution
        counts = Counter(values)
        dist_str = ", ".join(f"{k}:{counts.get(k,0)}" for k in [1,2,3,4,5])

        print(f"Question: {qid}")
        print(f"  N = {n}")
        print(f"  Distribution (1..5 counts): {dist_str}")
        print(f"  Average = {avg:.3f}")
        print(f"  Median  = {med:.3f}")
        print(f"  Std dev = {sd:.3f}")

        out_path = plot_distribution(qid, values, OUTPUT_DIR)
        print(f"  Plot saved to: {out_path}\n")


if __name__ == "__main__":
    main()