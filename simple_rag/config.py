"""
Simple Chat configuration file.
For Flask configuration, see: https://flask.palletsprojects.com/en/2.2.x/config/
For model parameters configuration, see: https://huggingface.co/docs/transformers/main_classes/pipelines
"""
import logging

DEBUG = True
TESTING = True
LOG_LEVEL = logging.INFO
MODEL = dict(
    model_id='meta-llama/Llama-3.2-1B-Instruct',
    device="cuda:0",
    max_history_messages=10,
    model_params=dict(
            max_new_tokens=600,
        ),
)
VECTOR_STORE = dict(
    embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs=dict(
        device='cuda:0',
    ),
    splitter_params=dict(
        chunk_size=1024,
        chunk_overlap=64,
    ),
    query_params=dict(
        k=5,
    ),
)