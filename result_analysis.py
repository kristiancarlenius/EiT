#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import statistics
from collections import defaultdict, Counter
from typing import Dict, Any, List, Tuple, Iterable

import matplotlib.pyplot as plt


# ----------------------------
# Config
# ----------------------------

RESULTS_PATH = "resultdata_longitudinal.jsonl"  # <- set this to your longitudinal file
OUTPUT_DIR = "plots_aggregate"

# (qid, healthy_norm, contradictory_bool)
QUESTIONS: List[Tuple[str, int, bool]] = [
    ("q1", 2, False),
    ("q2", 1, False),
    ("q3", 5, True),
    ("q4", 1, False),
    ("q5", 5, True),
    ("q6", 2, False),
    ("q7", 2, False),
    ("q8", 1, False),
    ("q9", 2, False),
    ("q10", 4, True),
    ("q11", 4, False),
    ("q12", 1, False),
    ("q13", 1, False),
    ("q14", 5, True),
    ("q15", 1, False),
    ("q16", 1, False),
    ("q17", 1, False),
    ("q18", 3, False),
    ("q19", 2, False),
    ("q20", 1, False),
    ("q21", 1, False),
    ("q22", 1, False),
    ("q23", 1, True),
    ("q24", 2, False),
]

NORM: Dict[str, int] = {qid: norm for qid, norm, _ in QUESTIONS}
IS_CONTRADICTORY: Dict[str, bool] = {qid: is_c for qid, _, is_c in QUESTIONS}
QIDS: List[str] = [qid for qid, _, _ in QUESTIONS]


# ----------------------------
# IO helpers
# ----------------------------

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


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def savefig(path: str) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


# ----------------------------
# Scoring primitives
# ----------------------------

def abs_dev_from_norm(answers: Dict[str, int], qids: List[str]) -> float:
    vals = []
    for qid in qids:
        v = answers.get(qid)
        if isinstance(v, int) and 1 <= v <= 5:
            vals.append(abs(v - NORM[qid]))
    return float("nan") if not vals else sum(vals) / len(vals)


def extreme_direction_dev(answers: Dict[str, int], qids: List[str]) -> float:
    """
    Measures movement toward the "sick-extreme" direction:
    - If norm is 4/5: lower answers are more extreme (norm - answer)
    - If norm is 1/2: higher answers are more extreme (answer - norm)
    - If norm is 3: distance from 3 is extreme
    """
    vals = []
    for qid in qids:
        norm = NORM[qid]
        v = answers.get(qid)
        if not (isinstance(v, int) and 1 <= v <= 5):
            continue
        if norm >= 4:
            vals.append(max(0, norm - v))
        elif norm <= 2:
            vals.append(max(0, v - norm))
        else:
            vals.append(abs(v - 3))
    return float("nan") if not vals else sum(vals) / len(vals)


def response_entropy(answers: Dict[str, int]) -> float:
    vals = [v for v in answers.values() if isinstance(v, int) and 1 <= v <= 5]
    if not vals:
        return float("nan")
    c = Counter(vals)
    n = len(vals)
    ent = 0.0
    for cnt in c.values():
        p = cnt / n
        ent -= p * math.log2(p)
    return ent


def compute_scores(answers: Dict[str, int]) -> Dict[str, float]:
    contr_qids = [q for q in QIDS if IS_CONTRADICTORY[q]]
    noncontr_qids = [q for q in QIDS if not IS_CONTRADICTORY[q]]

    dev_all = abs_dev_from_norm(answers, QIDS)
    dev_contr = abs_dev_from_norm(answers, contr_qids)
    dev_noncontr = abs_dev_from_norm(answers, noncontr_qids)

    # Your lying logic:
    # contradictory questions deviate, but non-contradictory do not.
    lie_score = dev_contr - dev_noncontr

    return {
        "health_score": dev_all,
        "extreme_score": extreme_direction_dev(answers, QIDS),
        "lie_score": lie_score,
        "entropy": response_entropy(answers),
        "dev_contradictory": dev_contr,
        "dev_noncontradictory": dev_noncontr,
    }


# ----------------------------
# Flagging rules (aggregate)
# ----------------------------

def is_flag_sick(health_score: float, extreme_score: float) -> bool:
    # Conservative defaults; tune after you see distributions
    if math.isnan(health_score) or math.isnan(extreme_score):
        return False
    return (health_score >= 1.25) or (extreme_score >= 1.0)


def is_flag_lying(lie_score: float, entropy: float) -> bool:
    # Conservative defaults; tune after you see distributions
    if math.isnan(lie_score):
        return False
    return (lie_score >= 0.60) or (not math.isnan(entropy) and entropy >= 2.05)


# ----------------------------
# Aggregate plotting helpers
# ----------------------------

def mean_std(values: List[float]) -> Tuple[float, float]:
    vals = [v for v in values if not math.isnan(v)]
    if not vals:
        return float("nan"), float("nan")
    if len(vals) == 1:
        return vals[0], 0.0
    return statistics.mean(vals), statistics.stdev(vals)


def heatmap(matrix: List[List[float]], row_labels: List[str], col_labels: List[str], title: str, out_path: str) -> None:
    plt.figure(figsize=(max(6, 0.75 * len(col_labels)), max(3, 0.55 * len(row_labels))))
    im = plt.imshow(matrix, aspect="auto")
    plt.colorbar(im, label="Mean score")
    plt.yticks(range(len(row_labels)), row_labels)
    plt.xticks(range(len(col_labels)), col_labels, rotation=45, ha="right")
    plt.title(title)
    plt.xlabel("Week (questionnaire_version)")
    plt.ylabel("Profile (name)")
    savefig(out_path)


def line_with_error(
    xs: List[int],
    series: Dict[str, List[Tuple[float, float]]],
    title: str,
    ylabel: str,
    out_path: str,
) -> None:
    plt.figure(figsize=(10, 5))
    for label, ms in series.items():
        means = [m for (m, s) in ms]
        stds = [s for (m, s) in ms]
        plt.plot(xs, means, marker="o", label=label)
        # simple error band
        lower = [m - s if not (math.isnan(m) or math.isnan(s)) else float("nan") for m, s in zip(means, stds)]
        upper = [m + s if not (math.isnan(m) or math.isnan(s)) else float("nan") for m, s in zip(means, stds)]
        plt.fill_between(xs, lower, upper, alpha=0.15)

    plt.title(title)
    plt.xlabel("Week (questionnaire_version)")
    plt.ylabel(ylabel)
    plt.legend()
    savefig(out_path)


def boxplot_by_profile(values_by_profile: Dict[str, List[float]], title: str, ylabel: str, out_path: str) -> None:
    labels = sorted(values_by_profile.keys())
    data = [[v for v in values_by_profile[l] if not math.isnan(v)] for l in labels]

    plt.figure(figsize=(10, 5))
    plt.boxplot(data, labels=labels, showfliers=True)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    savefig(out_path)


def hexbin_health_vs_lie(points: List[Tuple[float, float]], title: str, out_path: str) -> None:
    xs = [p[0] for p in points if not (math.isnan(p[0]) or math.isnan(p[1]))]
    ys = [p[1] for p in points if not (math.isnan(p[0]) or math.isnan(p[1]))]

    plt.figure(figsize=(7, 6))
    plt.hexbin(xs, ys, gridsize=35, mincnt=1)
    plt.colorbar(label="Count")
    plt.title(title)
    plt.xlabel("Health score (mean abs dev from norm)")
    plt.ylabel("Lie score (contr dev - noncontr dev)")
    savefig(out_path)


def stacked_flag_rates(
    weeks: List[int],
    profiles: List[str],
    sick_rate: Dict[str, List[float]],
    lie_rate: Dict[str, List[float]],
    out_path: str,
) -> None:
    # Two lines per profile: sick rate and lie rate
    plt.figure(figsize=(10, 5))
    for prof in profiles:
        plt.plot(weeks, sick_rate[prof], marker="o", label=f"{prof} sick-rate")
        plt.plot(weeks, lie_rate[prof], marker="o", linestyle="--", label=f"{prof} lie-rate")
    plt.title("Flag rates over time (aggregate)")
    plt.xlabel("Week (questionnaire_version)")
    plt.ylabel("Rate (0..1)")
    plt.ylim(-0.02, 1.02)
    plt.legend(ncol=2)
    savefig(out_path)


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    if not os.path.exists(RESULTS_PATH):
        raise FileNotFoundError(f"Could not find {RESULTS_PATH} in the current folder.")

    ensure_dir(OUTPUT_DIR)
    rows = read_jsonl(RESULTS_PATH)

    # profile -> week -> list of scores
    health_by_prof_week: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    lie_by_prof_week: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    extreme_by_prof_week: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    entropy_by_prof_week: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))

    # for global clouds
    all_points_health_lie: List[Tuple[float, float]] = []
    points_by_week: Dict[int, List[Tuple[float, float]]] = defaultdict(list)

    # for flag rates
    flags_sick_by_prof_week: Dict[str, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
    flags_lie_by_prof_week: Dict[str, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))

    for r in rows:
        if "name" not in r or "questionnaire_version" not in r:
            continue
        profile = str(r["name"])
        week = int(r["questionnaire_version"])
        answers = r.get("answers", {})
        if not isinstance(answers, dict):
            continue

        scores = compute_scores(answers)
        hs = scores["health_score"]
        ls = scores["lie_score"]
        es = scores["extreme_score"]
        en = scores["entropy"]

        health_by_prof_week[profile][week].append(hs)
        lie_by_prof_week[profile][week].append(ls)
        extreme_by_prof_week[profile][week].append(es)
        entropy_by_prof_week[profile][week].append(en)

        all_points_health_lie.append((hs, ls))
        points_by_week[week].append((hs, ls))

        flags_sick_by_prof_week[profile][week].append(int(is_flag_sick(hs, es)))
        flags_lie_by_prof_week[profile][week].append(int(is_flag_lying(ls, en)))

    profiles = sorted(health_by_prof_week.keys())
    if not profiles:
        print("No valid records found.")
        return

    all_weeks = sorted({w for prof in profiles for w in health_by_prof_week[prof].keys()})
    if not all_weeks:
        print("No weeks found.")
        return

    print(f"Loaded {len(rows)} rows from {RESULTS_PATH}")
    print(f"Profiles: {profiles}")
    print(f"Weeks: {all_weeks}")

    # ----------------------------
    # 1) Heatmaps: mean health and mean lie by (profile x week)
    # ----------------------------
    health_matrix: List[List[float]] = []
    lie_matrix: List[List[float]] = []
    extreme_matrix: List[List[float]] = []

    for prof in profiles:
        row_h = []
        row_l = []
        row_e = []
        for w in all_weeks:
            mh, _ = mean_std(health_by_prof_week[prof].get(w, []))
            ml, _ = mean_std(lie_by_prof_week[prof].get(w, []))
            me, _ = mean_std(extreme_by_prof_week[prof].get(w, []))
            row_h.append(mh)
            row_l.append(ml)
            row_e.append(me)
        health_matrix.append(row_h)
        lie_matrix.append(row_l)
        extreme_matrix.append(row_e)

    heatmap(
        matrix=health_matrix,
        row_labels=profiles,
        col_labels=[str(w) for w in all_weeks],
        title="Mean Health Score by Profile and Week",
        out_path=os.path.join(OUTPUT_DIR, "heatmap_health_mean.png"),
    )
    heatmap(
        matrix=lie_matrix,
        row_labels=profiles,
        col_labels=[str(w) for w in all_weeks],
        title="Mean Lie Score by Profile and Week",
        out_path=os.path.join(OUTPUT_DIR, "heatmap_lie_mean.png"),
    )
    heatmap(
        matrix=extreme_matrix,
        row_labels=profiles,
        col_labels=[str(w) for w in all_weeks],
        title="Mean Extreme Score by Profile and Week",
        out_path=os.path.join(OUTPUT_DIR, "heatmap_extreme_mean.png"),
    )

    # ----------------------------
    # 2) Mean ± std over time lines
    # ----------------------------
    health_series: Dict[str, List[Tuple[float, float]]] = {}
    lie_series: Dict[str, List[Tuple[float, float]]] = {}
    extreme_series: Dict[str, List[Tuple[float, float]]] = {}

    for prof in profiles:
        health_series[prof] = [mean_std(health_by_prof_week[prof].get(w, [])) for w in all_weeks]
        lie_series[prof] = [mean_std(lie_by_prof_week[prof].get(w, [])) for w in all_weeks]
        extreme_series[prof] = [mean_std(extreme_by_prof_week[prof].get(w, [])) for w in all_weeks]

    line_with_error(
        xs=all_weeks,
        series=health_series,
        title="Health Score Over Time (mean ± std)",
        ylabel="Health score (mean abs dev from norm)",
        out_path=os.path.join(OUTPUT_DIR, "lines_health_mean_std.png"),
    )
    line_with_error(
        xs=all_weeks,
        series=lie_series,
        title="Lie Score Over Time (mean ± std)",
        ylabel="Lie score (contr dev - noncontr dev)",
        out_path=os.path.join(OUTPUT_DIR, "lines_lie_mean_std.png"),
    )
    line_with_error(
        xs=all_weeks,
        series=extreme_series,
        title="Extreme Score Over Time (mean ± std)",
        ylabel="Extreme score (toward sick direction)",
        out_path=os.path.join(OUTPUT_DIR, "lines_extreme_mean_std.png"),
    )

    # ----------------------------
    # 3) Distribution plots (boxplots) aggregated over ALL weeks (per profile)
    # ----------------------------
    health_all_by_profile: Dict[str, List[float]] = {}
    lie_all_by_profile: Dict[str, List[float]] = {}
    extreme_all_by_profile: Dict[str, List[float]] = {}

    for prof in profiles:
        health_all_by_profile[prof] = [v for w in all_weeks for v in health_by_prof_week[prof].get(w, [])]
        lie_all_by_profile[prof] = [v for w in all_weeks for v in lie_by_prof_week[prof].get(w, [])]
        extreme_all_by_profile[prof] = [v for w in all_weeks for v in extreme_by_prof_week[prof].get(w, [])]

    boxplot_by_profile(
        values_by_profile=health_all_by_profile,
        title="Health Score Distribution by Profile (All Weeks)",
        ylabel="Health score",
        out_path=os.path.join(OUTPUT_DIR, "box_health_by_profile.png"),
    )
    boxplot_by_profile(
        values_by_profile=lie_all_by_profile,
        title="Lie Score Distribution by Profile (All Weeks)",
        ylabel="Lie score",
        out_path=os.path.join(OUTPUT_DIR, "box_lie_by_profile.png"),
    )
    boxplot_by_profile(
        values_by_profile=extreme_all_by_profile,
        title="Extreme Score Distribution by Profile (All Weeks)",
        ylabel="Extreme score",
        out_path=os.path.join(OUTPUT_DIR, "box_extreme_by_profile.png"),
    )

    # ----------------------------
    # 4) Point-cloud density: health vs lie (overall and per week)
    # ----------------------------
    hexbin_health_vs_lie(
        points=all_points_health_lie,
        title="Health vs Lie Score Density (All Profiles, All Weeks)",
        out_path=os.path.join(OUTPUT_DIR, "hexbin_health_vs_lie_all.png"),
    )

    # Per-week density (one image per week; not per profile)
    for w in all_weeks:
        hexbin_health_vs_lie(
            points=points_by_week[w],
            title=f"Health vs Lie Score Density (Week {w})",
            out_path=os.path.join(OUTPUT_DIR, f"hexbin_health_vs_lie_week_{w}.png"),
        )

    # ----------------------------
    # 5) Flag-rate trends (aggregate)
    # ----------------------------
    sick_rate: Dict[str, List[float]] = {}
    lie_rate: Dict[str, List[float]] = {}

    for prof in profiles:
        sick_rate[prof] = []
        lie_rate[prof] = []
        for w in all_weeks:
            svals = flags_sick_by_prof_week[prof].get(w, [])
            lvals = flags_lie_by_prof_week[prof].get(w, [])
            sr = (sum(svals) / len(svals)) if svals else float("nan")
            lr = (sum(lvals) / len(lvals)) if lvals else float("nan")
            sick_rate[prof].append(sr)
            lie_rate[prof].append(lr)

    stacked_flag_rates(
        weeks=all_weeks,
        profiles=profiles,
        sick_rate=sick_rate,
        lie_rate=lie_rate,
        out_path=os.path.join(OUTPUT_DIR, "flag_rates_over_time.png"),
    )

    # ----------------------------
    # Console summary
    # ----------------------------
    print("\nAggregate summary (mean scores by profile, last week):")
    last_w = all_weeks[-1]
    for prof in profiles:
        mh, sh = mean_std(health_by_prof_week[prof].get(last_w, []))
        ml, sl = mean_std(lie_by_prof_week[prof].get(last_w, []))
        me, se = mean_std(extreme_by_prof_week[prof].get(last_w, []))
        print(
            f"{prof:18s}  week={last_w}  "
            f"health={mh:.3f}±{sh:.3f}  lie={ml:.3f}±{sl:.3f}  extreme={me:.3f}±{se:.3f}"
        )

    print(f"\nSaved aggregate plots to: {OUTPUT_DIR}/")
    print("Key files:")
    print("  heatmap_health_mean.png, heatmap_lie_mean.png, heatmap_extreme_mean.png")
    print("  lines_health_mean_std.png, lines_lie_mean_std.png, lines_extreme_mean_std.png")
    print("  box_health_by_profile.png, box_lie_by_profile.png, box_extreme_by_profile.png")
    print("  hexbin_health_vs_lie_all.png, hexbin_health_vs_lie_week_*.png")
    print("  flag_rates_over_time.png")


if __name__ == "__main__":
    main()
