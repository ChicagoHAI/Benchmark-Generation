#!/usr/bin/env python3
import json
import sys

def filter_wrong(input_path: str, output_path: str):
    # Load the full evaluation results
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    problems  = data.get("problems", [])
    solutions = data.get("solutions", [])
    answers   = data.get("answers", [])
    labels    = data.get("label", [])

    # Prepare filtered lists
    wrong_problems  = []
    wrong_solutions = []
    wrong_answers   = []
    wrong_labels    = []

    for p, s, a, l in zip(problems, solutions, answers, labels):
        is_wrong = False
        # handle boolean labels
        if isinstance(l, bool):
            is_wrong = (l is False)
        # handle string labels "wrong"
        elif isinstance(l, str):
            is_wrong = (l.strip().lower() == "wrong")

        if is_wrong:
            wrong_problems .append(p)
            wrong_solutions.append(s)
            wrong_answers  .append(a)
            wrong_labels   .append(l)

    # Build the filtered output dict
    filtered = {
        "problems":  wrong_problems,
        "solutions": wrong_solutions,
        "answers":   wrong_answers,
        "label":     wrong_labels
    }

    # Write to new JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"Filtered {len(wrong_problems)} wrong items to '{output_path}'")


if __name__ == "__main__":
    if not (2 <= len(sys.argv) <= 3):
        print("Usage: python filter_wrong.py <input.json> [<output.json>]")
        sys.exit(1)

    in_path  = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) == 3 else "failing_questions.json"
    filter_wrong(in_path, out_path)
