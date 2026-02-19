"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
"""

import logging
import os
from typing import Any

DEBUG: bool = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
TESTING: bool = os.getenv("FLASK_TESTING", "").lower() in {"1", "true", "yes", "on"}
LOG_LEVEL: int | str = os.getenv("APP_LOG_LEVEL", logging.INFO)
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3.2:3b")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Multi-agent system configuration
# Note: All agents share the same OllamaModelHandler instance
# configured by MODEL_NAME and OLLAMA_HOST
AGENTS: dict[str, Any] = dict(
    # Router agent determines if RAG retrieval is needed
    router=dict(
        confidence_threshold=0.7,
    ),
    # Query analyzer enhances queries for better retrieval
    query_analyzer=dict(
        generate_variations=True,
        max_variations=2,
    ),
    # Retriever agent handles document retrieval
    retriever=dict(
        strategies=["semantic"],
        enable_reranking=True,
        max_results=5,
    ),
    # Synthesizer agent generates final responses
    synthesizer=dict(
        include_citations=True,
        max_context_chunks=5,
    ),
)

VECTOR_STORE: dict[str, Any] = dict(
    embeddings_model=MODEL_NAME,
    ollama_host=OLLAMA_HOST,
    query_params=dict(
        k=5,
    ),
    document_processor_config=dict(
        chunking_strategy="semantic",  # Options: "fixed", "semantic", "hierarchical"
        chunk_size=1024,
        chunk_overlap=128,
        extract_metadata=True,
        preserve_structure=True,
    ),
)

FILES: dict[str, Any] = dict(
    upload_folder="uploads",
    extensions=["pdf"],
)
