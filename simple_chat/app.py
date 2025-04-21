"""
Simple chatbot with LLM using Flask.

This module defines a simple chatbot application using a Large Language Model (LLM)
and the Flask framework. It handles user messages, sends them to the LLM for processing,
and returns the chatbot's response.

The application is designed to be accessible through a web interface and utilizes CORS
for cross-origin requests. It also includes basic logging for monitoring and debugging.
"""
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from model import ModelHandler

# Initialize Flask app and CORS
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.logger.setLevel(logging.ERROR)

model = ModelHandler("meta-llama/Llama-3.2-1B-Instruct")

# Define the route for the index page
@app.route('/', methods=['GET'])
def index():
    """Render the index page for the chatbot."""
    return render_template('index.html')  # Render the index.html template

# Define the route for processing messages
@app.route('/process-message', methods=['POST'])
def process_message_route():
    """Process user messages and return chatbot responses."""
    try:
        # Extract the user's message from the request
        user_message = request.json['userMessage']
        app.logger.info('User message: %s', user_message)

        # Process the user's message using the worker module
        bot_response = model.predict(user_message)
        app.logger.info('Bot response: %s', bot_response)

        # Return the bot's response as JSON
        return jsonify({
            "botResponse": bot_response,
        }), 200

    except KeyError:
        app.logger.error('Missing "userMessage" key in request data.')
        return jsonify({'error': 'Missing "userMessage" key in request data.'}), 400

    except Exception as e:
        app.logger.error('Error processing message: %s', e)
        return jsonify({'error': 'Failed to process message.'}), 500

# Define the route for resetting model chat history
@app.route('/reset-chat-history', methods=['GET'])
def reset_chat_history_route():
    """Reset the chat history."""
    try:
        model.clear_history()
        app.logger.info("Bot chat history cleared.")
        return jsonify({
            "status": "success",
            "message": "Chat history cleared",
        }), 200
    except Exception as e:
        app.logger.error("Error resetting chat history: %s", e)
        return jsonify({
            "status": "error",
            "message": f"Error resetting chat history: {e}",
        }), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
