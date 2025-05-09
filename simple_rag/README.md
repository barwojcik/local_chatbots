# Simple RAG (Retrieval-Augmented Generation)

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
- Hugging Face API token for LLM access

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/barwojcik/local_chatbots.git
   cd simple_rag
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
   
3. Install PyTorch and dependencies:
   ```bash
   pip install torch
   pip install -r requirements.txt
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t simple-rag .
   ```

2. Run the container:
   ```bash
   docker run --gpus all \
       -e HF_TOKEN=<your_token> \
       -v /path/to/documents:/app/uploads \
       -p 5000:5000 \ 
       -n simple-rag \
       simple-rag
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
   or
   ```bash
   flask --app app.py run
   ```
   alternatively, start docker container
   ```bash
   docker start simple-rag
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload documents through the web interface to create the knowledge base

4. Start chatting with the RAG-enhanced model

## File Structure

- `app.py`: Main Flask application
- `config.py`: Configuration settings
- `file_handler.py`: Document processing utilities
- `model.py`: LLM integration
- `vector_store.py`: Vector database management
- `static/`: Static web assets
- `templates/`: HTML templates