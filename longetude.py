#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from typing import Dict, Any, List, Iterable, Tuple


QUESTIONS: List[Tuple[str, int]] = [
    ("q1", 2), ("q2", 1), ("q3", 5), ("q4", 1), ("q5", 5), ("q6", 2),
    ("q7", 2), ("q8", 1), ("q9", 2), ("q10", 4), ("q11", 4), ("q12", 1),
    ("q13", 1), ("q14", 5), ("q15", 1), ("q16", 1), ("q17", 1), ("q18", 3),
    ("q19", 2), ("q20", 1), ("q21", 1), ("q22", 1), ("q23", 1), ("q24", 2),
]

NORM: Dict[str, int] = {qid: norm for qid, norm in QUESTIONS}

INPUT_PATH = "resultdata.jsonl"
OUTPUT_PATH = "resultdata_longitudinal.jsonl"

TOTAL_ATTEMPTS_PER_ID = 5  # week 1..5


def clamp_1_5(x: int) -> int:
    return 1 if x < 1 else 5 if x > 5 else x


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


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def extreme_target_for_norm(norm: int, rng: random.Random) -> int:
    if norm >= 4:
        return 1
    if norm <= 2:
        return 5
    return rng.choice([1, 5])


def healthy_truthful_next(prev: int, norm: int, rng: random.Random) -> int:
    delta = rng.choices([-1, 0, 1], weights=[10, 80, 10], k=1)[0]
    candidate = clamp_1_5(prev + delta)

    # light pull toward norm to reduce random walk
    if candidate != norm and rng.random() < 0.15:
        candidate += -1 if candidate > norm else 1

    return clamp_1_5(candidate)


def healthy_lying_next(prev: int, rng: random.Random) -> int:
    if rng.random() < 0.60:
        delta = rng.choices([-2, -1, 0, 1, 2], weights=[15, 20, 30, 20, 15], k=1)[0]
        return clamp_1_5(prev + delta)
    return rng.randint(1, 5)


def infected_truthful_next(prev: int, target: int, rng: random.Random) -> int:
    if prev == target:
        if rng.random() < 0.05:
            return clamp_1_5(prev + rng.choice([-1, 1]))
        return prev

    step = -1 if prev > target else 1
    candidate = prev + step

    # noise
    p = rng.random()
    if p < 0.10:
        candidate = prev
    elif p > 0.95:
        candidate = prev + 2 * step

    return clamp_1_5(candidate)


def infected_lying_next(prev: int, rng: random.Random) -> int:
    if rng.random() < 0.70:
        return rng.randint(1, 5)
    return rng.choices([1, 2, 3, 4, 5], weights=[35, 10, 10, 10, 35], k=1)[0]


def evolve_answers(
    profile: str,
    baseline_answers: Dict[str, int],
    attempts_total: int,
    rng: random.Random,
) -> List[Dict[str, int]]:
    all_attempts: List[Dict[str, int]] = [dict(baseline_answers)]

    infected_targets: Dict[str, int] = {}
    if profile == "Infected-Truthful":
        for qid, norm in NORM.items():
            infected_targets[qid] = extreme_target_for_norm(norm, rng)

    for _ in range(2, attempts_total + 1):
        prev = all_attempts[-1]
        nxt: Dict[str, int] = {}

        for qid, norm in NORM.items():
            prev_val = int(prev.get(qid, norm))

            if profile == "Healthy-Truthful":
                nxt[qid] = healthy_truthful_next(prev_val, norm, rng)
            elif profile == "Healthy-Lying":
                nxt[qid] = healthy_lying_next(prev_val, rng)
            elif profile == "Infected-Truthful":
                nxt[qid] = infected_truthful_next(prev_val, infected_targets[qid], rng)
            elif profile == "Infected-Lying":
                nxt[qid] = infected_lying_next(prev_val, rng)
            else:
                nxt[qid] = prev_val

        all_attempts.append(nxt)

    return all_attempts


def main() -> None:
    rng = random.Random(12345)

    rows = read_jsonl(INPUT_PATH)

    # Baseline per id (first occurrence)
    baselines: Dict[int, Dict[str, Any]] = {}
    for r in rows:
        if "id" not in r:
            continue
        pid = int(r["id"])
        if pid not in baselines:
            baselines[pid] = r

    out_rows: List[Dict[str, Any]] = []

    for pid, base in baselines.items():
        profile = str(base.get("name", "Unknown"))
        baseline_answers = base.get("answers", {})
        if not isinstance(baseline_answers, dict):
            continue

        attempts = evolve_answers(
            profile=profile,
            baseline_answers=baseline_answers,
            attempts_total=TOTAL_ATTEMPTS_PER_ID,
            rng=rng,
        )

        # questionnaire_version == week/attempt number
        for attempt_idx, answers in enumerate(attempts, start=1):
            out_rows.append(
                {
                    "id": pid,
                    "name": profile,
                    "answers": answers,
                    "questionnaire_version": attempt_idx,
                }
            )

    write_jsonl(OUTPUT_PATH, out_rows)
    print(
        f"Wrote {len(out_rows)} rows to {OUTPUT_PATH} "
        f"({len(baselines)} ids x {TOTAL_ATTEMPTS_PER_ID} weeks)."
    )


if __name__ == "__main__":
    main()
