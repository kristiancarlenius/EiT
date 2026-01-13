#!/usr/bin/env python3

from __future__ import annotations
import json
import os
import random
from typing import Dict, Any, List


QUESTIONS = ["q1", "q2", "q3"]  # Must match questionnaire qids
RESULTS_PATH = "resultdata.jsonl"

def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ---- Pattern generators (return answer 1..5) ----

def pattern_mostly_agree(rng: random.Random) -> int:
    # Heavily weighted to 4-5
    return rng.choices([1, 2, 3, 4, 5], weights=[3, 8, 1, 35, 53], k=1)[0]


def pattern_mostly_disagree(rng: random.Random) -> int:
    return rng.choices([1, 2, 3, 4, 5], weights=[53, 35, 1, 8, 3], k=1)[0]


def pattern_neutral(rng: random.Random) -> int:
    return rng.choices([1, 2, 3, 4, 5], weights=[15, 30, 10, 30, 15], k=1)[0]


def pattern_polarized(rng: random.Random) -> int:
    # Mostly extremes 1 or 5
    return rng.choices([1, 2, 3, 4, 5], weights=[45, 5, 0, 5, 45], k=1)[0]


def pattern_alternating_factory() -> Any:
    # Alternates between agree-ish and disagree-ish
    state = {"toggle": False}

    def _inner(rng: random.Random) -> int:
        state["toggle"] = not state["toggle"]
        if state["toggle"]:
            return rng.choices([3, 4, 5], weights=[30, 5, 65], k=1)[0]
        return rng.choices([1, 2, 3], weights=[65, 5, 30], k=1)[0]

    return _inner


PATTERNS = {
    "mostly_agree": pattern_mostly_agree,
    "mostly_disagree": pattern_mostly_disagree,
    "neutral": pattern_neutral,
    "polarized": pattern_polarized,
    "alternating": pattern_alternating_factory(),  # stateful
}


def simulate_one_run(pattern_name: str, rng: random.Random) -> Dict[str, Any]:
    pattern_fn = PATTERNS[pattern_name]
    answers = {qid: pattern_fn(rng) for qid in QUESTIONS}

    return {
        "id": random.randint(10000000, 99999999),
        "name": pattern_name,
        "answers": answers,
        "questionnaire_version": 1,
    }


def main() -> None:
    rng = random.Random(42)  # deterministic; change/remove for different runs

    # Example: generate 200 simulated runs across 5 “people”
    names = ["sim_alex", "sim_bella", "sim_chris", "sim_dana", "sim_eli"]
    pattern_cycle: List[str] = ["mostly_agree", "neutral", "polarized", "mostly_disagree", "alternating"]

    total_runs = 5000
    for i in range(total_runs):
        pattern_name = pattern_cycle[i % len(pattern_cycle)]
        record = simulate_one_run(pattern_name, rng)
        append_jsonl(RESULTS_PATH, record)

    print(f"Wrote {total_runs} simulated runs to {RESULTS_PATH}.")


if __name__ == "__main__":
    main()
