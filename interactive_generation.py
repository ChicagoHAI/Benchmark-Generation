import requests
url = "http://indigo.cs.uchicago.edu:8000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

import sys

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for s in self.streams:
            s.write(message)
            s.flush()  # Ensure it writes immediately

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except (ValueError, OSError):
                pass


def chat (sentence):
    data = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": sentence
        }
    ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def chat_message (sentence):
    response = chat(sentence)
    return response["choices"][0]['message']['content']


def interactive (sentence):
    for counter in range(5):
        print(chat_message(sentence + "first ask for details, don't generate directly"))
        sentence = input("Input here:")
    print(chat_message(sentence + "Now, generate the benchmark."))
    return None


if __name__=="__main__":
    with open("output.txt", "a") as f:
        tee = Tee(sys.stdout, f)
        sys.stdout = tee
        sentence = input("Please provide the detail of the benchmark you want to generate: ")
        interactive(sentence)




