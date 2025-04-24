import logging

DEBUG = True
TESTING = True
LOG_LEVEL = logging.INFO
MODEL = dict(
    model_id='meta-llama/Llama-3.2-1B-Instruct',
    model_params=dict(
        max_new_tokens=600,
    ),
    max_history_messages=10,
)