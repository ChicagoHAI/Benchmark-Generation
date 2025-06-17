#!/usr/bin/env python3
import requests
import re
import json
import sys
from datasets import load_dataset

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_URL   = "http://indigo.cs.uchicago.edu:8000/v1"
API_KEY    = "sk"  # replace/remove if unneeded
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

# Load first 100 examples from train as our “test” set
test_ds = load_dataset("gneubig/aime-1983-2024", split="train")

# ── Helpers ────────────────────────────────────────────────────────────────────
def format_prompt(question: str) -> str:
    return f"Question: {question}\nAnswer:"

def extract_answer(text: str):
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", text)
    if not nums:
        return None
    last = nums[-1]
    return int(last) if last.isdigit() else float(last)

def get_first_answer(text: str) -> str:
    parts = text.split("Answer:")
    return parts[-1].strip() if len(parts) > 1 else text.strip()

def query_model(prompt: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model":       MODEL_NAME,
        "prompt":      prompt,
        "max_tokens":  8000,
        "temperature": 0.0
    }
    resp = requests.post(f"{BASE_URL}/completions", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["text"].strip()

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    out_path = sys.argv[1] if len(sys.argv) == 2 else "evaluation_results.json"

    problems  = []
    solutions = []
    answers   = []
    labels    = []

    correct = 0
    total   = len(test_ds)

    for i, example in enumerate(test_ds, start=1):
        question    = example["Question"]
        gt_answer   = extract_answer(example["Answer"])
        prompt      = format_prompt(question)
        raw_output  = query_model(prompt)
        llm_answer  = get_first_answer(raw_output)
        pred_answer = extract_answer(llm_answer)
        if (pred_answer == gt_answer):
            is_correct  = "correct"
        else:
            is_correct = "wrong"

        # Console logging
        print(f"[{i}/{total}] Q: {question}")
        # print("  Raw LLM output:", raw_output)
        print(f"  Parsed answer: {llm_answer} | GT: {gt_answer} | Correct? {is_correct}")

        # collect for final JSON
        problems.append(question)
        solutions.append(gt_answer)
        answers.append(llm_answer)
        labels.append(is_correct)

        if is_correct == "correct":
            correct += 1

    accuracy = correct / total if total else 0
    print(f"\n✅ Accuracy: {correct}/{total} = {accuracy:.2%}")

    # build output dict
    out_dict = {
        "problems":  problems,
        "solutions": solutions,
        "answers":   answers,
        "label":     labels
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, ensure_ascii=False, indent=2)

    print(f"Wrote {total} records to '{out_path}'")

if __name__ == "__main__":
    main()