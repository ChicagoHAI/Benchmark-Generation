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
dataset = load_dataset("gsm8k", "main", split="test[:10]")

def format_prompt(question):
    return f"Question: {question}\nAnswer:"

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

# Prepare lists for JSON output, 加入 solutions 字段
results = {
    "problems": [],
    "solutions": [],       # 新增：存储数据集里的标准解答（包含解题思路 + 最终答案）
    "answers": [],         # 模型的输出（cleaned）
    "label": []            # correct / wrong
}

correct = 0
wrong_examples = []

for i, example in enumerate(dataset):
    question = example["question"]
    actual_solution = example["answer"]           # GSM8K中的完整解
    gt_answer = extract_answer(actual_solution)   # 提取数值型的“标准答案”
    
    prompt = format_prompt(question)
    model_output = query_model(prompt)
    
    clean_output = get_first_answer(model_output)
    pred_answer = extract_answer(clean_output)
    
    # Logging
    print("=" * 60)
    print(f"Q{i+1}: {question}")
    print("Model Output:", model_output.strip())
    print("Cleaned Output:", clean_output)
    print("Ground Truth (num):", gt_answer)
    print("Predicted (num):", pred_answer)
    
    # Append to results
    results["problems"].append(question)
    results["solutions"].append(actual_solution)  # 将实际解答存入
    results["answers"].append(clean_output)
    
    if pred_answer == gt_answer:
        results["label"].append("correct")
        correct += 1
    else:
        results["label"].append("wrong")
        wrong_examples.append({
            "index": i+1,
            "question": question,
            "ground_truth": gt_answer,
            "predicted": pred_answer,
            "model_output": model_output.strip(),
            "cleaned_output": clean_output
        })

# 打印总体准确率
print(f"\n✅ Accuracy: {correct}/{len(dataset)} = {correct / len(dataset):.2%}")

# 打印错误示例
print("\n\n--- Wrong Predictions ---")
for we in wrong_examples:
    print(f"Q{we['index']}: {we['question']}")
    print(f"Ground Truth: {we['ground_truth']}")
    print(f"Predicted: {we['predicted']}")
    print(f"Model Output: {we['model_output']}")
    print(f"Cleaned Output: {we['cleaned_output']}")
    print("-" * 60)

# Write the results to a JSON file that now includes the problem, the dataset solution, the model answer, and the label
with open("results.json", "w") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\nResults have been written to results.json.")
