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


QUESTIONS: List[Question] = [
    Question("q1", "I find it easy to focus on tasks."),
    Question("q2", "I feel stressed in my daily life."),
    Question("q3", "I enjoy working in teams."),
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
        "id": random.randint(1000000, 9999999),
        "name": name,
        "answers": answers,
        "questionnaire_version": 1,
    }

    append_jsonl(results_path, record)
    print(f"\nSaved results to {results_path} (appended as one new line).")


if __name__ == "__main__":
    main()
