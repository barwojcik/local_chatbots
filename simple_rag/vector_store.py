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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VectorStoreHandler:
    """
    Handles the loading, chunking, embedding, and querying of documents within a vector store.

    This class uses LangChain for document loading and chunking, Hugging Face for embeddings,
    and Chroma as the vector database.

    Attributes:
        embeddings (HuggingFaceEmbeddings): The embedding model used to generate document embeddings.
        vector_store (Chroma): The vector store used to store and manage document embeddings.
        chunk_size (int): The size of text chunks created from documents.
        chunk_overlap (int): The overlap between consecutive chunks to preserve context.

    Args:
        embeddings_model (str, optional): The identifier of the Hugging Face embeddings model.
            Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        chunk_size (int, optional): The size of text chunks. Defaults to 1024.
        chunk_overlap (int, optional): The overlap between chunks. Defaults to 64.
    """
    def __init__(
            self,
            embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
            chunk_size=1024,
            chunk_overlap=64,
    ) -> None:
        """
        Initializes the VectorStoreHandler with the specified model and parameters.

        Args:
            embeddings_model (str, optional): The identifier of the Hugging Face embeddings model.
                Defaults to "sentence-transformers/all-MiniLM-L6-v2".
            chunk_size (int, optional): The size of text chunks. Defaults to 1024.
            chunk_overlap (int, optional): The overlap between chunks. Defaults to 64.
        """
        logger.info("Initializing vector store...")
        device: str = "cuda:0" if torch.cuda.is_available() else "cpu"
        logger.info('Embeddings model will be initialized on %s.', device)
        self.embeddings: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
            model_name=embeddings_model,
            model_kwargs={"device": device},
        )
        logger.info('Embeddings model %s has been initialized.', embeddings_model)
        self.vector_store: Chroma = Chroma(embedding_function = self.embeddings)
        logger.info('Vector store has been initialized.')
        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap

    def process_document(self, document_path: str) -> None:
        """
        Loads, chunks, embeds, and stores a document in the vector store.

        Args:
            document_path (str): The path to the document to be processed.
        """
        # Load and chunk the document
        logger.info('Processing %s.', document_path)
        loader: PyPDFLoader = PyPDFLoader(document_path)
        logger.info(
            'Document will be slit with chunk_size %s and chunk_overlap %s',
            self.chunk_size, self.chunk_overlap,
        )
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks: list[Document] = loader.load_and_split(text_splitter)

        self.vector_store.add_documents(chunks)
        logger.info('Vector store has been populated from %s.', document_path)

    def get_context(self, query: str) -> list[str]:
        """
        Retrieves relevant context from the vector store based on a query.

        Args:
            query (str): The search query.

        Returns:
            list[str]: A list of relevant text chunks from the stored documents.
        """
        documents: list[Document] = self.vector_store.similarity_search(query)
        context: list[str] = [doc.page_content for doc in documents]
        logger.info('Query %s returned %s', query, context)
        return context

    def reset(self):
        """
        Resets the vector store by deleting the content of the collection.
        """
        # Get the list of ids in the collection
        id_list = self.vector_store.get()['ids']
        # Delete all if the collection is not empty
        if id_list:
            self.vector_store.delete()
            logger.info('Vector store has been reset.')