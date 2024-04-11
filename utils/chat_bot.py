# -*- coding: utf-8 -*-
import os
import sys
import time
import filelock
import traceback
from openai import OpenAI
from utils.logger import logger
from types import TracebackType
from utils.dirs import tmp_dir, lock_dir
from utils.common import get_ext_conf, dump_json, load_json


class ChatBot:
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

    def __init__(self, conf_name: str = "chat_bot") -> None:
        """
        Initialize an instance of the ChatBot class.

        Args:
            conf_name (str): The name of the configuration. Defaults to "chat_bot".

        Returns:
            None
        """
        self._lock = filelock.FileLock(os.path.abspath(os.path.join(lock_dir, "chat_bot.lock")))
        self._conf = get_ext_conf(name=conf_name)
        self._model = self._conf.get("model")
        self._history = self._conf.get("history")
        self._client = OpenAI(api_key=self._conf.get("api_key"), base_url=self._conf.get("base_url"))
        self._contexts = []
        self._init_contexts()

    def __enter__(self) -> 'ChatBot':
        """
        Context manager method for entering the context.

        Returns:
            ChatBot: The current instance of the ChatBot class.
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
        if exc_type:
            logger.error(f"""{exc_val}\n{"".join(traceback.format_tb(exc_tb))}""")

        self._save_contexts()

    def _init_contexts(self) -> None:
        """
        Initialize dialogue contexts from file or create a new file if it does not exist.

        Returns:
            None
        """
        os.makedirs(tmp_dir, exist_ok=True)
        dialogue_contexts_path = os.path.abspath(os.path.join(tmp_dir, "dialogue_contexts.json"))
        if os.path.exists(dialogue_contexts_path):
            try:
                self._contexts = load_json(dialogue_contexts_path)
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)
        else:
            with self._lock:
                try:
                    dump_json(dialogue_contexts_path, self._contexts)
                except Exception as e:
                    logger.error(f"{e}\n{traceback.format_exc()}")
                    sys.exit(1)

    def _save_contexts(self) -> None:
        """
        Save dialogue contexts to a json file.

        Returns:
            None
        """
        dialogue_contexts_path = os.path.abspath(os.path.join(tmp_dir, "dialogue_contexts.json"))
        with self._lock:
            try:
                dump_json(dialogue_contexts_path, self._contexts)
            except Exception as e:
                logger.error(f"{e}\n{traceback.format_exc()}")
                sys.exit(1)

    def _generate_response(self, prompt: str) -> None:
        """
        Generate a response using OpenAI model.

        Args:
            prompt (str): The prompt for generating the response.

        Returns:
            None
        """
        context = [{"role": "system", "content": "You are a helpful assistant."}]
        context.extend(self._contexts[-self._history * 2:])
        context.append({"role": "user", "content": prompt})

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=context
            )
            response_text = completion.choices[0].message.content
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            raise KeyboardInterrupt
        else:
            self._contexts.extend([{"role": "user", "content": prompt},
                                   {"role": "assistant", "content": response_text}])

        print(f"Bot:\n{response_text}")

    def run(self) -> None:
        """
        Execute dialogue and generate response based on user prompt.

        Returns:
            None
        """
        if not self._model:
            logger.error("model is empty")
            return

        logger.info(f"started dialogue")
        logger.info(f"model: {self._model}, history: {self._history}")
        try:
            while True:
                time.sleep(1)
                prompt = input("You:\n")
                self._generate_response(prompt)
        except KeyboardInterrupt:
            logger.info("finished dialogue")


if __name__ == "__main__":
    with ChatBot() as instance:
        instance.run()
