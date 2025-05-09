"""
This module provides a `OllamaModelHandler` class for using Ollama pre-trained text generation models.

The `OllamaModelHandler` class simplifies the process of loading, initializing, and using
a text generation model from the `ollama` library. It provides methods
for preprocessing prompts, generating text, and maintaining a chat history.

The module also includes basic logging functionality to provide information about
the model's initialization and usage.

Example usage:
model_handler = ModelHandler("meta-llama/Llama-3.2-1B-Instruct")
output = model_handler.predict("What is the capital of France?")
"""

import logging
from pyexpat.errors import messages
from typing import Any, Optional
from collections import deque
from ollama import Client, ListResponse, ChatResponse

logger = logging.getLogger(__name__)


class OllamaModelHandler:
    """
    Handles interactions with the Ollama service.

    Args:
        model_name (str): The identifier of the pre-trained model to use.
        ollama_host (str): The host of the Ollama service.
        chat_kwargs (dict[str, Any]): Additional keyword arguments passed to the chat method.
        max_history_messages (int): The maximum number of messages to keep in the chat history.

    Methods:
        from_config(cfg): Creates a new instance of the OllamaModelHandler class from a configuration dictionary.
        get_available_model_names(): Returns a list of available Ollama models.
        get_current_model_name(): Returns the current Ollama model identifier.
        is_service_available(): Returns True if the Ollama service is available.
        is_model_available(model_name:str): Returns True if the Ollama model is available.
        set_model(model_name:str): Sets the model identifier to the given value.
        clear_history(): Clears the chat history.
        get_history(): Returns the chat history.
        predict(prompt_text: str): Generates text based on the prompt and chat history.
    """

    DEFAULT_MODEL: str = "llama3.2:1b"

    def __init__(
        self,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        chat_kwargs: Optional[dict[str, Any]] = None,
        max_history_messages: int = 10,
    ) -> None:
        """
        Initializes the ModelHandler with the specified model and parameters.

        Args:
            model_name (str): The identifier of the pre-trained model to use.
            ollama_host (str): The host of the Ollama service.
            chat_kwargs (dict[str, Any]): Additional keyword arguments passed to the chat method.
            max_history_messages (int): The maximum number of messages to keep in the chat history.
        """
        self._model_name: str = model_name
        self._is_model_initialized: bool = False
        self._client: Client = Client(host=ollama_host)
        self._chat_kwargs: dict = chat_kwargs or dict()
        self._chat_history: deque[dict[str, str]] = deque([], max_history_messages)

        if self.is_service_available():
            self._is_model_initialized = self._init_model()

    @classmethod
    def from_config(cls, model_config: dict[str, Any]) -> "OllamaModelHandler":
        """
        Creates a new instance of the OllamaModelHandler class from a configuration dictionary.

        Args:
            model_config: Configuration dictionary containing model settings.

        Returns:
            OllamaModelHandler: New instance configured with the provided settings.
        """
        config: dict[str, Any] = model_config.copy()
        return cls(**config)

    def _init_model(self) -> bool:
        if self.is_model_available(self._model_name):
            return True

        if self._model_name == self.DEFAULT_MODEL:
            return False

        logger.warning("Falling back to default model %s", self.DEFAULT_MODEL)
        if self.is_model_available(self.DEFAULT_MODEL):
            self._model_name = self.DEFAULT_MODEL
            return True

        return False

    def _get_available_models(self) -> ListResponse:
        """
        Retrieves available models from Ollama service.
        """
        return self._client.list()

    def get_available_model_names(self) -> list[str]:
        """
        Retrieves a list of available model names from Ollama service.

        Returns:
            list[str]: List of available model names.
        """
        available_models: ListResponse = self._get_available_models()
        available_model_names: list[str] = [model.model for model in available_models.models]
        return available_model_names

    def get_current_model_name(self) -> str:
        """
        Retrieves the name of the current model.

        Returns:
            str: The name of the current model.
        """
        return self._model_name

    def is_service_available(self) -> bool:
        """
        Check if the Ollama service is available.

        Returns:
            bool: True if the service is available, False otherwise.
        """
        try:
            _ = self._get_available_models()
        except ConnectionError as e:
            logger.error("Ollama connection error: %s", e)
            return False
        except Exception as e:
            logger.error("Ollama service is not available: %s", e)
            return False

        return True

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specified model is available."""
        available_model_names: list[str] = self.get_available_model_names()
        if model_name in available_model_names:
            logger.info("Model %s found in available models", model_name)
            return True

        logger.warning("Model %s not found, attempting to pull from repository", model_name)
        try:
            self._client.pull(model_name)
            logger.info("Model %s successfully pulled", model_name)
            return True
        except Exception as e:
            logger.error("Failed to pull model %s: %s", model_name, e)
            return False

    def set_model(self, model_name: str) -> bool:
        """Set the active model for chat responses generation."""
        if not self.is_model_available(model_name):
            return False

        self._model_name = model_name
        self._is_model_initialized = True
        logger.info("Model set to %s", model_name)
        return True

    def clear_history(self) -> None:
        """Clears the chat history."""
        self._chat_history.clear()
        logger.info("Chat history cleared.")

    @staticmethod
    def _preprocess_prompt(prompt_text: str) -> dict[str, str]:
        """
        Preprocesses the prompt and returns it as a dictionary.

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
        self._chat_history.append(prompt)
        logger.info("%s has been added to chat history.", prompt)

    def get_history(self) -> list[dict[str, str]]:
        allowed_keys: list[str] = ["role", "content"]
        message_history: list[dict[str, str]] = list(self._chat_history)
        message_history = [{k: v for k, v in msg.items() if k in allowed_keys} for msg in message_history]
        return message_history

    def predict(self, prompt_text: str) -> str:
        """
        Generates text based on the prompt and chat history.

        Args:
            prompt_text (str): The prompt text.

        Returns:
            str: The generated text.
        """
        if not self._is_model_initialized:
            self._init_model()

        prompt: dict[str, str] = self._preprocess_prompt(prompt_text)
        self._add_to_history(prompt)
        try:
            ollama_response: ChatResponse = self._client.chat(
                model=self._model_name,
                messages=list(self._chat_history),
                stream=False,
                **self._chat_kwargs,
            )

            logger.debug("Ollama response: %s", ollama_response)
            self._add_to_history(dict(ollama_response.message))
            return ollama_response.message.content
        except Exception as e:
            logger.error("Error during text generation: %s", e)
            return "Sorry, I encountered an error while processing your request."
