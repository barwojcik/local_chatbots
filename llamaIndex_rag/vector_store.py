"""
This module provides a `VectorStoreHandler` class for managing and querying a vector store.

The `VectorStoreHandler` class facilitates the process of loading, chunking, embedding, and storing
documents within a vector store, primarily for semantic search and retrieval of relevant information.

It leverages the LangChain and Hugging Face ecosystems to provide a streamlined workflow for
handling document processing and similarity search.

Example usage:
python from your_module import VectorStoreHandler

handler = VectorStoreHandler()
handler.process_document("path/to/your_document.pdf")
context = handler.get_context("your search query")
print(context) # Output: List of relevant text chunks

"""

import logging
import torch
from typing import Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class VectorStoreHandler:
    """
    Handles the loading, chunking, embedding, and querying of documents within a vector store.

    This class uses LangChain for document loading and chunking, Hugging Face for embeddings,
    and Chroma as the vector database.

    Attributes:
        embeddings (HuggingFaceEmbeddings): The embedding model used to generate document embeddings.
        vector_store (Chroma): The vector store used to store and manage document embeddings.
        splitter_params (dict[str, Any]): Additional parameters for the text splitter.
        query_params (dict[str, Any]): Additional parameters for the similarity search query.

    Args:
        embeddings_model (str, optional): The identifier of the Hugging Face embeddings model.
            Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        model_kwargs (dict[str, Any], optional): Additional keyword arguments to pass to the embedding model.
                If not provided, defaults to {"device": "cuda:0"} if CUDA is available, otherwise to {"device": "cpu"}.
        splitter_params (dict[str, Any], optional): Additional parameters for the text splitter.
        query_params (dict[str, Any], optional): Additional parameters for the similarity search query.

    Methods:
        clean_chunks(chunks): Removes newlines from text chunks.
        process_document(document_path): Loads, chunks, embeds, and stores a document in the vector store.
        get_context(query): Retrieves relevant context from the vector store based on a query.
        reset(): Resets the vector store by deleting the content of the collection.
    """

    def __init__(
        self,
        embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs: dict[str, Any] = None,
        splitter_params: dict[str, Any] = None,
        query_params: dict[str, Any] = None,
    ) -> None:
        """
        Initializes the VectorStoreHandler with the specified model and parameters.

        Args:
            embeddings_model (str, optional): The identifier of the Hugging Face embeddings model.
                Defaults to "sentence-transformers/all-MiniLM-L6-v2".
            model_kwargs (dict[str, Any], optional): Additional keyword arguments to pass to the embeddings model.
                If not provided, defaults to {"device": "cuda:0"} if CUDA is available, otherwise to {"device": "cpu"}.
            splitter_params (dict[str, Any], optional): Additional parameters for the text splitter.
            query_params (dict[str, Any], optional): Additional parameters for the similarity search query.
        """
        logger.info("Initializing vector store...")
        model_kwargs = model_kwargs or dict()
        if "device" not in model_kwargs.keys():
            model_kwargs["device"] = "cuda:0" if torch.cuda.is_available() else "cpu"
        logger.info("Embeddings model will be initialized on %s.", model_kwargs["device"])
        self.embeddings: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
            model_name=embeddings_model,
            model_kwargs=model_kwargs,
        )
        logger.info("Embeddings model %s has been initialized.", embeddings_model)
        self.vector_store: Chroma = Chroma(embedding_function=self.embeddings)
        logger.info("Vector store has been initialized.")
        self.splitter_params: dict[str, Any] = splitter_params or dict()
        self.query_params: dict[str, Any] = query_params or dict()

    @classmethod
    def from_config(cls, vector_store_config: dict[str, str]) -> "VectorStoreHandler":
        """
        Creates a new instance of the VectorStoreHandler class from a configuration dictionary.

        Args:
            vector_store_config (dict[str, str]): A dictionary containing the configuration parameters for the vector store.

        Returns:
            VectorStoreHandler: A new instance of the VectorStoreHandler class initialized with the provided configuration.
        """
        config: dict[str, Any] = vector_store_config.copy()
        return cls(**config)

    @staticmethod
    def _clean_chunks(chunks):
        """Removes newlines from text chunks."""
        for chunk in chunks:
            chunk.page_content = chunk.page_content.replace("\n", " ")

    def process_document(self, document_path: str) -> None:
        """
        Loads, chunks, embeds, and stores a document in the vector store.

        Args:
            document_path (str): The path to the document to be processed.
        """
        # Load and chunk the document
        logger.info("Processing %s.", document_path)
        loader: PyPDFLoader = PyPDFLoader(document_path)
        logger.info("Document will be slit with parameters: %s", self.splitter_params)

        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(**self.splitter_params)
        chunks: list[Document] = loader.load_and_split(text_splitter)
        self._clean_chunks(chunks)

        self.vector_store.add_documents(chunks)
        logger.info("Vector store has been populated from %s.", document_path)

    def get_context(self, query: str) -> list[str]:
        """
        Retrieves relevant context from the vector store based on a query.

        Args:
            query (str): The search query.

        Returns:
            context (list[str]): A list of relevant text chunks from the stored documents.
        """
        documents: list[Document] = self.vector_store.similarity_search(query, **self.query_params)
        context: list[str] = [doc.page_content for doc in documents]
        logger.info("Query %s returned %s", query, context)
        return context

    def reset(self):
        """
        Resets the vector store by deleting the content of the collection.
        """
        # Get the list of ids in the collection
        id_list = self.vector_store.get()["ids"]
        # Delete all if the collection is not empty
        if id_list:
            self.vector_store.delete(id_list)
            logger.info("Vector store has been reset.")
