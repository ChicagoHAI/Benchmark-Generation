import json
import sys
import requests

url = "http://indigo.cs.uchicago.edu:8000/v1/chat/completions"
headers = {"Content-Type": "application/json"}

data = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": []
}

def chat(sentence: str) -> dict:
    user_message = {"role": "user", "content": sentence}
    data["messages"].append(user_message)
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()

def chat_message(sentence: str) -> str:
    response = chat(sentence)
    assistant_message = {
        "role": "assistant",
        "content": response["choices"][0]["message"]["content"]
    }
    data["messages"].append(assistant_message)
    return assistant_message["content"]

def load_problems(json_path: str) -> list[str]:
    with open(json_path, 'r', encoding='utf-8') as f:
        obj = json.load(f)

    probs = obj.get("problems")
    if not isinstance(probs, list):
        raise ValueError(f"Expected 'problems' to be a list, got {type(probs)}")
    if any(not isinstance(x, str) for x in probs):
        raise ValueError("All items in 'problems' must be strings")
    return probs

def main():
    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} ./GSM8k/failing_questions.json [out.json]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else "generated_failing_questions.json"

    try:
        problems = load_problems(input_path)
    except Exception as e:
        print(f"Error loading problems: {e}", file=sys.stderr)
        sys.exit(2)

    results = []
    for idx, prob in enumerate(problems, 1):
        print(f"[{idx}/{len(problems)}]→ Sending prompt to LLM…", end="", flush=True)
        try:
            reply = chat_message(prob + " Generate a similar math problem by modifying the numbers. No need to solve the problems. \
                                Output only the new problem. Don't add anything unrelated.")
            print(" got response.")
        except Exception as e:
            print(f" ERROR: {e}")
            reply = None
        # clear the context history for each generation
        data["messages"].clear()
        results.append({
            "original_problems": prob,
            "generated_problems": reply
        })

    # write out all problem pairs
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, ensure_ascii=False, indent=2)

    print(f"\nDone. Wrote {len(results)} entries to {output_path}")


if __name__ == "__main__":
    main()

