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

import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document, BaseNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryResult
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class VectorStoreHandler:
    """
    Handles the loading, chunking, embedding, and querying of documents within a vector store.

    This class uses LlamaIndex for document loading and chunking, Ollama for embeddings,
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
    COLLECTION_NAME: str = "uploaded_documents"
    DEFAULT_EXTENSIONS: set[str] = {"csv", "docx", "epub", "hwp", "ipynb", "mbox", "md", "pdf"}

    def __init__(
        self,
        embeddings_model: Optional[str] = None,
        ollama_host: Optional[str] = None,
        model_kwargs: dict[str, Any] = None,
        splitter_params: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
    ) -> None:
        """
        Initializes the VectorStoreHandler with the specified model and parameters.

        Args:
            embeddings_model (str, optional): The identifier of the Ollama embeddings model. Default "llama3.2:1b".
            model_kwargs (dict[str, Any], optional): Additional keyword arguments to pass to the embedding model.
            splitter_params (dict[str, Any], optional): Additional parameters for the text splitter.
            query_params (dict[str, Any], optional): Additional parameters for the similarity search query.
        """
        logger.info("Initializing vector store...")
        model_kwargs = model_kwargs or dict()
        self._embeddings: OllamaEmbedding = OllamaEmbedding(
            model_name=(embeddings_model or self.DEFAULT_MODEL),
            base_url=ollama_host,
            **model_kwargs,
        )
        logger.info("Embeddings model %s has been initialized.", embeddings_model)
        self._text_splitter = SentenceSplitter(**splitter_params)
        self._query_params: dict[str, Any] = query_params or dict()
        self._vector_store: ChromaVectorStore = self._init_chroma()
        logger.info("Vector store has been initialized.")

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

    def _init_chroma(self) -> ChromaVectorStore:
        """Initializes the chroma vector store."""
        client: chromadb.EphemeralClient = chromadb.EphemeralClient()
        collection: chromadb.Collection = client.create_collection(self.COLLECTION_NAME)
        return ChromaVectorStore(
            client=client,
            chroma_collection=collection,
        )

    @staticmethod
    def _clean_chunks(chunks):
        """Removes newlines from text chunks."""
        for chunk in chunks:
            chunk.page_content = chunk.page_content.replace("\n", " ")

    def _load_documents(self, document_paths: list[str]) -> list[Document]:
        """Loads documents from a list of paths."""
        reader: SimpleDirectoryReader = SimpleDirectoryReader(
            input_files=document_paths,
            required_exts=list(self.DEFAULT_EXTENSIONS),
        )
        return reader.load_data()

    def _embed_nodes(self, nodes: list[BaseNode]) -> list[BaseNode]:
        """Populates embedding field in given nodes."""
        for node in nodes:
            node.embedding = self._embeddings.get_text_embedding(node.text)
        return nodes

    def process_documents(self, document_paths: list[str] | str) -> None:
        """
        Loads, chunks, embeds, and stores documents in the vector store.

        Args:
            document_paths (list[str] | str): The path or list of paths to the documents to be processed.
        """
        if isinstance(document_paths, str):
            document_paths = [document_paths]

        documents: list[Document] = self._load_documents(document_paths)
        nodes: list[BaseNode] = self._text_splitter.get_nodes_from_documents(documents)
        nodes = self._embed_nodes(nodes)

        self._vector_store.add(nodes)
        logger.info("Vector store has been populated from %s.", document_paths)

    def get_context(self, query: str) -> list[str]:
        """
        Retrieves relevant context from the vector store based on a query.

        Args:
            query (str): The search query.

        Returns:
            context (list[str]): A list of relevant text chunks from the stored documents.
        """
        vector_store_query: VectorStoreQuery = VectorStoreQuery(
            query_str=query,
            query_embedding=self._embeddings.get_text_embedding(query),
            **self._query_params,
        )
        query_results: VectorStoreQueryResult = self._vector_store.query(vector_store_query)
        context: list[str] = [node.text for node in query_results.nodes]
        logger.info("Query %s returned %s", query, context)
        return context

    def reset(self):
        """Resets the vector store by deleting the content of the collection."""
        self._vector_store.clear()
        logger.info("Vector store has been reset.")
