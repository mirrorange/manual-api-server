from generate import TextGenerateBase
from errors import InvalidRequestError
from uuid import uuid4
import tiktoken
import shutil
import json
import time
import os


def messages_to_prompt(body: dict):
    messages = body.get("messages", None)
    prompt = ""
    for m in messages:
        if "role" not in m:
            raise InvalidRequestError(
                message="messages: missing role", param="messages"
            )
        if "content" not in m:
            raise InvalidRequestError(
                message="messages: missing content", param="messages"
            )
        role = m["role"]
        content = m["content"]
        prompt += f"{role}: {content}\n"

    return prompt


def num_tokens_from_string(string: str, model_name: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


class ManualReply(TextGenerateBase):
    chat_dir: str
    model_name: str
    prompt: str
    completion: str

    def __init__(self, body):
        os.makedirs("chat", exist_ok=True)
        self.chat_dir = f"chat/{uuid4()}"
        self.prompt = messages_to_prompt(body)
        self.model_name = body.get("model", "gpt-3.5-turbo")
        os.mkdir(self.chat_dir)
        with open(f"{self.chat_dir}/request.json", "w") as file:
            file.write(json.dumps(body))
        with open(f"{self.chat_dir}/messages.txt", "w") as file:
            file.write(self.prompt)
        with open(f"{self.chat_dir}/reply.txt", "w") as file:
            file.write("")

    def stream_generate(self):
        with open(f"{self.chat_dir}/reply.txt", "r") as file:
            while True:
                text = file.read()
                if text:
                    break
                time.sleep(0.1)

        self.completion = text
        self.finish()

        for char in self.completion:
            time.sleep(0.01)
            yield char

    def generate(self):
        with open(f"{self.chat_dir}/reply.txt", "r") as file:
            while True:
                text = file.read()
                if text:
                    break
                time.sleep(0.1)

        self.completion = text
        self.finish()

        return self.completion

    def finish(self):
        shutil.rmtree(self.chat_dir)

    def token_count(self):
        prompt_tokens = num_tokens_from_string(self.prompt, self.model_name)
        completion_tokens = num_tokens_from_string(self.completion, self.model_name)
        total_tokens = prompt_tokens + completion_tokens
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
