"""
Retriever agent that executes document retrieval with multiple strategies.

This agent coordinates different retrieval strategies, ranks results,
and returns the most relevant document chunks with metadata.
"""

import logging
from typing import Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RetrieverAgent(BaseAgent):
    """
    Coordinates document retrieval using multiple strategies.

    The RetrieverAgent manages the retrieval process, combining results from
    different search strategies and ranking them by relevance.

    Args:
        model_name (str, optional): The identifier of the Ollama model to use (for re-ranking).
        ollama_host (str, optional): The host of the Ollama service.
        strategies (list[str], optional): List of retrieval strategies to use. Default: ["semantic"].
        enable_reranking (bool, optional): Whether to re-rank retrieved documents. Default: True.
        max_results (int, optional): Maximum number of results to return. Default: 5.
        chat_kwargs (dict[str, Any], optional): Additional keyword arguments for chat.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        execute: Retrieves relevant documents for the query.
        set_vector_store: Sets the vector store handler for retrieval.
    """

    DEFAULT_RERANK_PROMPT = """You are a document relevance scorer. Given a query and a document chunk, rate the relevance on a scale of 0-10.

    Query: {query}
    
    Document chunk: {chunk}
    
    Consider:
    - Direct answer to query
    - Contextual relevance
    - Information completeness
    
    Respond with ONLY a single number between 0-10, no other text."""

    def __init__(
        self,
        model_handler=None,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        strategies: Optional[list[str]] = None,
        enable_reranking: bool = True,
        max_results: int = 5,
        system_prompt: Optional[str] = None,
        chat_kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the RetrieverAgent with specified parameters.

        Args:
            model_handler: Instance of OllamaModelHandler to use.
            model_name: The identifier of the Ollama model to use (if model_handler not provided).
            ollama_host: The host of the Ollama service (if model_handler not provided).
            strategies: List of retrieval strategies to use.
            enable_reranking: Whether to re-rank retrieved documents.
            max_results: Maximum number of results to return.
            system_prompt: Custom system prompt (uses default if None).
            chat_kwargs: Additional keyword arguments for chat (if model_handler not provided).
        """
        super().__init__(
            model_handler=model_handler,
            model_name=model_name,
            ollama_host=ollama_host,
            system_prompt=system_prompt,
            chat_kwargs=chat_kwargs,
        )
        self._strategies = strategies or ["semantic"]
        self._enable_reranking = enable_reranking
        self._max_results = max_results
        self._vector_store = None

    def set_vector_store(self, vector_store) -> None:
        """
        Sets the vector store handler for retrieval.

        Args:
            vector_store: VectorStoreHandler instance.
        """
        self._vector_store = vector_store

    def _rerank_documents(
        self, query: str, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Re-ranks documents based on relevance to query.

        Args:
            query: The search query.
            documents: List of document dictionaries with content and metadata.

        Returns:
            list[dict[str, Any]]: Re-ranked list of documents with scores.
        """
        if not self._enable_reranking or not documents:
            return documents

        logger.info("Re-ranking %d documents for query: %s", len(documents), query)

        scored_docs = []
        for doc in documents:
            try:
                # Build re-ranking prompt
                prompt = self.DEFAULT_RERANK_PROMPT.format(
                    query=query,
                    chunk=doc.get("content", ""),
                )

                messages = [{"role": "user", "content": prompt}]
                response = self._call_model(messages)

                # Parse score
                try:
                    score = float(response.strip())
                    score = max(0.0, min(10.0, score))  # Clamp to 0-10
                except ValueError:
                    logger.warning("Failed to parse rerank score: %s", response)
                    score = 5.0  # Default middle score

                doc["rerank_score"] = score
                scored_docs.append(doc)

            except Exception as e:
                logger.error("Error re-ranking document: %s", e)
                doc["rerank_score"] = 5.0
                scored_docs.append(doc)

        # Sort by rerank score
        scored_docs.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        logger.info("Re-ranking complete. Top score: %.2f", scored_docs[0].get("rerank_score", 0))

        return scored_docs

    def execute(
        self, query: str, query_analysis: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieves relevant documents for the query.

        Args:
            query: The search query string.
            query_analysis: Optional query analysis results from QueryAnalyzerAgent.

        Returns:
            list[dict[str, Any]]: List of retrieved documents with metadata:
                - content (str): Document chunk text
                - metadata (dict): Document metadata
                - score (float): Retrieval score
                - rerank_score (float): Re-ranking score (if enabled)
        """
        if not self._vector_store:
            logger.error("Vector store not set for RetrieverAgent")
            return []

        logger.info("RetrieverAgent retrieving documents for query: %s", query)

        # Use enhanced query if available
        search_query = query
        if query_analysis and "enhanced_query" in query_analysis:
            search_query = query_analysis["enhanced_query"]
            logger.info("Using enhanced query: %s", search_query)

        try:
            # Retrieve documents using configured strategies
            all_documents = []

            for strategy in self._strategies:
                if strategy == "semantic":
                    # Semantic search via vector store
                    results = self._vector_store.get_context_with_metadata(
                        search_query,
                        k=self._max_results * 2,  # Get more for re-ranking
                    )
                    all_documents.extend(results)

                elif strategy == "hybrid":
                    # Hybrid search (semantic + keyword)
                    results = self._vector_store.hybrid_search(
                        search_query,
                        k=self._max_results * 2,
                    )
                    all_documents.extend(results)

                else:
                    logger.warning("Unknown retrieval strategy: %s", strategy)

            # Also search with query variations if available
            if query_analysis and query_analysis.get("query_variations"):
                for variation in query_analysis["query_variations"][:2]:  # Limit variations
                    results = self._vector_store.get_context_with_metadata(
                        variation,
                        k=self._max_results,
                    )
                    all_documents.extend(results)

            # Remove duplicates based on content
            unique_docs = []
            seen_contents = set()
            for doc in all_documents:
                content = doc.get("content", "")
                if content and content not in seen_contents:
                    seen_contents.add(content)
                    unique_docs.append(doc)

            logger.info("Retrieved %d unique documents", len(unique_docs))

            # Re-rank documents if enabled
            if self._enable_reranking:
                unique_docs = self._rerank_documents(query, unique_docs)

            # Return top results
            final_results = unique_docs[: self._max_results]

            logger.info("Returning %d documents after retrieval and ranking", len(final_results))

            return final_results

        except Exception as e:
            logger.error("Error in RetrieverAgent: %s", e)
            return []
