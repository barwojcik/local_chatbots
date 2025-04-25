# Simple Chat

[![Python 3.10.12](https://img.shields.io/badge/python-3.10.12-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

A powerful chatbot application that provides an interactive chat interface through web browsers, powered by Large Language Models (LLM).

## Features

- Real-time chat interface
- LLM-powered responses
- RESTful API support
- Docker support for easy deployment
- Web-based user interface

## Requirements

- Python 3.10.12
- virtualenv (Python package manager)
- Docker (optional, for containerized deployment)

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/barwojcik/local_chatbots.git
   cd simple_chat
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
   
3. Install PyTorch
   ```bash
   pip install torch
   ```


4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t simple-chat
   ```

2. Run the container:
   ```bash
   docker run --gpus all -e HF_TOKEN=<your_token> -p 5000:5000 simple-chat
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
   alternatively run docker container.


2. Open your web browser and navigate to `http://localhost:5000`