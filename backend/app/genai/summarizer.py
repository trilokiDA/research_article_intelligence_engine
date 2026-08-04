"""
Summarization module for research articles using Groq LLM with LangChain.
"""

import os
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError
from dotenv import load_dotenv

from .schemas import Response
from .prompts import summarization_prompt, revalidate_prompt

load_dotenv()


class ArticleSummarizer:
    """
    Summarizes research articles using Groq LLM with structured output.
    """

    def __init__(
        self,
        model_name: str = "llama-3.3-70b-versatile",
        temperature: float = 0.0,
        max_retries: int = 3
    ):
        """
        Initialize the summarizer with Groq LLM.

        Args:
            model_name: Groq model to use (default: llama-3.3-70b-versatile)
            temperature: Temperature for generation (default: 0.0 for consistency)
            max_retries: Maximum retries for schema validation failures
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries

        # Initialize LLM
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            api_key=self.api_key
        )

        # Initialize output parser
        self.parser = PydanticOutputParser(pydantic_object=Response)

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert research article analyzer. Follow the instructions carefully and return valid JSON."),
            ("user", "{prompt}\n\n{format_instructions}")
        ])

        # Create the chain
        self.chain = self.prompt_template | self.llm | self.parser

    def summarize(
        self,
        doc_id: str,
        title: str,
        journal: str,
        date: str,
        abstract: str,
        feedback: Optional[str] = None,
        previous_summary: Optional[str] = None,
        previous_claims: Optional[str] = None
    ) -> Response:
        """
        Summarize a research article.

        Args:
            doc_id: Publication ID
            title: Article title
            journal: Journal name
            date: Publication date
            abstract: Article abstract
            feedback: Optional feedback from evaluation (for re-inference)
            previous_summary: Previous summary text (for re-inference)
            previous_claims: Previous claim evaluations (for re-inference)

        Returns:
            Response object with structured article summary

        Raises:
            ValidationError: If schema validation fails after max retries
            Exception: For other errors during processing
        """
        # Format the prompt with article data
        if feedback and previous_summary:
            # Use re-inference prompt with feedback
            from .prompts import reinfer_prompt
            formatted_prompt = reinfer_prompt.format(
                abstract=abstract if abstract else "",
                summary=previous_summary,
                claims=previous_claims or feedback
            )
            # Append the original summarization task instructions
            formatted_prompt += f"\n\n{summarization_prompt.format(doc_id=doc_id, title=title, journal=journal, date=date, abstract=abstract if abstract else '')}"
        else:
            # Standard summarization
            formatted_prompt = summarization_prompt.format(
                doc_id=doc_id,
                title=title,
                journal=journal,
                date=date,
                abstract=abstract if abstract else ""
            )

        # Try summarization with retries for validation errors
        for attempt in range(self.max_retries):
            try:
                result = self.chain.invoke({
                    "prompt": formatted_prompt,
                    "format_instructions": self.parser.get_format_instructions()
                })
                return result

            except ValidationError as e:
                if attempt < self.max_retries - 1:
                    # Retry with error feedback
                    error_json = str(e.json())
                    formatted_prompt += revalidate_prompt.format(error_json=error_json)
                    print(f"Validation error on attempt {attempt + 1}, retrying...")
                else:
                    print(f"Max retries reached. Final validation error: {e}")
                    raise

            except Exception as e:
                print(f"Error during summarization: {e}")
                raise

    def summarize_batch(self, articles: list[Dict[str, Any]]) -> list[Response]:
        """
        Summarize multiple articles.

        Args:
            articles: List of article dictionaries with keys:
                     doc_id, title, journal, date, abstract

        Returns:
            List of Response objects
        """
        results = []
        for article in articles:
            try:
                result = self.summarize(
                    doc_id=article.get("doc_id", ""),
                    title=article.get("title", ""),
                    journal=article.get("journal", ""),
                    date=article.get("date", ""),
                    abstract=article.get("abstract", "")
                )
                results.append(result)
            except Exception as e:
                print(f"Failed to summarize article {article.get('doc_id', 'unknown')}: {e}")
                # Continue with next article

        return results


# Convenience function for single article summarization
def summarize_article(
    doc_id: str,
    title: str,
    journal: str,
    date: str,
    abstract: str,
    model_name: str = "llama-3.3-70b-versatile"
) -> Response:
    """
    Convenience function to summarize a single article.

    Args:
        doc_id: Publication ID
        title: Article title
        journal: Journal name
        date: Publication date
        abstract: Article abstract
        model_name: Groq model to use

    Returns:
        Response object with structured article summary
    """
    summarizer = ArticleSummarizer(model_name=model_name)
    return summarizer.summarize(doc_id, title, journal, date, abstract)


if __name__ == "__main__":
    # Example usage
    sample_article = {
        "doc_id": "TEST001",
        "title": "Effects of Electronic Cigarette Use on Cardiovascular Health",
        "journal": "Journal of Public Health",
        "date": "2024-01-15",
        "abstract": "This study examines the cardiovascular effects of electronic cigarette use in adults who previously smoked traditional cigarettes. We conducted a randomized controlled trial with 200 participants over 12 months. Results indicate that participants who switched to e-cigarettes showed improved cardiovascular markers compared to those who continued smoking, though not reaching the levels of those who quit entirely."
    }

    try:
        result = summarize_article(**sample_article)
        print("Summarization successful!")
        print(f"Title: {result.title}")
        print(f"Subject: {result.subject}")
        print(f"Category: {result.category}")
        print(f"Entities: {result.entity}")
        print(f"Summary: {result.summary}")
        print(f"Sentiment: {result.sentiment}")
    except Exception as e:
        print(f"Error: {e}")
