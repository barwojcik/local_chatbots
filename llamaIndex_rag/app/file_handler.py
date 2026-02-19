"""
File handling utilities for document processing in the RAG application.

This module provides a FileHandler class that manages file operations,
including saving uploaded files, validating file types, and cleaning up
temporary files.

Example usage:
file_handler = FileHandler()
# get file (FileStorage)
file_path = file_handler.save_file(file)
# do something with the saved file
file_handler.cleanup_file(file_path)
"""

import logging
import os
from collections.abc import Iterable
from typing import Any

from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles file operations for document processing.

    Attributes:
        upload_folder (str): Directory where uploaded files will be stored

    Args:
        upload_folder (str): Directory where uploaded files will be stored
        extensions (list[str]): List of allowed file extensions (default: ['pdf'])

    Methods:
        from_config (cls, config): Creates a new instance of the FileHandler class from a
            configuration dictionary.
        save_file: Save an uploaded file securely.
        save_files: Save all uploaded files securely.
        cleanup_file: Remove a processed file from the upload directory.
        cleanup_files: Remove all processed files from the upload directory.
    """

    DEFAULT_EXTENSIONS: set[str] = {"csv", "docx", "epub", "hwp", "ipynb", "mbox", "md", "pdf"}

    def __init__(
        self,
        upload_folder: str = "uploads",
        extensions: list[str] | None = None,
    ) -> None:
        """
        Initialize FileHandler with a specified upload folder.

        Args:
            upload_folder (str): Directory where uploaded files will be stored
            extensions (list[str]): List of allowed file extensions (default: ['pdf'])
        """
        self.upload_folder = upload_folder
        if extensions is not None:
            self._allowed_extensions = {*extensions}
        else:
            self._allowed_extensions = self.DEFAULT_EXTENSIONS
        self._create_upload_directory()

    @classmethod
    def from_config(cls, file_config: dict[str, Any]) -> "FileHandler":
        """
        Creates a new instance of the FileHandler class from a configuration dictionary.

        Args:
            file_config: Configuration dictionary containing file settings.

        Returns:
            FileHandler: New instance of the FileHandler class initialized with the provided
                configuration.
        """
        return cls(**file_config)

    def _create_upload_directory(self) -> None:
        """Create an upload directory if it doesn't exist."""
        os.makedirs(self.upload_folder, exist_ok=True)

    def _allowed_file(self, filename: str) -> None:
        """
        Check if the file extension is allowed.

        Args:
            filename (str): Name of the file to check.

        Raises:
            ValueError: If the file is not allowed or does not exist.
        """
        if not filename:
            raise ValueError("No file provided.")

        if "." not in filename:
            raise ValueError("Invalid file extension.")

        if not filename.lower().endswith(tuple(self._allowed_extensions)):
            raise ValueError("File extension not allowed.")

    def save_file(self, file: FileStorage) -> str:
        """
        Save an uploaded file securely.

        Args:
            file: FileStorage object from Flask request.

        Returns:
            file_path: Path where the file was saved.

        Raises:
            ValueError: If the file is not allowed or does not exist.

        """
        self._allowed_file(file.filename)
        filename: str = secure_filename(file.filename)
        file_path: str = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        logger.info("File saved successfully at: %s", file_path)
        return file_path

    def save_files(self, file_list: Iterable[FileStorage]) -> list[str]:
        """
        Save an uploaded files securely.

        Args:
            file_list: List of the FileStorage objects from Flask request.

        Returns:
            file_paths: list of paths where the files were saved.

        Raises:
            ValueError: If the file is not allowed or does not exist.

        """
        file_paths: list[str] = [self.save_file(file) for file in file_list]
        return file_paths

    @staticmethod
    def cleanup_file(file_path: str) -> None:
        """
        Remove a processed file from the upload directory.

        Args:
            file_path (str): Path to the file to be removed.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Cleaned up file: %s", file_path)
        except Exception as e:
            logger.error("Error cleaning up file %s: %s", file_path, e)

    def cleanup_files(self, file_paths: list[str]) -> None:
        """
        Remove a processed file from the upload directory.

        Args:
            file_paths (str): List of paths to the files to be removed.
        """
        for file_path in file_paths:
            self.cleanup_file(file_path)
