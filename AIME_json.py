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
        "max_tokens":  4096,
        "temperature": 0.0
    }
    resp = requests.post(f"{BASE_URL}/completions", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["text"].strip()

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # Optional second arg is the output JSON path
    out_path = sys.argv[1] if len(sys.argv) == 2 else "evaluation_results.json"

    results = []
    correct = 0
    total   = len(test_ds)

    for i, example in enumerate(test_ds, start=1):
        question   = example["Question"]
        gt_answer  = extract_answer(example["Answer"])
        prompt     = format_prompt(question)
        raw_output = query_model(prompt)
        solution   = get_first_answer(raw_output)
        pred_answer= extract_answer(solution)
        label      = (pred_answer == gt_answer)

        # Console logging
        print(f"[{i}/{total}] Q: {question}")
        print("  Raw LLM output:", raw_output)
        print("  Parsed answer:", solution, "| GT:", gt_answer, "| Correct?", label)

        if label:
            correct += 1

        # Collect for JSON
        results.append({
            "problem":   question,
            "solution":  solution,
            "answer":    gt_answer,
            "label":     label
        })

    accuracy = correct / total if total else 0
    print(f"\n✅ Accuracy: {correct}/{total} = {accuracy:.2%}")

    # Dump all records to JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Wrote {total} records to '{out_path}'")

if __name__ == "__main__":
    main()
