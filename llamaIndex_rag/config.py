"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
"""

import logging

DEBUG = False
TESTING = False
LOG_LEVEL = logging.INFO
MODEL = dict(
    ollama_host='http://localhost:11434',
    model_name='llama3.2:1b'
)
VECTOR_STORE = dict(
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
FILES = dict(
    upload_folder="uploads",
    extensions=["pdf"],
)