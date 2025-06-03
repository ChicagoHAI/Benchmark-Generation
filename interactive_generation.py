import requests
url = "http://indigo.cs.uchicago.edu:8000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

data = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
    ]
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

def ask_input(prompt = "Input here: "):
    sentence = input(prompt)
    f.write(sentence + "\n")
    f.flush()
    return sentence


def chat (sentence):
    user_message = {
            "role": "user",
            "content": sentence
        }
    data["messages"].append(user_message)
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def chat_message (sentence):
    response = chat(sentence)
    assistant_message = {
        "role": "assistant",
        "content": response["choices"][0]['message']['content']
        }
    data["messages"].append(assistant_message)
    return response["choices"][0]['message']['content']


def interactive (sentence):
    print(chat_message(sentence + " rememver to consider the potential ambiguities \
        in the benchmark generation requirements, ask clarifying questions and details about the benchmark. \
        Take especial focus on the criteria of the benchmark. Think how should the rubric for the benchmark be formed,\
        and provide ideas on rubric formation. Don't generate the whole benchmark directly."))
    sentence = ask_input()
    for counter in range(5):
        print(chat_message(sentence + " consider all the interactions and discussions we had before. \
            You can also try to search the Internet for reference."))
        sentence = ask_input()
    print(chat_message(sentence + " Now, given all the details, incorporate \
        all our interactions and discussions to generate the benchmark samples. \
        Remember to provide not only the questions but also the answers."))
    return None


if __name__=="__main__":
    with open("output.txt", "a") as f:
        tee = Tee(sys.stdout, f)
        sys.stdout = tee
        sentence = ask_input("Please provide the details of the benchmark you want to generate: ")
        interactive(sentence)
