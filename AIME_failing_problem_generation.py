#!/usr/bin/env python3
import argparse
import json
import re
import sys
import requests

API_URL = "http://indigo.cs.uchicago.edu:8000/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

def chat_message(prompt: str) -> str:
    """Send one‐shot prompt, return the assistant’s raw content."""
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def load_problems(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    probs = obj.get("problems")
    if not isinstance(probs, list) or any(not isinstance(x, str) for x in probs):
        raise ValueError("'problems' must be a list of strings")
    return probs

def parse_generated(reply: str) -> list[str]:
    """Try to JSON‐parse; else split lines & strip bullets."""
    text = reply.strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            arr = json.loads(text)
            if all(isinstance(x, str) for x in arr):
                return arr
        except json.JSONDecodeError:
            pass

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # strip leading numbers like "1. " or "2) "
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        lines.append(line)
    return lines

def build_parser():
    p = argparse.ArgumentParser(
        description="Take each problem, ask LLM to generate N variants, save JSON."
    )
    p.add_argument("input", help="JSON file with top‐level 'problems': [\"…\",…]")
    p.add_argument(
        "-o", "--output",
        default="generated.json",
        help="Output path for JSON results (default: %(default)s)"
    )
    p.add_argument(
        "-n", "--num",
        type=int,
        default=5,
        help="How many variants to generate per problem (default: %(default)s)"
    )
    return p

def main():
    args = build_parser().parse_args()

    try:
        problems = load_problems(args.input)
    except Exception as e:
        print(f"Error loading '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    total = len(problems)
    for idx, prob in enumerate(problems, 1):
        print(f"[{idx}/{total}] Generating {args.num} variants…", end="", flush=True)
        prompt = (
            f"""{prob}
                Generate {args.num} similar math problems. No need to solve. \
                Output only a JSON array of strings.""")
        try:
            raw = chat_message(prompt)
            generated = parse_generated(raw)
            print(" done.")
        except Exception as e:
            print(f" ERROR: {e}")
            generated = []

        results.append({
            "original": prob,
            "generated": generated
        })

    with open(args.output, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(results)} entries to '{args.output}'.")

if __name__ == "__main__":
    main()

