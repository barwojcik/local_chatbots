# LlamaIndex RAG (Retrieval-Augmented Generation)

[![Python 3.10.12](https://img.shields.io/badge/python-3.10.12-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

A powerful RAG-based chatbot application that enhances Large Language Model (LLM) responses with document retrieval capabilities, providing context-aware answers through an interactive web interface.

## Features

- Document upload and processing
- Vector-based document retrieval
- Context-aware LLM responses
- Real-time chat interface
- RESTful API support
- Docker support for easy deployment
- Web-based user interface

## Requirements

- Python 3.10.12
- virtualenv (Python package manager)
- Docker (optional, for containerized deployment)
- Storage space for document vectors
- Ollama running locally

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/barwojcik/local_chatbots.git
   cd llamaIndex_rag
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
   
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t llamaindex-rag .
   ```

2. Run the container:
   ```bash
   docker run --name llamaindex-rag \
       --network host \
       llamaindex-rag
   ```

## Usage

1. Make sure Ollama is running
2. Start the application:
   ```bash
   python app.py
   ```
   or
   ```bash
   flask --app app.py run
   ```
   alternatively, start docker container
   ```bash
   docker start llamaindex-rag
   ```

3. Open your web browser and navigate to `http://localhost:5000`

4. Start chatting

## File Structure

- `app.py`: Main Flask application
- `config.py`: Configuration settings
- `file_handler.py`: Document processing utilities
- `model.py`: LLM integration
- `vector_store.py`: Vector database management
- `static/`: Static web assets
- `templates/`: HTML templates