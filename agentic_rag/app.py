"""
LangChain Multi-Agent RAG with Ollama using Flask.

This module defines a Multi-Agent RAG application using a Large Language Model (LLM)
and the Flask framework. It handles user messages, sends them to the LLM for processing,
and returns the chatbot's response.

The application is designed to be accessible through a web interface and utilizes CORS
for cross-origin requests. It also includes basic logging for monitoring and debugging.
"""

import logging
import json
import queue
import threading
from flask import Flask, render_template, request, jsonify, stream_with_context
from flask.wrappers import Response
from flask_cors import CORS
from model import OllamaModelHandler
from file_handler import FileHandler
from vector_store import VectorStoreHandler
from agents import RouterAgent, QueryAnalyzerAgent, RetrieverAgent, SynthesizerAgent

# Initialize Flask app and CORS
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config.from_object("config")
cfg = app.config
logging.basicConfig(level=cfg["LOG_LEVEL"])

# Initialize shared model handler
model: OllamaModelHandler = OllamaModelHandler(
    model_name=cfg.get("MODEL_NAME"),
    ollama_host=cfg.get("OLLAMA_HOST"),
)

vector_store: VectorStoreHandler = (
    VectorStoreHandler.from_config(cfg["VECTOR_STORE"])
    if "VECTOR_STORE" in cfg
    else VectorStoreHandler()
)

file_handler: FileHandler = (
    FileHandler.from_config(cfg["FILES"]) if "FILES" in cfg else FileHandler()
)

# Initialize agents with shared model handler
router_agent: RouterAgent = RouterAgent(
    model_handler=model,
    **cfg["AGENTS"]["router"] if "AGENTS" in cfg and "router" in cfg["AGENTS"] else {}
)

query_analyzer_agent: QueryAnalyzerAgent = QueryAnalyzerAgent(
    model_handler=model,
    **cfg["AGENTS"]["query_analyzer"] if "AGENTS" in cfg and "query_analyzer" in cfg["AGENTS"] else {}
)

retriever_agent: RetrieverAgent = RetrieverAgent(
    model_handler=model,
    **cfg["AGENTS"]["retriever"] if "AGENTS" in cfg and "retriever" in cfg["AGENTS"] else {}
)
retriever_agent.set_vector_store(vector_store)

synthesizer_agent: SynthesizerAgent = SynthesizerAgent(
    model_handler=model,
    **cfg["AGENTS"]["synthesizer"] if "AGENTS" in cfg and "synthesizer" in cfg["AGENTS"] else {}
)


# Define the route for the index page
@app.route("/", methods=["GET"])
def index() -> str:
    """Render the index page for the chatbot."""
    return render_template("index.html")  # Render the index.html template


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


def process_message_with_streaming(user_message: str, progress_queue: queue.Queue) -> str:
    """Process message and emit progress updates to queue."""
    try:
        # Get chat history for context-aware responses
        chat_history = model.get_history()

        # Step 1: Router agent determines if RAG retrieval is needed
        progress_queue.put(
            {"type": "progress", "agent": "router", "status": "analyzing query type"}
        )
        has_docs = vector_store.has_documents()
        routing_decision = router_agent.execute(user_message, has_documents=has_docs)
        app.logger.info("Routing decision: %s", routing_decision)
        decision = (
            "using RAG" if routing_decision["needs_retrieval"] and has_docs else "direct response"
        )
        progress_queue.put(
            {"type": "progress", "agent": "router", "status": "completed", "decision": decision}
        )

        if routing_decision["needs_retrieval"] and has_docs:
            # Multi-agent RAG pipeline
            app.logger.info("Using multi-agent RAG pipeline")

            # Step 2: Query analyzer enhances the query
            progress_queue.put(
                {"type": "progress", "agent": "query_analyzer", "status": "enhancing query"}
            )
            query_analysis = query_analyzer_agent.execute(user_message)
            app.logger.info("Query analysis: %s", query_analysis)
            progress_queue.put(
                {
                    "type": "progress",
                    "agent": "query_analyzer",
                    "status": "completed",
                }
            )

            # Step 3: Retriever agent fetches relevant documents
            progress_queue.put(
                {"type": "progress", "agent": "retriever", "status": "searching documents"}
            )
            retrieved_documents = retriever_agent.execute(user_message, query_analysis)
            app.logger.info("Retrieved %d documents", len(retrieved_documents))
            progress_queue.put(
                {
                    "type": "progress",
                    "agent": "retriever",
                    "status": "completed",
                    "documents_found": len(retrieved_documents),
                }
            )

            # Step 4: Synthesizer agent generates response with context
            progress_queue.put(
                {"type": "progress", "agent": "synthesizer", "status": "generating response"}
            )
            bot_response = synthesizer_agent.execute(
                user_message,
                retrieved_documents,
                chat_history=chat_history,
            )
        else:
            # Direct response without RAG
            app.logger.info("Using direct response without RAG")
            progress_queue.put(
                {"type": "progress", "agent": "synthesizer", "status": "generating response"}
            )
            bot_response = synthesizer_agent.execute_without_context(
                user_message,
                chat_history=chat_history,
            )

        progress_queue.put({"type": "progress", "agent": "synthesizer", "status": "completed"})
        app.logger.info("Bot response: %s", bot_response)

        # Update model's chat history
        model.add_to_history({"role": "user", "content": user_message})
        model.add_to_history({"role": "assistant", "content": bot_response})

        return bot_response

    except Exception as e:
        app.logger.error("Error processing message: %s", e)
        progress_queue.put({"type": "error", "message": str(e)})
        return None


@app.route("/messages/stream", methods=["POST"])
def stream_message_processing():
    """Stream agent progress and response using SSE."""
    try:
        user_message: str = request.json["userMessage"]
        app.logger.info("Streaming message processing: %s", user_message)

        def generate():
            progress_queue = queue.Queue()

            # Start processing in background thread
            def process():
                bot_response = process_message_with_streaming(user_message, progress_queue)
                progress_queue.put({"type": "response", "content": bot_response})
                progress_queue.put({"type": "done"})

            thread = threading.Thread(target=process)
            thread.start()

            # Stream progress updates
            while True:
                try:
                    update = progress_queue.get(timeout=30)
                    yield f"data: {json.dumps(update)}\n\n"

                    if update.get("type") == "done":
                        break
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

            thread.join(timeout=1)

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    except Exception as e:
        app.logger.error("Error in stream_message_processing: %s", e)
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

        # Save uploaded files
        file_paths: list[str] = file_handler.save_files(request.files.values())
        # Process files and populate vector store with them
        vector_store.process_documents(file_paths)
        # Delete files after processing
        file_handler.cleanup_files(file_paths)

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
        return (
            jsonify({"botResponse": f"An error occurred while processing your document: {e}"}),
            400,
        )
    except Exception as e:
        app.logger.error("Error processing document: %s", e)
        return (
            jsonify({"botResponse": f"An error occurred while processing your document: {e}"}),
            500,
        )


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
