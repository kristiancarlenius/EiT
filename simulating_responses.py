#!/usr/bin/env python3

from __future__ import annotations
import json
import os
import random
from typing import Dict, Any, List


QUESTIONS = [
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
    ("q25", 1, True),
    ("q26", 4, True),
    ("q27", 4, True),
    ("q28", 1, True),
    ("q29", 3, True)
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
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]

        elif (qid[1]==2):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[25, 40, 20, 10, 5], k=1)[0]

        elif (qid[1]==4):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25], k=1)[0]

        elif (qid[1]==5):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[3, 7, 15, 25, 50], k=1)[0]

        else:
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[5, 25, 40, 25, 5], k=1)[0]
    print(ret)
    return ret

def Infected_True(Questions):
    ret = {}
    for qid in Questions:
        if (qid[1]==1):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[3, 7, 15, 25, 50] , k=1)[0]

        elif (qid[1]==2):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25], k=1)[0]

        elif (qid[1]==4):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[25, 40, 20, 10, 5], k=1)[0]

        elif (qid[1]==5):
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]

        else:
            ret[qid[0]] = random.choices([1, 2, 3, 4, 5], weights=[30, 17, 6, 17, 30], k=1)[0]
    return ret

import random
from typing import Dict, Any, List, Tuple

# QUESTIONS: List[Tuple[qid, norm, contradictory]] already defined

def clamp_1_5(x: int) -> int:
    return 1 if x < 1 else 5 if x > 5 else x

def sample_near(value: int, rng: random.Random, tight: bool = True) -> int:
    """
    Sample near a target Likert value.
    tight=True makes it stick closer (more realistic "strategic" answering).
    """
    if tight:
        return rng.choices(
            [clamp_1_5(value-1), value, clamp_1_5(value+1)],
            weights=[20, 60, 20],
            k=1
        )[0]
    return rng.choices(
        [clamp_1_5(value-2), clamp_1_5(value-1), value, clamp_1_5(value+1), clamp_1_5(value+2)],
        weights=[10, 20, 40, 20, 10],
        k=1
    )[0]

def socially_desirable_answer(norm: int, rng: random.Random) -> int:
    """
    Push towards 'healthy-looking' response.
    Here we assume norm itself is healthy, so stick to it or slightly toward center.
    """
    # Mild centering: avoid extremes unless norm is extreme.
    if norm in (1, 5):
        return sample_near(norm, rng, tight=True)
    return rng.choices([2, 3, 4], weights=[25, 50, 25], k=1)[0]

def plausible_random(rng: random.Random) -> int:
    """
    Human-like random (NOT uniform): middle answers more likely, extremes rarer.
    """
    return rng.choices([1, 2, 3, 4, 5], weights=[8, 22, 40, 22, 8], k=1)[0]


def generate_liar_answers(
    questions: List[Tuple[str, int, bool]],
    rng: random.Random,
    infected: bool,
) -> Dict[str, int]:
    """
    Liar model = mixture of strategies.
    infected=True means their "true" tendency might drift sick, but they attempt to mask it.
    """
    # Participant-level style bias (stable within one run; your longitudinal expansion will evolve later)
    style_bias = rng.choices([-1, 0, 1], weights=[15, 70, 15], k=1)[0]

    # Pick a lying strategy for this run (you can later make it per-id stable if you want)
    strategy = rng.choices(
        ["social", "defensive", "overcompensate_contradict", "plausible_random"],
        weights=[45, 25, 20, 10],
        k=1
    )[0]

    ret: Dict[str, int] = {}

    for qid, norm, is_contra in questions:
        norm_biased = clamp_1_5(norm + style_bias)

        if strategy == "social":
            # Keep non-contradictory close to norm; contradictories sometimes manipulated.
            if not is_contra:
                ans = sample_near(norm_biased, rng, tight=True)
            else:
                # If you want liars to "slip" more on contradictory items:
                if rng.random() < 0.60:
                    # move away from norm by 1-2
                    direction = rng.choice([-1, 1])
                    step = rng.choices([1, 2], weights=[70, 30], k=1)[0]
                    ans = clamp_1_5(norm_biased + direction * step)
                else:
                    ans = sample_near(norm_biased, rng, tight=True)

        elif strategy == "defensive":
            # Lots of 2-4 (avoid extremes), look consistent.
            if rng.random() < 0.80:
                ans = rng.choices([2, 3, 4], weights=[30, 40, 30], k=1)[0]
            else:
                ans = sample_near(norm_biased, rng, tight=True)

        elif strategy == "overcompensate_contradict":
            # Your desired signature:
            # Deviate on contradictory questions, stay close on non-contradictory.
            if is_contra:
                # deliberate deviation
                direction = -1 if norm_biased >= 4 else (1 if norm_biased <= 2 else rng.choice([-1, 1]))
                step = rng.choices([1, 2, 3], weights=[55, 30, 15], k=1)[0]
                ans = clamp_1_5(norm_biased + direction * step)
            else:
                ans = sample_near(norm_biased, rng, tight=True)

        else:  # plausible_random
            # Somewhat random but human-like; still not uniform.
            ans = plausible_random(rng)

        # If infected and lying: sometimes they fail to fully mask and drift "sick-ish" on a few items.
        # This creates realistic overlap and makes classification harder (and more honest).
        if infected and rng.random() < 0.15:
            # push 1 step toward "sick extreme direction"
            if norm_biased >= 4:
                ans = clamp_1_5(ans - 1)
            elif norm_biased <= 2:
                ans = clamp_1_5(ans + 1)
            else:
                ans = clamp_1_5(ans + rng.choice([-1, 1]))

        ret[qid] = ans

    return ret


def Healthy_Lying(questions):
    rng = random.Random()  # uses global randomness
    return generate_liar_answers(questions, rng=rng, infected=False)

def Infected_Lying(questions):
    rng = random.Random()
    return generate_liar_answers(questions, rng=rng, infected=True)


PATTERNS = {
    "Healthy-Truthful": Normal_True,
    "Healthy-Lying": Healthy_Lying,          # updated
    "Infected-Truthful": Infected_True,
    "Infected-Lying": Infected_Lying,        # updated
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
    pattern_cycle: List[str] = ["Healthy-Truthful", "Healthy-Lying", "Infected-Truthful", "Infected-Lying"]

    total_runs = 10000
    for i in range(total_runs):
        pattern_name = pattern_cycle[random.choices([0, 1, 2, 3], weights=[90, 9.7, 0.2, 0.1], k=1)[0]]
        record = simulate_one_run(pattern_name, rng)
        append_jsonl(RESULTS_PATH, record)

    print(f"Wrote {total_runs} simulated runs to {RESULTS_PATH}.")


if __name__ == "__main__":
    main()
