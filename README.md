# Local LLM Chatbots

A collection of Flask-based applications powered by Large Language Models (LLMs) that run locally on your machine.

## Available Applications

### Chat

#### Simple Chat
- Built using the `transformers` library
- Provides basic conversational capabilities
- Runs completely offline

#### Ollama Chat
- Built using the `ollama` library
- Provides basic conversational capabilities
- Runs completely offline

### RAG (Retrieval-Augmented Generation)

#### Simple RAG 
- Built using `transformers` and `langchain` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

#### LangChain RAG
- Built using `ollama` and `langchain` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

#### LlamaIndex RAG
- Built using `ollama` and `llama_index` libraries
- Enables context-aware responses using document retrieval
- Supports local document processing

#### Multi-Agent RAG
- Built using `ollama` and `langchain` libraries
- Coordinates specialized agents (router, query analyzer, retriever, synthesizer) to decide when to retrieve, refine queries, fetch relevant context, and generate answers
- Supports hybrid retrieval (semantic + keyword) with re-ranking and source citations

## Usage
Each application can be run from its respective directory.
