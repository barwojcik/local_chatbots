# Local LLM Chatbots

[![Python 3.10.12](https://img.shields.io/badge/python-3.10.12-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

A collection of Flask-based applications powered by Large Language Models (LLMs), ranging from
simple chat interfaces to advanced multi-agent Retrieval-Augmented Generation (RAG) systems.
Built using modern frameworks like `langchain`, `llama_index`, `chromadb` and powered by `ollama`
or `transformers`, all running locally on your machine. Dockerized and ready for containerized
deployment.

---

## Available Applications

### Chat

#### [**Simple Chat**](./simple_chat/README.md)
- Built using the `transformers` library
- Provides basic conversational capabilities
- Runs completely offline

#### [**Ollama Chat**](./ollama_chat/README.md)
- Built using the `ollama` library
- Provides basic conversational capabilities
- Runs completely offline

#### [**LangChain Chat**](./langchain_chat/README.md)
- Built using the `langchain` library
- Provides basic conversational capabilities
- Runs completely offline

#### [**LlamaIndex Chat**](./llamaIndex_chat/README.md)
- Built using the `llamaindex` library
- Provides basic conversational capabilities
- Runs completely offline

### RAG (Retrieval-Augmented Generation)

#### [**Simple RAG**](./simple_rag/README.md)
- Built using `transformers` and `langchain` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

#### [**LangChain RAG**](./langchain_rag/README.md)
- Built using `ollama` and `langchain` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

#### [**LlamaIndex RAG**](./llamaIndex_rag/README.md)
- Built using `ollama` and `llama_index` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

### Agentic RAG

#### [**Multi-Agent RAG**](./agentic_rag/README.md)
- Built using `ollama` and `langchain` libraries
- Coordinates specialized agents (router, query analyzer, retriever, synthesizer) to decide when to retrieve, refine queries, fetch relevant context, and generate answers
- Supports hybrid retrieval (semantic + keyword) with re-ranking and source citations

---

## Quick Start

Pull the image from the GitHub Container Registry (Replace `<APP_NAME>` with the name of the application you want to run):

```bash
docker pull ghcr.io/barwojcik/local_chatbots/<APP_NAME>:latest
```

**Note:** Most applications require `ollama` running.

---

## Usage
Each application can be run from its respective directory. You can find detailed instructions inside each application's README.md file:
- [**Simple Chat**](./simple_chat/README.md#installation)
- [**Ollama Chat**](./ollama_chat/README.md#installation)
- [**LangChain Chat**](./langchain_chat/README.md#installation)
- [**LlamaIndex Chat**](./llamaIndex_chat/README.md#installation)
- [**Simple RAG**](./simple_rag/README.md#installation)
- [**LangChain RAG**](./langchain_rag/README.md#installation)
- [**LlamaIndex RAG**](./llamaIndex_rag/README.md#installation)
- [**Multi-Agent RAG**](./agentic_rag/README.md#installation)

---

## Project Structure
```text
local_chatbots/
├── agentic_rag/app/
│   ├── agents/                     # Multi-agent system
│   │   ├── base_agent.py           # Base agent class
│   │   ├── query_agent.py          # Query enhancement
│   │   ├── retriever_agent.py      # Document retrieval
│   │   ├── router_agent.py         # Query routing
│   │   └── synthesizer_agent.py    # Response generation
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   ├── file_handler.py             # File upload utilities
│   ├── model.py                    # LLM integration
│   └── vector_store.py             # Vector database management
├── langchain_chat/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   └── config.py                   # Configuration settings
├── langchain_rag/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   ├── file_handler.py             # File upload utilities
│   ├── model.py                    # LLM integration
│   └── vector_store.py             # Vector database management
├── llamaIndex_chat/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   └── config.py                   # Configuration settings
├── llamaIndex_rag/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   ├── file_handler.py             # File upload utilities
│   ├── model.py                    # LLM integration
│   └── vector_store.py             # Vector database management
├── ollama_chat/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   └── model.py                    # LLM integration
├── simple_chat/app/
│   ├── static/                     # Static web assets
│   ├── templates/                  # HTML templates
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Configuration settings
│   └── model.py                    # LLM integration
└── simple_rag/app/
    ├── static/                     # Static web assets
    ├── templates/                  # HTML templates
    ├── app.py                      # Main Flask application
    ├── config.py                   # Configuration settings
    ├── file_handler.py             # File upload utilities
    ├── model.py                    # LLM integration
    └── vector_store.py             # Vector database management
```
