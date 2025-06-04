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

summary = []

stage_one_loop_time = 2
stage_two_loop_time = 2
stage_three_loop_time = 2
stage_four_loop_time = 1

stage_one_prompt = ["Help me to think deeply about the specific task this benchmark is \
                    going to test and help me to narrow down the scope of the benchmark. \
                    ask clarifying questions about any ambiguities. Do we want to test the generation ability \
                    or the evaluation ability? Do we want to have a wide range or a small range to cover in the \
                    benchmark? (For example, If I say generate \
                    a benchmark about math, you ask questions and give advice to help me think about the \
                    specific math problem I want. Do I want to test algebra? Calculus? Statistics? or maybe Linear Algebra? \
                    and what specific type of algebra question? Statistic questions? or Calculus questions?)", 
                    "Now, take all of our discussions into account, summarize everything, especially what we have reached \
                    and agreed on. What specific task do we want our benchmark to test? What specofic topic do \
                    we want our benchmark to include? etc."]
stage_two_prompt = ["We have discussed and reached a conclusion on what specific task we want our benchmark to test. \
                     Here is a summary you made for our previous discussions. Now, I want you to help me to think deeply \
                     about the source of data we want to evaluate on with the benchmark. Do we want to evaluate on talks? Books? \
                     News? Academic papers? Political talks? Or maybe LLM generated content?", 
                    "Now, take all of our discussions into account, summarize everything, especially what we have reached \
                     and agreed on."]
stage_three_prompt = ["We have discussed on what specific task we want out benchmark to test, and we have discussed what \
                      source of data we want to evaluate on with the benchmark. Here is a summary you made for our previous \
                      discussions. Now, I want you to help me to think deeply about the specific rubric and criteria of our benchmark. \
                      How are we going to evaluate? What rules do we have? How do we distinguish between good and bad or between right and wrong? \
                      Ask clarifying questions about any ambiguities, leading me to think in depth.", 
                    "Now, take all of our discussions into account, summarize everything, especially what we have reached \
                     and agreed on."]
stage_four_prompt = ["We have discussed on what specific task we want out benchmark to test, what \
                      source of data we want to evaluate on with the benchmark, and the specific rubrics we want \
                      to be included in the benchmark. Here is a summary you made for our previous \
                      discussions. Now, I want you to start generate this benchmark.", ""]

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


def chat(sentence):
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


def extract_summary():
    summary.append(data["messages"][-1])
    data["messages"] = summary[:]


def interactive(sentence, loop_time, start_prompt, end_prompt, stage):
    print(chat_message(sentence + start_prompt))
    sentence = ask_input()
    for counter in range(loop_time):
        if (stage != 4):
            print(chat_message(sentence + " consider all the interactions and discussions we had before. \
                You can also try to search the Internet for reference. Remember our focus is on \
                iscussing and reaching a conclusion on what exactly we want, instead of merely generating\
                a benchmark. Therefore, don't generate the whole benchmark directly. Only give samples \
                and ask for feedbacks to further the discussion."))
        else:
            print(chat_message(sentence))
        sentence = ask_input()
    print(chat_message(sentence + end_prompt))
    return None

def generation_process(remove_history = True):
    if remove_history:
        summary.clear()
    sentence = ask_input("Please provide the details of the benchmark you want to generate: ")
    # stage 1, discuss and narrow down the task
    interactive(sentence, stage_one_loop_time, stage_one_prompt[0], stage_one_prompt[1], 1)
    extract_summary()
    # stage 2, discuss and narrow down the data source
    sentence = ask_input("Please provide the details of the data source you plan to test: ")
    interactive(sentence, stage_two_loop_time, stage_two_prompt[0], stage_two_prompt[1], 2)
    extract_summary()
    # stage 3, discuss and narrow down the rubric of the benchmark
    sentence = ask_input("Please provide the details of the rubric (if you have any idea) you want the evaluation to be based on: ")
    interactive(sentence, stage_three_loop_time, stage_three_prompt[0], stage_three_prompt[1], 3)
    extract_summary()
    # stage 4, generate examples for evaluation
    sentence = ask_input("Do you have anything to add before we generate some samples for the benchmark: ")
    interactive(sentence, stage_four_loop_time, stage_four_prompt[0], stage_four_prompt[1], 4)


if __name__=="__main__":
    with open("output.txt", "a") as f:
        tee = Tee(sys.stdout, f)
        sys.stdout = tee
        generation_process()
        restart = ask_input("Are you satisfied with the benchmark samples? Do you want to start all over? Please reply 'Y' or 'N'")
        if restart == 'Y':
            generation_process()
        
