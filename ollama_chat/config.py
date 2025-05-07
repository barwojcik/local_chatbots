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
