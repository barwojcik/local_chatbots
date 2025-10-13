# Multi-Agent RAG (Retrieval-Augmented Generation)


[![Python 3.10.12](https://img.shields.io/badge/python-3.10.12-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange.svg)](https://www.langchain.com/)

An advanced multi-agent RAG (Retrieval-Augmented Generation) chatbot that intelligently decides when to retrieve documents, enhances queries, and provides context-aware answers with citations through an interactive web interface.

## Features

### Core Capabilities
- **🤖 Multi-Agent Architecture**: Specialized agents for routing, query analysis, retrieval, and synthesis
- **📚 Advanced Document Processing**: Semantic chunking with metadata extraction and hierarchical organization
- **🔍 Intelligent Query Routing**: Automatically determines when document retrieval is needed
- **🎯 Hybrid Search**: Combines semantic and keyword-based retrieval strategies
- **📖 Source Citations**: Responses include references to source documents
- **⚡ Real-time Progress Tracking**: Visual feedback showing agent activities

### Additional Capabilities
- Document upload and processing (PDF support)
- Vector-based document storage with Chroma
- Context-aware LLM responses via Ollama
- Interactive web interface with markdown support
- RESTful API endpoints
- Docker support for easy deployment
- Configurable agent behaviors

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
   cd agentic_agent
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
   docker build -t agentic-rag .
   ```

2. Run the container:
   ```bash
   docker run --name agentic-rag \
       --network host \
       agentic-rag
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
   docker start agentic-rag
   ```

3. Open your web browser and navigate to `http://localhost:5000`

4. Upload documents through the web interface to create the knowledge base

5. Start chatting with the RAG-enhanced model

## Architecture

The application uses a multi-agent system that coordinates specialized AI agents:

### Agent Pipeline

1. **Router Agent** (`agents/router_agent.py`)
   - Analyzes incoming queries
   - Determines if document retrieval is needed
   - Routes to the appropriate processing path

2. **Query Analyzer Agent** (`agents/query_agent.py`)
   - Enhances and reformulates queries
   - Extracts key concepts
   - Generates query variations for better retrieval

3. **Retriever Agent** (`agents/retriever_agent.py`)
   - Executes document retrieval with multiple strategies
   - Performs semantic and hybrid search
   - Re-ranks results for relevance

4. **Synthesizer Agent** (`agents/synthesizer_agent.py`)
   - Generates coherent responses from retrieved context
   - Includes source citations
   - Maintains conversation context

### Document Processing

The system uses advanced document processing with semantic chunking:
- **Semantic Chunking**: Preserves document structure and context
- **Metadata Extraction**: Captures headings, sections, and importance scores
- **Hierarchical Organization**: Maintains document hierarchy
- **Multiple Strategies**: Fixed, semantic, and hierarchical chunking options

## File Structure

```
agentic_rag/
├── agents/                      # Multi-agent system
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   ├── router_agent.py         # Query routing
│   ├── query_agent.py          # Query enhancement
│   ├── retriever_agent.py      # Document retrieval
│   └── synthesizer_agent.py    # Response generation
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── document_processor.py       # Advanced document processing
├── file_handler.py             # File upload utilities
├── model.py                    # LLM integration
├── vector_store.py             # Vector database management
├── static/                     # Static web assets
│   ├── script.js               # Frontend logic
│   └── style.css               # Styling
├── templates/                  # HTML templates
│   └── index.html
├── requirements.txt            # Python dependencies
└── Dockerfile                  # Docker configuration
```

## Configuration

All components are configurable via `config.py`:

## API Endpoints

### Chat
- **POST** `/messages`
  - Send a message to the chatbot
  - Request: `{"userMessage": "your question"}`
  - Response: `{"botResponse": "answer", "agentProgress": [...]}`

- **GET** `/messages`
  - Retrieve chat history
  - Response: `{"status": "success", "messages": [...]}`

### Document Management
- **POST** `/document`
  - Upload PDF documents
  - Content-Type: `multipart/form-data`
  - Response: `{"botResponse": "confirmation message"}`

### System Management
- **GET** `/reset-chat-history`
  - Clear conversation history
  - Response: `{"status": "success", "message": "..."}`

- **GET** `/reset-vector-store`
  - Clear uploaded documents
  - Response: `{"status": "success", "message": "..."}`

### Model Management
- **GET** `/model`
  - Get available models and current model
  - Response: `{"available_models": [...], "current_model": "..."}`

- **POST** `/model`
  - Set active model
  - Request: `{"model": "model_name"}`
  - Response: `{"success": true}`

## How It Works

1. **User sends a message** → Router Agent analyzes the query
2. **Router decides** → Use RAG or direct response?
3. **If RAG needed**:
   - Query Analyzer enhances the query
   - Retriever searches and ranks documents
   - Synthesizer generates response with citations
4. **If direct response**:
   - Synthesizer generates response without retrieval
5. **Progress tracking** → Frontend displays agent activities in real-time

## Advanced Features

### Semantic Chunking
Unlike traditional fixed-size chunking, semantic chunking:
- Preserves paragraph and section boundaries
- Detects and respects document headings
- Maintains logical content flow
- Extracts metadata for better retrieval

### Hybrid Search
Combines multiple retrieval strategies:
- **Semantic Search**: Vector similarity using embeddings
- **Keyword Search**: Term frequency matching
- **Re-ranking**: LLM-based relevance scoring

### Intelligent Routing
The router agent uses LLM reasoning to determine:
- Is this a general knowledge question?
- Does it reference uploaded documents?
- Would document context improve the answer?

### Agent Performance
- Increase `confidence_threshold` in router config for more selective RAG usage
- Adjust `max_results` in retriever config to retrieve more/fewer documents
- Disable `enable_reranking` for faster responses (lower quality)