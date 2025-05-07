"""
This module provides a `ModelHandler` class for using pre-trained text generation models.

The `ModelHandler` class simplifies the process of loading, initializing, and using
a text generation model from the `transformers` library. It provides methods
for preprocessing prompts, generating text, and maintaining a chat history.

The module also includes basic logging functionality to provide information about
the model's initialization and usage.

Example usage:
model_handler = ModelHandler("meta-llama/Llama-3.2-1B-Instruct")
output = model_handler.predict("What is the capital of France?")
"""

import logging
import torch
from typing import Any
from transformers import pipeline

logger = logging.getLogger(__name__)


class ModelHandler:
    """
    Handles the loading, initialization, and usage of a text generation model.

    This class uses the `transformers` library to load and initialize a pre-trained
    text generation model. It provides methods for preprocessing prompts,
    generating text, and maintaining a chat history.

    Attributes:
        pipe (transformers.Pipeline): The text generation pipeline.
        chat_history (list): A list of previous interactions in the chat.
        max_history_messages (int): The maximum number of messages to keep in the chat history.

    Args:
        model_id (str): The identifier of the pre-trained model to use.
        device (str): The device to use for text generation. Defaults to None, which uses CUDA if available.
        max_history_messages (int): The maximum number of messages to keep in the chat history.
        model_params (dict[str, Any]): Additional parameters to pass to the model initialization function.

    Methods:
        from_config (cls, config): Creates a new instance of the ModelHandler class from a configuration dictionary.
        clear_history (self): Clears the chat history.
        _preprocess_prompt (prompt_text): Preprocesses the prompt and returns it as a dictionary.
        _add_to_history (self, prompt): Adds a prompt to the chat history.
        _menage_history_length (self): Manages the length of the chat history.
        predict (self, prompt_text): Generates text based on the prompt and chat history.

    """

    def __init__(
        self,
        model_id: str,
        device: str = None,
        max_history_messages: int = 10,
        model_params: dict[str, Any] = None,
    ) -> None:
        """
        Initializes the ModelHandler with the specified model and parameters.

        Args:
            model_id (str): The identifier of the pre-trained model to use.
            device (str): The device to use for text generation. Defaults to None, which uses CUDA if available.
            max_history_messages (int): The maximum number of messages to keep in the chat history.
            model_params (dict[str, Any]): Additional parameters to pass to the model initialization function.
        """
        logger.info("Initializing model %s.", model_id)
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        logger.info("Model will be initialized on %s.", device)
        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            device=device,
            **(model_params or dict()),
        )
        logger.info("Model %s has been initialized.", model_id)
        self.chat_history: list[dict[str, str]] = []
        self.max_history_messages: int = max_history_messages

    @classmethod
    def from_config(cls, model_config: dict[str, Any]) -> "ModelHandler":
        """Creates a new instance of the ModelHandler class from a configuration dictionary.

        Args:
            model_config: Configuration dictionary containing model settings.
                Must contain a 'model_id' key and may contain additional parameters.

        Returns:
            ModelHandler: New instance configured with the provided settings.

        Raises:
            KeyError: If a 'model_id' key is missing from the configuration.
        """
        config: dict[str, Any] = model_config.copy()

        if "model_id" not in config.keys():
            raise KeyError("Missing required 'model_id' key in configuration")

        model_id: str = config.pop("model_id")
        return cls(model_id, **config)

    def clear_history(self) -> None:
        """Clears the chat history."""
        self.chat_history = []
        logger.info("Chat history cleared.")

    @staticmethod
    def _preprocess_prompt(prompt_text: str) -> dict[str, str]:
        """Preprocesses the prompt and returns it as a dictionary.

        Args:
            prompt_text (str): The prompt text.

        Returns:
            dict: The preprocessed prompt as a dictionary containing the role and content keys
            ({'role': 'user', 'content': 'What is the capital of France?'}).
        """
        prompt: dict[str, str] = {"role": "user", "content": prompt_text}
        return prompt

    def _add_to_history(self, prompt: dict[str, str]) -> None:
        """
        Adds a prompt to the chat history.

        Args:
            prompt (dict): The prompt to be added to the chat history.

        """
        self.chat_history.append(prompt)
        logger.info("%s has been added to chat history.", prompt)

    def _manage_history_length(self) -> None:
        """Manages the length of the chat history."""
        if len(self.chat_history) > self.max_history_messages:
            while len(self.chat_history) > self.max_history_messages:
                message: dict = self.chat_history.pop(0)
                logger.info("Message %s deleted form the chat history.", message)
            logger.info("Chat history truncated to %s messages.", self.max_history_messages)
        logger.info("Chat history at %s / %s messages.", len(self.chat_history), self.max_history_messages)

    def predict(self, prompt_text: str) -> str:
        """
        Generates text based on the prompt and chat history.

        Args:
            prompt_text (str): The prompt text.

        Returns:
            str: The generated text.
        """
        prompt: dict[str, str] = self._preprocess_prompt(prompt_text)
        self._add_to_history(prompt)
        self._manage_history_length()
        try:
            output: dict[str, str] = self.pipe(self.chat_history)[0]["generated_text"][-1]
        except Exception as e:
            logger.error("Error during text generation: %s", e)
            return "Sorry, I encountered an error while processing your request."
        self.chat_history.append(output)
        logger.info("%s has been added to chat history.", output)
        return output["content"]
