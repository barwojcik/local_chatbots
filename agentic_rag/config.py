"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
"""

import logging

DEBUG = False
TESTING = False
LOG_LEVEL = logging.DEBUG
MODEL_NAME = "llama3.2:3b"
OLLAMA_HOST = "http://localhost:11434"

# Multi-agent system configuration
AGENTS = dict(
    # Router agent determines if RAG retrieval is needed
    router=dict(
        model_name=MODEL_NAME,
        ollama_host=OLLAMA_HOST,
        confidence_threshold=0.7,
    ),
    # Query analyzer enhances queries for better retrieval
    query_analyzer=dict(
        model_name=MODEL_NAME,
        ollama_host=OLLAMA_HOST,
        generate_variations=True,
        max_variations=2,
    ),
    # Retriever agent handles document retrieval
    retriever=dict(
        model_name=MODEL_NAME,
        ollama_host=OLLAMA_HOST,
        strategies=["semantic", "hybrid"],
        enable_reranking=True,
        max_results=5,
    ),
    # Synthesizer agent generates final responses
    synthesizer=dict(
        model_name=MODEL_NAME,
        ollama_host=OLLAMA_HOST,
        include_citations=True,
        max_context_chunks=5,
    ),
)

VECTOR_STORE = dict(
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

FILES = dict(
    upload_folder="uploads",
    extensions=["pdf"],
)
