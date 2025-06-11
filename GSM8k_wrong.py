import requests
from datasets import load_dataset
import json
import re
import sys

# Config
BASE_URL = "http://indigo.cs.uchicago.edu:8000/v1"
API_KEY = "sk"  # dummy key if not needed
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

# Load 10 samples for testing (adjust "test[:10]" to more samples if needed)
dataset = load_dataset("gsm8k", "main", split="test")

def format_prompt(question):
    return f"{question}\n"

def extract_answer(text):
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", text)
    if matches:
        ans = matches[-1]
        return int(ans) if ans.isdigit() else float(ans)
    return None

def get_first_answer(text):
    split_text = re.split(r'(Question:|Q\d+:)', text)
    return split_text[0].strip()

def query_model(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 2048,
        "temperature": 0.0,
    }
    response = requests.post(f"{BASE_URL}/completions", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["text"]

# 只保留 wrong 的条目
results = {
    "problems": [],
    "solutions": [],
    "answers": [],
    "label": []
}

correct = 0
wrong_examples = []

for i, example in enumerate(dataset):
    question = example["question"]
    actual_solution = example["answer"]
    gt_answer = extract_answer(actual_solution)

    prompt = format_prompt(question)
    model_output = query_model(prompt)

    clean_output = get_first_answer(model_output)
    pred_answer = extract_answer(clean_output)

    # Logging to 控制台
    print("=" * 60)
    print(f"Q{i+1}: {question}")
    print("Model Output:", model_output.strip())
    print("Cleaned Output:", clean_output)
    print("Ground Truth (num):", gt_answer)
    print("Predicted (num):", pred_answer)

    if pred_answer == gt_answer:
        correct += 1
    else:
        # 只有 wrong 的才追加到 results
        results["problems"].append(question)
        results["solutions"].append(actual_solution)
        results["answers"].append(clean_output)
        results["label"].append("wrong")

        wrong_examples.append({
            "index": i+1,
            "question": question,
            "ground_truth": gt_answer,
            "predicted": pred_answer,
            "model_output": model_output.strip(),
            "cleaned_output": clean_output
        })

# 输出总体准确率
print(f"\n✅ Accuracy: {correct}/{len(dataset)} = {correct / len(dataset):.2%}")

# 输出错误示例
print("\n\n--- Wrong Predictions ---")
for we in wrong_examples:
    print(f"Q{we['index']}: {we['question']}")
    print(f"Ground Truth: {we['ground_truth']}")
    print(f"Predicted: {we['predicted']}")
    print(f"Model Output: {we['model_output']}")
    print(f"Cleaned Output: {we['cleaned_output']}")
    print("-" * 60)

# 仅把 wrong 的条目写入 JSON
with open("results.json", "w") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\nResults have been written to results.json.")
