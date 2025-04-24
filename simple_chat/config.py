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
    model_params=dict(
        max_new_tokens=600,
    ),
    max_history_messages=10,
)
