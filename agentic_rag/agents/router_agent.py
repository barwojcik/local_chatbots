"""
Router agent that determines if RAG retrieval is needed for a query.

This agent analyzes user queries to decide whether they require external context
from documents or can be answered directly using the model's knowledge.
"""

import logging
import json
from typing import Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """
    Routes queries to appropriate processing paths based on content analysis.

    The RouterAgent determines if a user query requires document retrieval (RAG)
    or can be answered directly. It analyzes the query's nature and returns a
    routing decision with confidence score.

    Args:
        model_name (str, optional): The identifier of the Ollama model to use.
        ollama_host (str, optional): The host of the Ollama service.
        confidence_threshold (float, optional): Threshold for routing decision (0-1). Default: 0.7.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Analyzes query and returns routing decision.
    """

    DEFAULT_SYSTEM_PROMPT = """You are a routing agent that determines if a user query requires external document retrieval.

    Analyze the query and respond with a JSON object containing:
    - "needs_retrieval": boolean indicating if document retrieval is needed
    - "confidence": float between 0 and 1 indicating confidence in the decision
    - "reasoning": brief explanation of the decision
    
    Query types that NEED retrieval:
    - Questions about specific documents, papers, or uploaded content
    - Requests for information that requires domain-specific knowledge
    - Questions about data, statistics, or facts not in common knowledge
    - Queries referencing "the document", "the file", "uploaded content", etc.
    
    Query types that DON'T need retrieval:
    - General knowledge questions
    - Casual conversation and greetings
    - Requests for explanations of common concepts
    - Math calculations or logic problems
    - Programming help with common languages/frameworks
    
    Respond ONLY with valid JSON, no additional text."""

    def __init__(
        self,
        model_handler=None,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        confidence_threshold: float = 0.7,
        system_prompt: Optional[str] = None,
        chat_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the RouterAgent with specified parameters.

        Args:
            model_handler: Instance of OllamaModelHandler to use.
            model_name: The identifier of the Ollama model to use (if model_handler not provided).
            ollama_host: The host of the Ollama service (if model_handler not provided).
            confidence_threshold: Threshold for routing decision (0-1).
            system_prompt: Custom system prompt (uses default if None).
            chat_kwargs: Additional keyword arguments for chat (if model_handler not provided).
        """
        super().__init__(
            model_handler=model_handler,
            model_name=model_name,
            ollama_host=ollama_host,
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            chat_kwargs=chat_kwargs,
        )
        self._confidence_threshold = confidence_threshold

    def execute(self, query: str, has_documents: bool = True) -> dict[str, Any]:
        """
        Analyzes query and determines if RAG retrieval is needed.

        Args:
            query: The user's query string.
            has_documents: Whether documents are available in the vector store.

        Returns:
            dict containing:
                - needs_retrieval (bool): Whether to use RAG
                - confidence (float): Confidence in decision
                - reasoning (str): Explanation of decision
        """
        logger.info("RouterAgent analyzing query: %s", query)

        # If no documents are available, skip retrieval
        if not has_documents:
            logger.info("No documents in vector store, skipping retrieval")
            return {
                "needs_retrieval": False,
                "confidence": 1.0,
                "reasoning": "No documents available in vector store",
            }

        try:
            # Build messages for routing decision
            messages = self._build_messages(query)

            # Get model response
            response = self._call_model(messages)

            # Parse JSON response
            try:
                result = json.loads(response)

                # Validate response structure
                if not all(key in result for key in ["needs_retrieval", "confidence", "reasoning"]):
                    raise ValueError("Missing required keys in router response")

                # Apply confidence threshold
                if result["confidence"] < self._confidence_threshold:
                    logger.warning(
                        "Router confidence %.2f below threshold %.2f",
                        result["confidence"],
                        self._confidence_threshold,
                    )

                logger.info(
                    "Routing decision: needs_retrieval=%s, confidence=%.2f, reasoning=%s",
                    result["needs_retrieval"],
                    result["confidence"],
                    result["reasoning"],
                )

                return result

            except (json.JSONDecodeError, ValueError) as e:
                logger.error("Failed to parse router response: %s. Response: %s", e, response)
                # Default to using retrieval if parsing fails
                return {
                    "needs_retrieval": True,
                    "confidence": 0.5,
                    "reasoning": "Failed to parse routing decision, defaulting to retrieval",
                }

        except Exception as e:
            logger.error("Error in RouterAgent: %s", e)
            # Default to using retrieval on error
            return {
                "needs_retrieval": True,
                "confidence": 0.5,
                "reasoning": f"Error in routing: {str(e)}",
            }
