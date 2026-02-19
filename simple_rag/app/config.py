"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
For vector store embeddings_model and model_kwargs configuration,
see: https://python.langchain.com/api_reference/huggingface/embeddings/langchain_huggingface.embeddings.huggingface.HuggingFaceEmbeddings.html
For text splitter configuration, see: https://huggingface.co/docs/langchain/main_classes/text_splitter/recursive_character_text_splitter
For query parameters configuration, see: https://huggingface.co/docs/vectorstores/main_classes/retrievers#retriever.similarity_search
"""

import logging
import os
from typing import Any

DEBUG: bool = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
TESTING: bool = os.getenv("FLASK_TESTING", "").lower() in {"1", "true", "yes", "on"}
LOG_LEVEL: int | str = os.getenv("APP_LOG_LEVEL", logging.INFO)
MODEL: dict[str, Any] = dict(
    model_id="meta-llama/Llama-3.2-1B-Instruct",
    device="cuda:0",
    max_history_messages=10,
    model_params=dict(
        max_new_tokens=600,
    ),
)
VECTOR_STORE: dict[str, Any] = dict(
    embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs=dict(
        device="cuda:0",
    ),
    splitter_params=dict(
        chunk_size=1024,
        chunk_overlap=64,
    ),
    query_params=dict(
        k=5,
    ),
)
FILES: dict[str, Any] = dict(
    upload_folder="uploads",
    extensions=["pdf"],
)
