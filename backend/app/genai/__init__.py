"""
GenAI module for article analysis and summarization.

This module provides LLM-powered analysis of research articles using Groq.
"""

from .summarizer import ArticleSummarizer, summarize_article
from .repository import ArticleRepository
from .pipeline import SummarizationPipeline

__all__ = [
    'ArticleSummarizer',
    'summarize_article',
    'ArticleRepository',
    'SummarizationPipeline',
]
