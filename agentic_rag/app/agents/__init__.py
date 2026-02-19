"""
Agents package for multi-agent RAG system.

This package provides specialized agents for:
- Routing: Determining if RAG retrieval is needed
- Query Analysis: Enhancing and reformulating queries
- Retrieval: Executing document retrieval with multiple strategies
- Synthesis: Generating coherent responses from retrieved context
"""

from .base_agent import BaseAgent
from .query_agent import QueryAnalyzerAgent
from .retriever_agent import RetrieverAgent
from .router_agent import RouterAgent
from .synthesizer_agent import SynthesizerAgent

__all__ = [
    "BaseAgent",
    "RouterAgent",
    "QueryAnalyzerAgent",
    "RetrieverAgent",
    "SynthesizerAgent",
]
