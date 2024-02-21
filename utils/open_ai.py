# -*- coding: utf-8 -*-
import os
import json
import time
import filelock
import traceback
from openai import OpenAI
from utils.logger import logger
from types import TracebackType
from utils.common import get_conf
from utils.dirs import tmp_dir, lock_dir


class OpenAi:
    _instance = None

    def __new__(cls, *args, **kwargs) -> None:
        """
        Implement singleton mode.

        Returns:
            None
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, openai_conf_name: str = "open_ai") -> None:
        """
        Initialize an instance of the OpenAi class.

        Args:
            openai_conf_name (str): The name of the OpenAi configuration. Defaults to "open_ai".

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, "open_ai.lock")))
        self._openai_conf = get_conf(name=openai_conf_name)
        self._model = self._openai_conf.get("model")
        self._history = self._openai_conf.get("history")
        self._client = OpenAI(api_key=self._openai_conf.get("api_key"))
        self._contexts = []
        self._init_contexts()

    def __enter__(self) -> 'OpenAi':
        """
        Context manager method for entering the context.

        Returns:
            OpenAi: The current instance of the OpenAi class.
        """
        return self

    def __exit__(self, exc_type: type, exc_val: BaseException, exc_tb: TracebackType) -> None:
        """
        Context manager method for exiting the context.

        Args:
            exc_type (type): The type of the exception (if any) that occurred within the context.
            exc_val (BaseException): The exception object (if any) that occurred within the context.
            exc_tb (TracebackType): The traceback object (if any) associated with the exception.

        Returns:
            None
        """
        self._save_contexts()
        if exc_type:
            logger.error(f"an exception of type {exc_type} occurred: {exc_val}")

        if exc_tb:
            logger.error("".join(traceback.format_tb(exc_tb)))

    def _init_contexts(self) -> None:
        """
        Initialize dialogue contexts from file or create a new file if it doesn't exist.

        Returns:
            None
        """
        os.makedirs(tmp_dir, exist_ok=True)
        dialogue_contexts_path = os.path.abspath(os.path.join(tmp_dir, "dialogue_contexts.json"))
        if os.path.exists(dialogue_contexts_path):
            with open(dialogue_contexts_path, "r", encoding="utf-8") as f:
                self._contexts = json.load(f)
        else:
            with self._lock:
                with open(dialogue_contexts_path, "w", encoding="utf-8") as f:
                    json.dump(self._contexts, f, indent=4)

    def _save_contexts(self) -> None:
        """
        Save dialogue contexts to a JSON file.

        Returns:
            None
        """
        dialogue_contexts_path = os.path.abspath(os.path.join(tmp_dir, "dialogue_contexts.json"))
        with self._lock:
            with open(dialogue_contexts_path, "w", encoding="utf-8") as f:
                json.dump(self._contexts, f, indent=4)

    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response using OpenAI's model.

        Args:
            prompt (str): The prompt for generating the response.

        Returns:
            str: The text of response.
        """
        context = "\n".join(self._contexts[-self._history:])

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = completion.choices[0].message
        except Exception as e:
            logger.error(f"error: {e}")
            response_text = "failed to generate a response"

        self._contexts.append(f"Prompt: {prompt}, Answer: {response_text}.")

        logger.info(f"You:\n{prompt}")
        logger.info(f"Bot:\n{response_text}")

        return response_text

    def run(self):
        logger.info(f"started dialogue")
        logger.info(f"Model: {self._model}, History: {self._history}")
        try:
            while True:
                time.sleep(1)
                prompt = input("input your prompt:\n")
                response_text = self._generate_response(prompt)
                if response_text == "failed to generate a response":
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            logger.info("finished dialogue")


if __name__ == "__main__":
    with OpenAi() as instance:
        instance.run()
