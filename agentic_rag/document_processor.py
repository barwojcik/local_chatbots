"""
Enhanced document processor with semantic chunking and metadata extraction.

This module provides advanced document processing capabilities including:
- Semantic-aware chunking based on document structure
- Metadata extraction (titles, headings, page numbers)
- Hierarchical document organization
- Multiple chunking strategies
"""

import logging
import re
from typing import Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes documents with advanced chunking and metadata extraction.

    This class provides sophisticated document processing including semantic chunking,
    metadata extraction, and hierarchical organization of document content.

    Args:
        chunking_strategy (str, optional): Strategy for chunking documents.
            Options: "fixed", "semantic", "hierarchical". Default: "semantic".
        chunk_size (int, optional): Size of chunks for fixed chunking. Default: 1024.
        chunk_overlap (int, optional): Overlap between chunks. Default: 128.
        extract_metadata (bool, optional): Whether to extract metadata. Default: True.
        preserve_structure (bool, optional): Whether to preserve document structure. Default: True.

    Methods:
        from_config: Creates a new instance from a configuration dictionary.
        process_document: Processes a single document and returns chunks.
        process_documents: Processes multiple documents.
    """

    def __init__(
        self,
        chunking_strategy: str = "semantic",
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        extract_metadata: bool = True,
        preserve_structure: bool = True,
    ) -> None:
        """
        Initializes the DocumentProcessor with specified parameters.

        Args:
            chunking_strategy: Strategy for chunking documents.
            chunk_size: Size of chunks for fixed chunking.
            chunk_overlap: Overlap between chunks.
            extract_metadata: Whether to extract metadata.
            preserve_structure: Whether to preserve document structure.
        """
        self._chunking_strategy = chunking_strategy
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._extract_metadata = extract_metadata
        self._preserve_structure = preserve_structure

        logger.info(
            "DocumentProcessor initialized with strategy=%s, chunk_size=%d, overlap=%d",
            chunking_strategy,
            chunk_size,
            chunk_overlap,
        )

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "DocumentProcessor":
        """
        Creates a new instance from a configuration dictionary.

        Args:
            config: Configuration dictionary containing processor settings.

        Returns:
            DocumentProcessor: New instance configured with the provided settings.
        """
        return cls(**config)

    def _extract_heading_level(self, text: str) -> int | None:
        """
        Extracts heading level from text if it appears to be a heading.

        Args:
            text: Text to analyze.

        Returns:
            Optional[int]: Heading level (1-6) or None if not a heading.
        """
        # Check for markdown-style headings
        heading_match = re.match(r"^(#{1,6})\s+", text)
        if heading_match:
            return len(heading_match.group(1))

        # Check for all-caps short lines (likely headings)
        if len(text) < 100 and text.isupper() and not text.endswith("."):
            return 2

        # Check for title case short lines
        words = text.split()
        if len(words) <= 10 and sum(1 for w in words if w and w[0].isupper()) >= len(words) * 0.7:
            return 3

        return None

    def _enhance_metadata(self, chunk: Document, doc_index: int, chunk_index: int) -> None:
        """
        Enhances chunk metadata with extracted information.

        Args:
            chunk: Document chunk to enhance.
            doc_index: Index of the source document.
            chunk_index: Index of the chunk within the document.
        """
        if not self._extract_metadata:
            return

        # Add basic indexing metadata
        chunk.metadata["doc_index"] = doc_index
        chunk.metadata["chunk_index"] = chunk_index

        # Try to extract heading if chunk starts with one
        first_line = chunk.page_content.split("\n")[0].strip()
        heading_level = self._extract_heading_level(first_line)

        if heading_level:
            chunk.metadata["heading"] = first_line
            chunk.metadata["heading_level"] = heading_level

        # Add content type hints
        content_lower = chunk.page_content.lower()
        if any(word in content_lower for word in ["table", "figure", "chart", "graph"]):
            chunk.metadata["contains_visual"] = True

        if content_lower.count("\n") > 10 and ":" in content_lower:
            chunk.metadata["structured_content"] = True

        # Estimate importance based on content
        importance_score = 0
        if heading_level:
            importance_score += (
                7 - heading_level
            ) * 2  # Higher importance for higher-level headings

        if any(
            word in content_lower for word in ["summary", "conclusion", "abstract", "introduction"]
        ):
            importance_score += 5

        chunk.metadata["importance_score"] = importance_score

    def _fixed_chunking(self, documents: list[Document]) -> list[Document]:
        """
        Performs fixed-size chunking on documents.

        Args:
            documents: List of documents to chunk.

        Returns:
            list[Document]: List of chunked documents.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return text_splitter.split_documents(documents)

    def _semantic_chunking(self, documents: list[Document]) -> list[Document]:
        """
        Performs semantic-aware chunking based on document structure.

        Args:
            documents: List of documents to chunk.

        Returns:
            list[Document]: List of semantically chunked documents.
        """
        chunks: list[Document] = []

        for doc in documents:
            # Split by paragraphs first
            paragraphs = doc.page_content.split("\n\n")
            current_chunk: list[str] = []
            current_size = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_size = len(para)

                # Check if this paragraph is a heading
                is_heading = self._extract_heading_level(para.split("\n")[0]) is not None

                # Start new chunk if:
                # 1. Current chunk would exceed size limit
                # 2. This is a heading and we have content
                if (current_size + para_size > self._chunk_size and current_chunk) or (
                    is_heading and current_chunk and current_size > self._chunk_size * 0.3
                ):
                    # Create chunk from accumulated paragraphs
                    chunk_content = "\n\n".join(current_chunk)
                    chunk = Document(
                        page_content=chunk_content,
                        metadata=doc.metadata.copy(),
                    )
                    chunks.append(chunk)

                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk.append(para)
                    current_size += para_size + 2  # +2 for \n\n

            # Add remaining content
            if current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunk = Document(
                    page_content=chunk_content,
                    metadata=doc.metadata.copy(),
                )
                chunks.append(chunk)

        return chunks

    def _hierarchical_chunking(self, documents: list[Document]) -> list[Document]:
        """
        Performs hierarchical chunking preserving document structure.

        Args:
            documents: List of documents to chunk.

        Returns:
            list[Document]: List of hierarchically chunked documents.
        """
        chunks: list[Document] = []
        current_section = None

        for doc in documents:
            lines = doc.page_content.split("\n")
            current_chunk: list[str] = []
            current_size = 0

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if line is a heading
                heading_level = self._extract_heading_level(line)

                if heading_level:
                    # Save previous chunk if exists
                    if current_chunk:
                        chunk_content = "\n".join(current_chunk)
                        chunk = Document(
                            page_content=chunk_content,
                            metadata=doc.metadata.copy(),
                        )
                        if current_section:
                            chunk.metadata["section"] = current_section
                        chunks.append(chunk)

                    # Start new section
                    current_section = line
                    current_chunk = [line]
                    current_size = len(line)
                else:
                    # Add to current chunk
                    current_chunk.append(line)
                    current_size += len(line) + 1

                    # Split if too large
                    if current_size > self._chunk_size:
                        chunk_content = "\n".join(current_chunk)
                        chunk = Document(
                            page_content=chunk_content,
                            metadata=doc.metadata.copy(),
                        )
                        if current_section:
                            chunk.metadata["section"] = current_section
                        chunks.append(chunk)

                        current_chunk = []
                        current_size = 0

            # Add remaining content
            if current_chunk:
                chunk_content = "\n".join(current_chunk)
                chunk = Document(
                    page_content=chunk_content,
                    metadata=doc.metadata.copy(),
                )
                if current_section:
                    chunk.metadata["section"] = current_section
                chunks.append(chunk)

        return chunks

    def _clean_chunks(self, chunks: list[Document]) -> None:
        """
        Cleans chunk content by removing extra whitespace.

        Args:
            chunks: List of chunks to clean.
        """
        for chunk in chunks:
            # Replace multiple newlines with double newline
            chunk.page_content = re.sub(r"\n{3,}", "\n\n", chunk.page_content)
            # Replace multiple spaces with single space
            chunk.page_content = re.sub(r" {2,}", " ", chunk.page_content)
            # Strip leading/trailing whitespace
            chunk.page_content = chunk.page_content.strip()

    def process_document(self, document_path: str, doc_index: int = 0) -> list[Document]:
        """
        Processes a single document and returns chunks with metadata.

        Args:
            document_path: Path to the document file.
            doc_index: Index of the document for tracking.

        Returns:
            list[Document]: List of processed document chunks.
        """
        logger.info(
            "Processing document: %s with strategy: %s", document_path, self._chunking_strategy
        )

        # Load document
        loader = PyPDFLoader(document_path)
        documents = loader.load()

        # Apply chunking strategy
        if self._chunking_strategy == "fixed":
            chunks = self._fixed_chunking(documents)
        elif self._chunking_strategy == "semantic":
            chunks = self._semantic_chunking(documents)
        elif self._chunking_strategy == "hierarchical":
            chunks = self._hierarchical_chunking(documents)
        else:
            logger.warning("Unknown chunking strategy: %s, using fixed", self._chunking_strategy)
            chunks = self._fixed_chunking(documents)

        # Clean chunks
        self._clean_chunks(chunks)

        # Enhance metadata
        for idx, chunk in enumerate(chunks):
            self._enhance_metadata(chunk, doc_index, idx)

        logger.info("Document processed: %d chunks created", len(chunks))

        return chunks

    def process_documents(self, document_paths: list[str] | str) -> list[Document]:
        """
        Processes multiple documents and returns all chunks.

        Args:
            document_paths: Path or list of paths to document files.

        Returns:
            list[Document]: List of all processed document chunks.
        """
        if isinstance(document_paths, str):
            document_paths = [document_paths]

        all_chunks = []
        for idx, path in enumerate(document_paths):
            chunks = self.process_document(path, doc_index=idx)
            all_chunks.extend(chunks)

        logger.info(
            "Total chunks created from %d documents: %d", len(document_paths), len(all_chunks)
        )

        return all_chunks
