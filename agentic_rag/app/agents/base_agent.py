"""
Base agent class for all agents in the multi-agent system.

This module provides the BaseAgent abstract class that defines the common interface
and functionality for all specialized agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from model import OllamaModelHandler

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    Args:
        model_handler (OllamaModelHandler, optional): Instance of OllamaModelHandler to use.
        model_name (str, optional): The identifier of the Ollama model to use (if model_handler
            not provided).
        ollama_host (str, optional): The host of the Ollama service (if model_handler not provided).
        system_prompt (str, optional): System prompt to guide agent behavior.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat (if
            model_handler not provided).

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Abstract method that each agent must implement.
    """

    DEFAULT_MODEL: str = "llama3.2:3b"

    def __init__(
        self,
        model_handler: OllamaModelHandler | None = None,
        model_name: str | None = None,
        ollama_host: str | None = None,
        system_prompt: str | None = None,
        chat_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Initializes the BaseAgent with the specified model and parameters.

        Args:
            model_handler: Instance of OllamaModelHandler to use.
            model_name: The identifier of the Ollama model to use (if model_handler not provided).
            ollama_host: The host of the Ollama service (if model_handler not provided).
            system_prompt: System prompt to guide agent behavior.
            chat_kwargs: Additional keyword arguments for chat (if model_handler not provided).
        """
        if model_handler is not None:
            self._model_handler = model_handler
        else:
            self._model_handler = OllamaModelHandler(
                model_name=model_name or self.DEFAULT_MODEL,
                ollama_host=ollama_host,
                chat_kwargs=chat_kwargs,
            )
        self._system_prompt: str | None = system_prompt

    @classmethod
    def from_config(cls, agent_config: dict[str, Any]) -> "BaseAgent":
        """
        Creates a new instance of the agent from a configuration dictionary.

        Args:
            agent_config: Configuration dictionary containing agent settings.

        Returns:
            BaseAgent: New instance configured with the provided settings.
        """
        config: dict[str, Any] = agent_config.copy()
        return cls(**config)

    def _call_model(self, messages: list[dict[str, str]]) -> str:
        """
        Calls the Ollama model with the provided messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.

        Returns:
            str: The model's response content.
        """
        try:
            response = self._model_handler.predict(messages)
            logger.debug("Agent %s received response: %s", self.__class__.__name__, response)
            return response
        except Exception as e:
            logger.error("Error in agent %s: %s", self.__class__.__name__, e)
            raise

    def _build_messages(
        self, user_content: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, str]]:
        """
        Builds the messages list for the model call.

        Args:
            user_content: The user's message content.
            context: Optional context dictionary for additional information.

        Returns:
            list[dict[str, str]]: List of formatted messages.
        """
        messages = []

        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        messages.append({"role": "user", "content": user_content})

        return messages

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Abstract method that each agent must implement.

        This method defines the specific behavior of the agent.
        """
        pass
