"""
Synthesizer agent that generates coherent responses from retrieved context.

This agent combines retrieved document chunks with the user's query to generate
accurate, well-sourced responses with optional citations.
"""

import logging
from typing import Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SynthesizerAgent(BaseAgent):
    """
    Synthesizes responses from retrieved documents and user queries.

    The SynthesizerAgent generates coherent answers by combining context from
    multiple document sources, maintaining accuracy and providing citations.

    Args:
        model_name (str, optional): The identifier of the Ollama model to use.
        ollama_host (str, optional): The host of the Ollama service.
        include_citations (bool, optional): Whether to include citations. Default: True.
        max_context_chunks (int, optional): Maximum context chunks to use. Default: 5.
        chat_history (list, optional): Chat history for context-aware responses.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Generates response from query and retrieved documents.
        set_chat_history: Sets the chat history for context-aware responses.
    """

    DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

    Guidelines:
    1. Answer based primarily on the provided context
    2. If the context doesn't contain enough information, acknowledge this
    3. Be accurate and precise
    4. Include relevant details from the context
    5. Maintain a helpful and professional tone
    6. If asked to cite sources, reference the document chunks provided
    
    If the context is insufficient, you may use your general knowledge but clearly indicate when you're doing so."""

    CITATION_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

    Guidelines:
    1. Answer based primarily on the provided context
    2. Include citations in the format [Source N] after statements from specific chunks
    3. If the context doesn't contain enough information, acknowledge this
    4. Be accurate and precise
    5. Include relevant details from the context
    6. Maintain a helpful and professional tone
    
    At the end of your response, list the sources used:
    ---
    Sources:
    [Source 1] Brief description of the document chunk
    [Source 2] Brief description of the document chunk
    ..."""

    def __init__(
        self,
        model_handler=None,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        include_citations: bool = True,
        max_context_chunks: int = 5,
        system_prompt: Optional[str] = None,
        chat_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the SynthesizerAgent with specified parameters.

        Args:
            model_handler: Instance of OllamaModelHandler to use.
            model_name: The identifier of the Ollama model to use (if model_handler not provided).
            ollama_host: The host of the Ollama service (if model_handler not provided).
            include_citations: Whether to include citations in responses.
            max_context_chunks: Maximum number of context chunks to use.
            system_prompt: Custom system prompt (uses default if None).
            chat_kwargs: Additional keyword arguments for chat (if model_handler not provided).
        """
        # Choose system prompt based on citation preference
        if system_prompt is None:
            system_prompt = (
                self.CITATION_SYSTEM_PROMPT if include_citations else self.DEFAULT_SYSTEM_PROMPT
            )

        super().__init__(
            model_handler=model_handler,
            model_name=model_name,
            ollama_host=ollama_host,
            system_prompt=system_prompt,
            chat_kwargs=chat_kwargs,
        )
        self._include_citations = include_citations
        self._max_context_chunks = max_context_chunks
        self._chat_history = []

    def set_chat_history(self, chat_history: list[dict[str, str]]) -> None:
        """
        Sets the chat history for context-aware responses.

        Args:
            chat_history: List of message dictionaries with 'role' and 'content'.
        """
        self._chat_history = chat_history

    def _format_context(self, documents: list[dict[str, Any]]) -> str:
        """
        Formats retrieved documents into a context string.

        Args:
            documents: List of document dictionaries with content and metadata.

        Returns:
            str: Formatted context string.
        """
        if not documents:
            return "No context available."

        context_parts = []
        for idx, doc in enumerate(documents[: self._max_context_chunks], 1):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Format with source number for citation
            if self._include_citations:
                source_info = []
                if "source" in metadata:
                    source_info.append(f"File: {metadata['source']}")
                if "page" in metadata:
                    source_info.append(f"Page: {metadata['page']}")

                source_str = ", ".join(source_info) if source_info else "Unknown source"
                context_parts.append(f"[Source {idx}] ({source_str})\n{content}")
            else:
                context_parts.append(content)

        return "\n\n---\n\n".join(context_parts)

    def execute(
        self,
        query: str,
        retrieved_documents: list[dict[str, Any]],
        chat_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Generates a response based on the query and retrieved documents.

        Args:
            query: The user's query string.
            retrieved_documents: List of retrieved document dictionaries.
            chat_history: Optional chat history for context-aware responses.

        Returns:
            str: Generated response.
        """
        logger.info("SynthesizerAgent generating response for query: %s", query)

        if chat_history is not None:
            self._chat_history = chat_history

        try:
            # Format context from retrieved documents
            context = self._format_context(retrieved_documents)

            # Build prompt with context
            user_prompt = f"""Context from documents:
            {context}
            
            ---
            
            User question: {query}
            
            Please answer the question based on the context provided above."""

            # Build messages with chat history
            messages = []

            # Add system prompt
            if self._system_prompt:
                messages.append({"role": "system", "content": self._system_prompt})

            # Add chat history (excluding system messages)
            for msg in self._chat_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)

            # Add current query with context
            messages.append({"role": "user", "content": user_prompt})

            # Generate response
            response = self._call_model(messages)

            logger.info("Response generated successfully")

            return response

        except Exception as e:
            logger.error("Error in SynthesizerAgent: %s", e)
            return "I apologize, but I encountered an error while generating a response."

    def execute_without_context(
        self,
        query: str,
        chat_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Generates a response without retrieved context (for queries that don't need RAG).

        Args:
            query: The user's query string.
            chat_history: Optional chat history for context-aware responses.

        Returns:
            str: Generated response.
        """
        logger.info("SynthesizerAgent generating response without context for query: %s", query)

        if chat_history is not None:
            self._chat_history = chat_history

        try:
            # Build messages with chat history
            messages = []

            # Add simplified system prompt for non-RAG queries
            messages.append(
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer questions clearly and concisely.",
                }
            )

            # Add chat history (excluding system messages)
            for msg in self._chat_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)

            # Add current query
            messages.append({"role": "user", "content": query})

            # Generate response
            response = self._call_model(messages)

            logger.info("Response generated successfully without context")

            return response

        except Exception as e:
            logger.error("Error in SynthesizerAgent: %s", e)
            return "I apologize, but I encountered an error while generating a response."
