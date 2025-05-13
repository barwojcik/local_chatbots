"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
"""

import logging

DEBUG = False
TESTING = False
LOG_LEVEL = logging.INFO
MODEL_NAME = "llama3.2:3b"
OLLAMA_HOST = "http://localhost:11434"
MODEL = dict(
    ollama_host=OLLAMA_HOST,
    model_name=MODEL_NAME,
)
VECTOR_STORE = dict(
    embeddings_model=MODEL_NAME,
    ollama_host=OLLAMA_HOST,
    splitter_params=dict(
        chunk_size=1024,
        chunk_overlap=64,
    ),
    query_params=dict(
        similarity_top_k=5,
    ),
)
FILES = dict(
    upload_folder="uploads",
)
