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
MODEL: dict[str, Any] = dict(
    model_id="meta-llama/Llama-3.2-1B-Instruct",
    device="cuda:0",
    max_history_messages=10,
    model_params=dict(
        max_new_tokens=600,
    ),
)
