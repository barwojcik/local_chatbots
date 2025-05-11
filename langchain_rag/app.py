"""
LangChain RAG with Ollama using Flask.

This module defines a RAG application using a Large Language Model (LLM)
and the Flask framework. It handles user messages, sends them to the LLM for processing,
and returns the chatbot's response.

The application is designed to be accessible through a web interface and utilizes CORS
for cross-origin requests. It also includes basic logging for monitoring and debugging.
"""

from flask import Flask, render_template, request, jsonify
from flask.wrappers import Response
from flask_cors import CORS
from werkzeug.datastructures.file_storage import FileStorage
from model import RAGOllamaModelHandler
from file_handler import FileHandler
from vector_store import VectorStoreHandler

# Initialize Flask app and CORS
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config.from_object("config")
cfg = app.config
app.logger.setLevel(cfg["LOG_LEVEL"])

model: RAGOllamaModelHandler = (
    RAGOllamaModelHandler.from_config(cfg["MODEL"]) if "MODEL" in cfg else RAGOllamaModelHandler()
)

vector_store: VectorStoreHandler = (
    VectorStoreHandler.from_config(cfg["VECTOR_STORE"]) if "VECTOR_STORE" in cfg else VectorStoreHandler()
)

file_handler: FileHandler = FileHandler.from_config(cfg["FILES"]) if "FILES" in cfg else FileHandler()


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
        return (
            jsonify(
                {
                    "status": "success",
                    "messages": model.get_history(),
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
        user_message: str = request.json["userMessage"]
        app.logger.info("User message: %s", user_message)

        # Get context to a user message from the vector store
        context: list[str] = vector_store.get_context(user_message)

        # Process the user's message using the worker module
        bot_response: str = model.predict(user_message, context)
        app.logger.info("Bot response: %s", bot_response)

        # Return the bot's response as JSON
        return (
            jsonify(
                {
                    "botResponse": bot_response,
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


# Define the route for processing documents
@app.route("/document", methods=["POST"])
def process_document() -> tuple[Response, int]:
    """Process uploaded documents and return a success message to the client."""
    # Check if a file was uploaded
    try:
        if not request.files:
            return (
                jsonify(
                    {
                        "botResponse": "It seems like the file was not uploaded correctly, can you try "
                                       "again. If the problem persists, try using a different file"
                    }
                ),
                400,
            )

        for file in request.files.values():
            file_path: str = file_handler.save_file(file)
            vector_store.process_document(file_path)
            file_handler.cleanup_file(file_path)

        # Return a success message as JSON
        return (
            jsonify(
                {
                    "botResponse": "Thank you for providing your PDF document. I have analyzed it, so now you can ask me any "
                    "questions regarding it!"
                }
            ),
            200,
        )
    except ValueError as e:
        app.logger.error("Error processing document: %s", e)
        return jsonify({"botResponse": f"An error occurred while processing your document: {e}"}), 400
    except Exception as e:
        app.logger.error("Error processing document: %s", e)
        return jsonify({"botResponse": f"An error occurred while processing your document: {e}"}), 500


# Define the route for resetting the vector store
@app.route("/reset-vector-store", methods=["GET"])
def reset_vector_store() -> tuple[Response, int]:
    """Reset the vector store and return a success message to the client."""
    try:
        vector_store.reset()
        app.logger.info("Vector store cleared.")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Vector store cleared",
                }
            ),
            200,
        )
    except Exception as e:
        app.logger.error("Error resetting vector store: %s", e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error resetting vector store: {e}",
                }
            ),
            500,
        )


# Define the route for resetting model chat history
@app.route("/reset-chat-history", methods=["GET"])
def reset_chat_history() -> tuple[Response, int]:
    """Reset the chat history."""
    try:
        model.clear_history()
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
def process_model() -> tuple[Response, int]:
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
        return (
            jsonify(
                {
                    "success": True,
                    "available_models": model.get_available_model_names(),
                    "current_model": model.get_current_model_name(),
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
        model_name = request.json["model"]
        app.logger.info("Setting model to %s", model_name)
        if model.set_model(model_name):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Invalid model name"}), 400
    except KeyError as e:
        app.logger.error("Missing key in request data: %s", e)
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except Exception as e:
        app.logger.error("Error processing message: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# Run the Flask app
if __name__ == "__main__":
    app.run()
