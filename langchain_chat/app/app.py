"""
LangChain chatbot with LLM (powered by Ollama) using Flask.

This module defines a simple chatbot application using a Large Language Model (LLM)
and the Flask framework. It handles user messages, sends them to the LLM for processing,
and returns the chatbot's response.

The application is designed to be accessible through a web interface and utilizes CORS
for cross-origin requests. It also includes basic logging for monitoring and debugging.
"""

import logging
from collections import deque

from flask import Flask, jsonify, render_template, request
from flask.wrappers import Response
from flask_cors import CORS
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from ollama import ListResponse

# Initialize Flask app and CORS
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config.from_object("config")
cfg = app.config
logging.basicConfig(level=cfg["LOG_LEVEL"])

# Default model configuration
DEFAULT_MODEL: str = "llama3.2:1b"
DEFAULT_TEMPERATURE: float = 0.7
DEFAULT_MAX_HISTORY_MESSAGES: int = 10
DEFAULT_KEEP_ALIVE: str = "5m"
DEFAULT_NUM_CTX: int = 8192
DEFAULT_OLLAMA_HOST: str = "http://localhost:11434"

# Initialize the model handler with the model configuration from the config file
MODEL_CFG = cfg.get("MODEL", {})
model: ChatOllama = ChatOllama(
    model=MODEL_CFG.get("model_name", DEFAULT_MODEL),
    base_url=MODEL_CFG.get("ollama_host", DEFAULT_OLLAMA_HOST),
    temperature=MODEL_CFG.get("temperature", DEFAULT_TEMPERATURE),
    num_ctx=MODEL_CFG.get("context_window", DEFAULT_NUM_CTX),
    keep_alive=MODEL_CFG.get("keep_alive", DEFAULT_KEEP_ALIVE),
)
_conversation: deque[BaseMessage] = deque(
    maxlen=MODEL_CFG.get("keep_alive", DEFAULT_MAX_HISTORY_MESSAGES),
)


# Define the route for the index page
@app.route("/", methods=["GET"])
def index() -> str:
    """Render the index page for the chatbot."""
    return render_template("index.html")  # Render the index.html template


# Define the route for processing messages
@app.route("/messages", methods=["GET", "POST"])
def messages_route() -> tuple[Response, int]:
    if request.method == "GET":
        return get_messages()
    return process_message()


def get_messages() -> tuple[Response, int]:
    """Get the chat history."""
    try:
        history = [
            {"role": m.type, "content": m.content}
            for m in list(_conversation)
            if m.type in ("human", "ai")
        ]
        return (
            jsonify(
                {
                    "status": "success",
                    "messages": history,
                }
            ),
            200,
        )
    except Exception as e:
        app.logger.error("Error when getting chat history: %s", e)
        return (
            jsonify(
                {
                    "status": "error",
                }
            ),
            500,
        )


def process_message() -> tuple[Response, int]:
    """Process user messages and return chatbot responses."""
    try:
        # Extract the user's message from the request
        user_message: str = request.json["userMessage"]  # type: ignore
        app.logger.info("User message: %s", user_message)
        _conversation.append(HumanMessage(content=user_message))

        # Process the user's message using the worker module
        bot_response: AIMessage = model.invoke(list(_conversation))
        _conversation.append(bot_response)

        app.logger.info("Bot response: %s", bot_response.content)

        # Return the bot's response as JSON
        return (
            jsonify(
                {
                    "botResponse": bot_response.content,
                }
            ),
            200,
        )

    except KeyError:
        app.logger.error('Missing "userMessage" key in request data.')
        return jsonify({"error": 'Missing "userMessage" key in request data.'}), 400

    except Exception as e:
        app.logger.error("Error processing message: %s", e)
        return jsonify({"error": "Failed to process message."}), 500


# Define the route for resetting model chat history
@app.route("/reset-chat-history", methods=["GET"])
def reset_chat_history_route() -> tuple[Response, int]:
    """Reset the chat history."""
    try:
        _conversation.clear()
        app.logger.info("Bot chat history cleared.")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Chat history cleared",
                }
            ),
            200,
        )
    except Exception as e:
        app.logger.error("Error resetting chat history: %s", e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error resetting chat history: {e}",
                }
            ),
            500,
        )


@app.route("/model", methods=["GET", "POST"])
def process_model_route() -> tuple[Response, int]:
    """
    Processes a model based on the HTTP request method.


    Returns:
        tuple[Response, int]: A tuple containing a `Response` object and an integer indicating
            the HTTP status code.
    """
    if request.method == "GET":
        return process_get_model()

    return process_set_model()


def process_get_model() -> tuple[Response, int]:
    """
    Processes a request to retrieve information about the available models and
    the currently active model being used.

    Returns:
        tuple[Response, int]: A tuple containing a JSON response and the corresponding HTTP status
            code. The successful response includes the available model names and the
            actively selected model.
    """
    try:
        ollama_models: ListResponse = model._client.list()
        model_names: list[str] = [m.model for m in ollama_models.models if m.model is not None]
        return (
            jsonify(
                {
                    "success": True,
                    "available_models": model_names,
                    "current_model": model.model,
                }
            ),
            200,
        )
    except Exception as e:
        app.logger.error("Error when getting model info: %s", e)
        return jsonify({"error": "Internal server error"}), 500


def process_set_model() -> tuple[Response, int]:
    """
    Sets the model name based on the input JSON request and updates the
    application's state accordingly.

    Returns:
        tuple[Response, int]: A tuple containing a ``Response`` object and an integer status code.
    """
    try:
        model_name = request.json["model"]  # type: ignore
        app.logger.info("Setting model to %s", model_name)
        model.model = model_name
        return jsonify({"success": True}), 200

    except KeyError as e:
        app.logger.error("Missing key in request data: %s", e)
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except Exception as e:
        app.logger.error("Error processing message: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# Run the Flask app
if __name__ == "__main__":
    app.run()
