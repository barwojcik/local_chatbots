"""
Query analyzer agent that enhances and reformulates queries for better retrieval.

This agent improves query quality by expanding terms, identifying key concepts,
and generating multiple query variations for comprehensive document retrieval.
"""

import json
import logging
from typing import Any

from model import OllamaModelHandler

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QueryAnalyzerAgent(BaseAgent):
    """
    Analyzes and enhances user queries for improved document retrieval.

    The QueryAnalyzerAgent reformulates queries, extracts key concepts, and
    generates alternative phrasings to maximize retrieval effectiveness.

    Args:
        model_name (str, optional): The identifier of the Ollama model to use.
        ollama_host (str, optional): The host of the Ollama service.
        generate_variations (bool, optional): Whether to generate query variations. Default: True.
        max_variations (int, optional): Maximum number of query variations. Default: 3.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Analyzes query and returns enhanced query information.
    """

    DEFAULT_SYSTEM_PROMPT = """
    You are a query analysis agent that enhances queries for document retrieval.

    Analyze the query and respond with a JSON object containing:
    - "enhanced_query": improved version of the original query
    - "key_concepts": list of important keywords/concepts
    - "query_variations": list of alternative phrasings (if requested)
    - "query_type": type of query (factual, analytical, procedural, conceptual)

    Guidelines for enhancement:
    1. Expand abbreviations and acronyms
    2. Add relevant synonyms
    3. Clarify ambiguous terms
    4. Maintain the original intent
    5. Keep queries concise but complete

    Respond ONLY with valid JSON, no additional text."""

    def __init__(
        self,
        model_handler: OllamaModelHandler | None = None,
        model_name: str | None = None,
        ollama_host: str | None = None,
        generate_variations: bool = True,
        max_variations: int = 3,
        system_prompt: str | None = None,
        chat_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Initializes the QueryAnalyzerAgent with specified parameters.

        Args:
            model_handler: Instance of OllamaModelHandler to use.
            model_name: The identifier of the Ollama model to use (if model_handler not provided).
            ollama_host: The host of the Ollama service (if model_handler not provided).
            generate_variations: Whether to generate query variations.
            max_variations: Maximum number of query variations.
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
        self._generate_variations = generate_variations
        self._max_variations = max_variations

    def execute(self, query: str) -> dict[str, Any]:
        """
        Analyzes and enhances the user query.

        Args:
            query: The original user query string.

        Returns:
            dict containing:
                - enhanced_query (str): Improved version of the query
                - key_concepts (list[str]): Important keywords/concepts
                - query_variations (list[str]): Alternative phrasings
                - query_type (str): Type classification
                - original_query (str): The original query for reference
        """
        logger.info("QueryAnalyzerAgent analyzing query: %s", query)

        try:
            # Build prompt with variation instructions
            user_prompt = query
            if self._generate_variations:
                user_prompt += f"\n\nGenerate up to {self._max_variations} query variations."

            messages = self._build_messages(user_prompt)

            # Get model response
            response = self._call_model(messages)

            # Parse JSON response
            try:
                result = json.loads(response)

                # Validate response structure
                required_keys = ["enhanced_query", "key_concepts", "query_type"]
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required keys in query analysis response")

                # Ensure query_variations exists
                if "query_variations" not in result:
                    result["query_variations"] = []

                # Add original query for reference
                result["original_query"] = query

                logger.info(
                    "Query analysis complete: enhanced=%s, concepts=%s, type=%s",
                    result["enhanced_query"],
                    result["key_concepts"],
                    result["query_type"],
                )

                return result

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(
                    "Failed to parse query analysis response: %s. Response: %s", e, response
                )
                # Return basic analysis if parsing fails
                return {
                    "enhanced_query": query,
                    "key_concepts": query.split(),
                    "query_variations": [],
                    "query_type": "unknown",
                    "original_query": query,
                }

        except Exception as e:
            logger.error("Error in QueryAnalyzerAgent: %s", e)
            # Return original query on error
            return {
                "enhanced_query": query,
                "key_concepts": query.split(),
                "query_variations": [],
                "query_type": "unknown",
                "original_query": query,
            }
