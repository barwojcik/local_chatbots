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
MODEL: dict[str, Any] = dict(
    ollama_host=OLLAMA_HOST,
    model_name=MODEL_NAME,
)
