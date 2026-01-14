#!/usr/bin/env python3
"""
CLI questionnaire that stores each completed run as one JSON object per line (JSONL).
- Prompts for a name (used as ID)
- Asks Likert questions with 5 fixed options
- Appends results to a single file: results.jsonl
"""

from __future__ import annotations
import random
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any


LIKERT_OPTIONS = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]


@dataclass(frozen=True)
class Question:
    qid: str
    text: str
    norm: int
    cont: bool


QUESTIONS: List[Question] = [
    Question("q1", "I often feel that I am on an emotional high", 2, False),
    Question("q2", "I flare up quickly but get over it quickly", 1, False),
    Question("q3", "When something upsets me I try to keep my emotions in balance", 5, True),
    Question("q4", "I wonder why sometimes I feel so bitter about things", 1, False),
    Question("q5", "I can usually understand my feelings", 5, True),
    Question("q6", "When I’m upset, I can’t concentrate on anything", 2, False),
    Question("q7", "I feel sad when I suffer even minor setbacks", 2, False),
    Question("q8", "Sometimes I fly off the handle for no good reason", 1, False),
    Question("q9", "Not knowing whether I am infected makes me feel emotionally distressed rather than just worried", 2, False),
    Question("q10", "Dealing with my emotions is simple", 4, True),
    Question("q11", "When I’m upset, I can’t seem to manage my emotions", 4, False),
    Question("q12", "Being upset makes me feel worthless", 1, False),
    Question("q13", "I have threatened people I know", 1, False),
    Question("q14", "I am an even-tempered person", 5, True),
    Question("q15", "I have trouble controlling my temper", 1, False),
    Question("q16", "I sometimes feel like a powder keg ready to explode", 1, False),
    Question("q17", "I have become so mad that I have broken things", 1, False),
    Question("q18", "I get into fights a little more than the average person", 3, False),
    Question("q19", "I think I should “stop and think” more instead of jumping into things too quickly", 2, False),
    Question("q20", "I often do risky things without thinking of the consequences", 1, False),
    Question("q21", "When trying to make a decision, I find myself constantly chewing it over", 1, False),
    Question("q22", "I frequently buy things without thinking about whether or not I can really afford them", 1, False),
    Question("q23", "I don’t like to make decisions quickly, even simple decisions, such as choosing what to wear, or what to have for dinner", 1, True),
    Question("q24", "I would enjoy working at a job that required me to make a lot of split-second decisions", 2, False),
    """
    Question("q25", "My friends say that I’m somewhat argumentative  . Modify: that i have changed my personality", ),
    Question("q26", "Overall, how happy do you consider your life to be?"),
    Question("q27", "How happy do you feel right now, at this moment?"),
    Question("q28", "When I’m upset, my emotions are so overwhelming they prevent me from doing things"),
    Question("q29", "I like sports and games in which you have to choose your next move very quickly"),
    """
    # Add more questions here
]


def prompt_name() -> str:
    while True:
        name = input("Enter your name (ID): ").strip()
        if len(name) >= 2:
            return name
        print("Name must be at least 2 characters.")


def prompt_likert(question: Question) -> int:
    print("\n" + question.text)
    question_str = ""
    for i, opt in enumerate(LIKERT_OPTIONS, start=1):
        question_str += opt+" "
    print(question_str)#f"  {i}) {opt}")

    while True:
        raw = input("Select 1-5: ").strip()
        if raw.isdigit():
            val = int(raw)
            if 1 <= val <= 5:
                return val
        print("Invalid input. Please enter a number from 1 to 5.")


def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main() -> None:
    results_path = "resultdata.jsonl"

    name = prompt_name()
    answers: Dict[str, int] = {}

    print("\nAnswer the following questions:\n")

    for q in QUESTIONS:
        answers[q.qid] = prompt_likert(q)

    record = {
        "id": random.randint(10000000, 99999999),
        "sample": 1,
        "name": name,
        "answers": answers,
        "questionnaire_version": 1,
    }

    append_jsonl(results_path, record)
    print(f"\nSaved results to {results_path} (appended as one new line).")


if __name__ == "__main__":
    main()
