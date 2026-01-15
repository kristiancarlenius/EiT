#!/usr/bin/env python3

from __future__ import annotations
import json
import os
import random
from typing import Dict, Any, List


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
    ]  # Must match questionnaire qids

RESULTS_PATH = "resultdata.jsonl"

def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ---- Pattern generators (return answer 1..5) ----

def Normal_True(Questions):
    ret = {}
    for qid in Questions:
        if (qid[1]==1):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]

        elif (qid[1]==2):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[25, 40, 20, 10, 5], k=1)[0]

        elif (qid[1]==4):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25], k=1)[0]

        elif (qid[1]==5):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[3, 7, 15, 25, 50], k=1)[0]

        else:
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[5, 25, 40, 25, 5], k=1)[0]
    return ret

def Infected_True(Questions):
    ret = {}
    for qid in Questions:
        if (qid[1]==1):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[3, 7, 15, 25, 50] , k=1)[0]

        elif (qid[1]==2):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25], k=1)[0]

        elif (qid[1]==4):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[25, 40, 20, 10, 5], k=1)[0]

        elif (qid[1]==5):
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]

        else:
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[30, 17, 6, 17, 30], k=1)[0]
    return ret

def Normal_False(Questions):
    ret = {}
    for qid in Questions:
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[20, 20, 20, 20, 20], k=1)[0]
    return ret

def Infected_False(Questions):
    ret = {}
    for qid in Questions:
            ret[qid[0]] = random.Random.choice([1, 2, 3, 4, 5], weights=[20, 20, 20, 20, 20], k=1)[0]
    return ret

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
    "Healthy-Truthful": Normal_True,
    "Healthy-Lying": Normal_False,
    "Infected-Truthful": Infected_True,
    "Infected-Lying": Infected_False,
}


def simulate_one_run(pattern_name: str, rng: random.Random) -> Dict[str, Any]:
    pattern_fn = PATTERNS[pattern_name]
    answers = pattern_fn(QUESTIONS)

    return {
        "id": random.randint(10000000, 99999999),
        "name": pattern_name,
        "answers": answers,
        "questionnaire_version": 1,
    }


def main() -> None:
    rng = random.Random(42)  # deterministic; change/remove for different runs
    pattern_cycle: List[str] = ["mostly_agree", "neutral", "polarized", "mostly_disagree", "alternating"]

    total_runs = 500000
    for i in range(total_runs):
        pattern_name = pattern_cycle[i % len(pattern_cycle)]
        record = simulate_one_run(pattern_name, rng)
        append_jsonl(RESULTS_PATH, record)

    print(f"Wrote {total_runs} simulated runs to {RESULTS_PATH}.")


if __name__ == "__main__":
    main()
