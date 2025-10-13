"""
Base agent class for all agents in the multi-agent system.

This module provides the BaseAgent abstract class that defines the common interface
and functionality for all specialized agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from ollama import Client, ChatResponse

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    Args:
        model_name (str): The identifier of the Ollama model to use.
        ollama_host (str, optional): The host of the Ollama service.
        system_prompt (str, optional): System prompt to guide agent behavior.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Abstract method that each agent must implement.
    """

    DEFAULT_MODEL: str = "llama3.2:3b"

    def __init__(
        self,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        system_prompt: Optional[str] = None,
        chat_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the BaseAgent with the specified model and parameters.

        Args:
            model_name: The identifier of the Ollama model to use.
            ollama_host: The host of the Ollama service.
            system_prompt: System prompt to guide agent behavior.
            chat_kwargs: Additional keyword arguments for chat.
        """
        self._model_name: str = model_name or self.DEFAULT_MODEL
        self._client: Client = Client(host=ollama_host)
        self._system_prompt: Optional[str] = system_prompt
        self._chat_kwargs: dict[str, Any] = chat_kwargs or {}

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
            response: ChatResponse = self._client.chat(
                model=self._model_name,
                messages=messages,
                stream=False,
                **self._chat_kwargs,
            )
            logger.debug("Agent %s received response: %s", self.__class__.__name__, response)
            return response.message.content
        except Exception as e:
            logger.error("Error in agent %s: %s", self.__class__.__name__, e)
            raise

    def _build_messages(
        self, user_content: str, context: Optional[dict[str, Any]] = None
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
    def execute(self, *args, **kwargs) -> Any:
        """
        Abstract method that each agent must implement.

        This method defines the specific behavior of the agent.
        """
        pass
