"""
This module provides a `VectorStoreHandler` class for managing and querying a vector store.

The `VectorStoreHandler` class facilitates the process of loading, chunking, embedding, and storing
documents within a vector store, primarily for semantic search and retrieval of relevant information.

It leverages the LlamaIndex and Ollama ecosystems to provide a streamlined workflow for handling document
processing and similarity search.

Example usage:
from your_module import VectorStoreHandler

handler = VectorStoreHandler()
handler.process_documents(["path/to/your_document.pdf"])
context = handler.get_context("your search query")
print(context) # Output: List of relevant text chunks

"""

import logging
from typing import Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class VectorStoreHandler:
    """
    Handles the loading, chunking, embedding, and querying of documents within a vector store.

    This class uses LangChain for document loading and chunking, Ollama for embeddings,
    and Chroma as the vector database.

    Args:
        embeddings_model (str, optional): The identifier of the Ollama embeddings model. Default "llama3.2:1b".
        ollama_host (str, optional): The hostname of the Ollama.
        model_kwargs (dict[str, Any], optional): Additional keyword arguments to pass to the embedding model.
        splitter_params (dict[str, Any], optional): Additional parameters for the text splitter.
        query_params (dict[str, Any], optional): Additional parameters for the similarity search query.

    Methods:
        clean_chunks(chunks): Removes newlines from text chunks.
        process_documents(document_paths): Loads, chunks, embeds, and stores documents in the vector store.
        get_context(query): Retrieves relevant context from the vector store based on a query.
        reset(): Resets the vector store by deleting the content of the collection.
    """

    DEFAULT_MODEL: str = "llama3.2:1b"

    def __init__(
        self,
        embeddings_model: Optional[str] = None,
        ollama_host: Optional[str] = None,
        model_kwargs: dict[str, Any] = None,
        splitter_params: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
        document_processor_config: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the VectorStoreHandler with the specified model and parameters.

        Args:
            embeddings_model (str, optional): The identifier of the Hugging Face embeddings model.
                Defaults to "sentence-transformers/all-MiniLM-L6-v2".
            model_kwargs (dict[str, Any], optional): Additional keyword arguments to pass to the embedding model.
            splitter_params (dict[str, Any], optional): Additional parameters for the text splitter.
            query_params (dict[str, Any], optional): Additional parameters for the similarity search query.
            document_processor_config (dict[str, Any], optional): Configuration for document processor.
        """
        logger.info("Initializing vector store...")
        model_kwargs = model_kwargs or dict()
        self._embeddings: OllamaEmbeddings = OllamaEmbeddings(
            model=(embeddings_model or self.DEFAULT_MODEL),
            base_url=ollama_host,
            **model_kwargs,
        )
        logger.info("Embeddings model %s has been initialized.", embeddings_model)
        self.vector_store: Chroma = Chroma(embedding_function=self._embeddings)
        logger.info("Vector store has been initialized.")
        self._splitter_params: dict[str, Any] = splitter_params or dict()
        self._query_params: dict[str, Any] = query_params or dict()

        # Initialize document processor
        if document_processor_config:
            self._document_processor = DocumentProcessor.from_config(document_processor_config)
        else:
            # Use splitter_params for backward compatibility
            self._document_processor = DocumentProcessor(
                chunking_strategy="semantic",
                chunk_size=self._splitter_params.get("chunk_size", 1024),
                chunk_overlap=self._splitter_params.get("chunk_overlap", 128),
            )

    @classmethod
    def from_config(cls, vector_store_config: dict[str, str]) -> "VectorStoreHandler":
        """
        Creates a new instance of the VectorStoreHandler class from a configuration dictionary.

        Args:
            vector_store_config (dict[str, str]): A dictionary containing the configuration parameters for
                the vector store.

        Returns:
            VectorStoreHandler: A new instance of the VectorStoreHandler class initialized with the provided
                configuration.
        """
        config: dict[str, Any] = vector_store_config.copy()
        return cls(**config)

    def _process_document(self, document_path: str, doc_index: int = 0) -> None:
        """
        Loads, chunks, embeds, and stores a document in the vector store.

        Args:
            document_path (str): The path to the document to be processed.
            doc_index (int): Index of the document for tracking.
        """
        logger.info("Processing %s with enhanced document processor.", document_path)

        # Use document processor to chunk and extract metadata
        chunks: list[Document] = self._document_processor.process_document(document_path, doc_index)

        # Add to vector store
        self.vector_store.add_documents(chunks)
        logger.info(
            "Vector store has been populated from %s with %d chunks.", document_path, len(chunks)
        )

    def process_documents(self, document_paths: list[str] | str) -> None:
        """
        Loads, chunks, embeds, and stores documents in the vector store.

        Args:
            document_paths (list[str] | str): The path or list of paths to the documents to be processed.
        """
        if isinstance(document_paths, str):
            document_paths = [document_paths]

        for idx, document_path in enumerate(document_paths):
            self._process_document(document_path, doc_index=idx)

    def get_context(self, query: str) -> list[str]:
        """
        Retrieves relevant context from the vector store based on a query.

        Args:
            query (str): The search query.

        Returns:
            context (list[str]): A list of relevant text chunks from the stored documents.
        """
        documents: list[Document] = self.vector_store.similarity_search(query, **self._query_params)
        context: list[str] = [doc.page_content for doc in documents]
        logger.info("Query %s returned %s", query, context)
        return context

    def get_context_with_metadata(
        self, query: str, k: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieves relevant context with metadata from the vector store.

        Args:
            query: The search query.
            k: Number of results to return (overrides default query_params).

        Returns:
            list[dict[str, Any]]: List of documents with content and metadata.
        """
        query_params = self._query_params.copy()
        if k is not None:
            query_params["k"] = k

        documents: list[Document] = self.vector_store.similarity_search(query, **query_params)

        results = []
        for doc in documents:
            results.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
            )

        logger.info("Query '%s' returned %d documents with metadata", query, len(results))
        return results

    def hybrid_search(self, query: str, k: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Performs hybrid search combining semantic and keyword-based retrieval.

        Args:
            query: The search query.
            k: Number of results to return.

        Returns:
            list[dict[str, Any]]: List of documents with content and metadata.
        """
        k_value = k if k is not None else self._query_params.get("k", 5)

        # Semantic search
        semantic_results = self.get_context_with_metadata(query, k=k_value * 2)

        # Keyword-based filtering (simple implementation)
        # Extract keywords from query
        keywords = [word.lower() for word in query.split() if len(word) > 3]

        # Score results based on keyword presence
        for result in semantic_results:
            content_lower = result["content"].lower()
            keyword_score = sum(1 for kw in keywords if kw in content_lower)
            result["keyword_score"] = keyword_score

        # Sort by keyword score (keeping semantic order as secondary)
        semantic_results.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)

        # Return top k results
        final_results = semantic_results[:k_value]

        logger.info("Hybrid search for '%s' returned %d documents", query, len(final_results))
        return final_results

    def has_documents(self) -> bool:
        """
        Checks if the vector store contains any documents.

        Returns:
            bool: True if documents exist, False otherwise.
        """
        try:
            id_list = self.vector_store.get()["ids"]
            return len(id_list) > 0
        except Exception as e:
            logger.error("Error checking for documents: %s", e)
            return False

    def reset(self):
        """Resets the vector store by deleting the content of the collection."""
        # Get the list of ids in the collection
        id_list = self.vector_store.get()["ids"]
        # Delete all if the collection is not empty
        if id_list:
            self.vector_store.delete(id_list)
            logger.info("Vector store has been reset.")
