"""
Evaluation module for assessing quality of GenAI summaries.
Provides fact-checking, hallucination detection, and quality scoring.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

from .schemas import (
    EvaluationResult,
    EvaluationMetadata,
    QualityScore,
    ClaimEvaluation,
    LabelEnum,
    FactualEvaluationResponse
)
from .prompts import (
    quality_scoring_prompt,
    hallucination_detection_prompt,
    people_first_check_prompt,
    entity_consistency_check_prompt,
    summary_evaluation_prompt
)

# Load environment variables
load_dotenv()


class SummaryEvaluator:
    """
    Evaluates the quality of generated article summaries.

    Performs:
    - Quality scoring (0-100%)
    - Fact-checking against original abstract
    - Hallucination detection
    - People-first language validation
    - Entity/category consistency checks
    """

    def __init__(
        self,
        model_name: str = "llama-3.3-70b-versatile",
        evaluation_version: str = "v1.0",
        quality_threshold: float = 80.0
    ):
        """
        Initialize the evaluator.

        Args:
            model_name: Groq model to use for evaluation
            evaluation_version: Version identifier for evaluation logic
            quality_threshold: Minimum score to pass (0-100)
        """
        self.model_name = model_name
        self.evaluation_version = evaluation_version
        self.quality_threshold = quality_threshold

        # Initialize LLM
        self.llm = ChatGroq(
            model=model_name,
            temperature=0,  # Deterministic for evaluation
            max_retries=3
        )

    def evaluate(self, raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a raw analysis file from data/analysis/raw/.

        Args:
            raw_analysis: Dictionary loaded from raw/*.json file

        Returns:
            Dictionary with evaluation result and metadata
        """
        start_time = time.time()

        article_id = raw_analysis.get("article_id")
        source_data = raw_analysis.get("source_data", {})
        analysis = raw_analysis.get("analysis", {})

        # Extract required fields
        title = source_data.get("title", "")
        abstract = source_data.get("abstract", "")
        summary = analysis.get("summary", "")
        entities = analysis.get("entity", [])
        subject = analysis.get("subject", "")
        category = analysis.get("category", "")
        sentiment = analysis.get("sentiment", "")

        # Skip evaluation if abstract or summary is empty
        if not abstract or not summary:
            return self._create_empty_evaluation(
                article_id=article_id,
                reason="Empty abstract or summary",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Run evaluations in parallel (conceptually - sequential for now)
        try:
            # 1. Quality scoring
            quality_score = self._evaluate_quality(
                title=title,
                abstract=abstract,
                summary=summary,
                entities=entities,
                subject=subject,
                category=category,
                sentiment=sentiment
            )

            # 2. Hallucination detection
            hallucination_result = self._detect_hallucinations(
                abstract=abstract,
                summary=summary
            )

            # 3. People-first language check
            people_first_result = self._check_people_first_language(summary=summary)

            # 4. Entity consistency check
            entity_result = self._check_entity_consistency(
                abstract=abstract,
                entities=entities
            )

            # 5. Detailed claim evaluation
            claim_evaluations = self._evaluate_claims(
                abstract=abstract,
                summary=summary
            )

            # Calculate overall pass/fail
            passed = quality_score.overall_score >= self.quality_threshold

            # Generate feedback
            feedback = self._generate_feedback(
                quality_score=quality_score,
                hallucination_result=hallucination_result,
                people_first_result=people_first_result,
                entity_result=entity_result,
                claim_evaluations=claim_evaluations
            )

            # Build evaluation result
            evaluation_result = EvaluationResult(
                article_id=article_id,
                quality_score=quality_score,
                hallucination_detected=hallucination_result["hallucination_detected"],
                hallucination_examples=hallucination_result["hallucination_examples"],
                people_first_violations=people_first_result["violations"],
                entity_consistency=entity_result["entity_consistency"],
                entity_issues=entity_result["entity_issues"],
                claim_evaluations=claim_evaluations,
                feedback=feedback,
                passed=passed,
                evaluated_at=datetime.now().isoformat()
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Build metadata
            metadata = EvaluationMetadata(
                evaluator_model=self.model_name,
                evaluation_version=self.evaluation_version,
                processing_time_ms=processing_time_ms,
                tokens_used=0,  # TODO: Extract from Groq response if available
                cost_usd=0.0    # TODO: Calculate based on token usage
            )

            return {
                "evaluation": evaluation_result.model_dump(),
                "metadata": metadata.model_dump()
            }

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"[ERROR] Evaluation failed for {article_id}: {e}")

            return self._create_failed_evaluation(
                article_id=article_id,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    def _evaluate_quality(
        self,
        title: str,
        abstract: str,
        summary: str,
        entities: List[str],
        subject: str,
        category: str,
        sentiment: str
    ) -> QualityScore:
        """
        Evaluate summary quality across multiple dimensions.

        Returns:
            QualityScore with scores for each dimension and overall score
        """
        try:
            prompt = quality_scoring_prompt.format(
                title=title,
                abstract=abstract,
                summary=summary,
                entities=", ".join(entities),
                subject=subject,
                category=category,
                sentiment=sentiment
            )

            # Use structured output for quality scoring
            parser = JsonOutputParser()
            chain = ChatPromptTemplate.from_messages([
                ("system", "You are a quality evaluator. Respond with JSON only."),
                ("user", prompt + "\n\nRespond with JSON: {{\"factual_accuracy\": <0-100>, \"completeness\": <0-100>, \"clarity\": <0-100>, \"people_first_language\": <0-100>}}")
            ]) | self.llm | parser

            result = chain.invoke({})

            # Extract scores
            factual = float(result.get("factual_accuracy", 50))
            completeness = float(result.get("completeness", 50))
            clarity = float(result.get("clarity", 50))
            people_first = float(result.get("people_first_language", 50))

            # Calculate weighted overall score
            overall = (
                factual * 0.4 +
                completeness * 0.3 +
                clarity * 0.2 +
                people_first * 0.1
            )

            return QualityScore(
                factual_accuracy=factual,
                completeness=completeness,
                clarity=clarity,
                people_first_language=people_first,
                overall_score=overall
            )

        except Exception as e:
            print(f"[WARNING] Quality scoring failed: {e}")
            # Return default scores on failure
            return QualityScore(
                factual_accuracy=50.0,
                completeness=50.0,
                clarity=50.0,
                people_first_language=50.0,
                overall_score=50.0
            )

    def _detect_hallucinations(self, abstract: str, summary: str) -> Dict[str, Any]:
        """
        Detect unsupported claims (hallucinations) in the summary.

        Returns:
            Dictionary with hallucination_detected (bool) and hallucination_examples (list)
        """
        try:
            prompt = hallucination_detection_prompt.format(
                abstract=abstract,
                summary=summary
            )

            parser = JsonOutputParser()
            chain = ChatPromptTemplate.from_messages([
                ("system", "You are a fact-checker. Respond with JSON only."),
                ("user", prompt + "\n\nRespond with JSON: {{\"hallucination_detected\": <true/false>, \"hallucination_examples\": [\"example1\", \"example2\"]}}")
            ]) | self.llm | parser

            result = chain.invoke({})

            return {
                "hallucination_detected": result.get("hallucination_detected", False),
                "hallucination_examples": result.get("hallucination_examples", [])
            }

        except Exception as e:
            print(f"[WARNING] Hallucination detection failed: {e}")
            return {
                "hallucination_detected": False,
                "hallucination_examples": []
            }

    def _check_people_first_language(self, summary: str) -> Dict[str, Any]:
        """
        Check adherence to people-first language guidelines.

        Returns:
            Dictionary with violations (list) and score (0-100)
        """
        try:
            prompt = people_first_check_prompt.format(summary=summary)

            parser = JsonOutputParser()
            chain = ChatPromptTemplate.from_messages([
                ("system", "You are a language guidelines checker. Respond with JSON only."),
                ("user", prompt + "\n\nRespond with JSON: {{\"people_first_violations\": [\"violation1\", \"violation2\"], \"people_first_score\": <0-100>}}")
            ]) | self.llm | parser

            result = chain.invoke({})

            return {
                "violations": result.get("people_first_violations", []),
                "score": result.get("people_first_score", 100)
            }

        except Exception as e:
            print(f"[WARNING] People-first language check failed: {e}")
            return {
                "violations": [],
                "score": 100
            }

    def _check_entity_consistency(self, abstract: str, entities: List[str]) -> Dict[str, Any]:
        """
        Check if extracted entities match article content.

        Returns:
            Dictionary with entity_consistency (bool) and entity_issues (list)
        """
        try:
            prompt = entity_consistency_check_prompt.format(
                abstract=abstract,
                entities=", ".join(entities)
            )

            parser = JsonOutputParser()
            chain = ChatPromptTemplate.from_messages([
                ("system", "You are an entity extraction validator. Respond with JSON only."),
                ("user", prompt + "\n\nRespond with JSON: {{\"entity_consistency\": <true/false>, \"entity_issues\": [\"issue1\", \"issue2\"]}}")
            ]) | self.llm | parser

            result = chain.invoke({})

            return {
                "entity_consistency": result.get("entity_consistency", True),
                "entity_issues": result.get("entity_issues", [])
            }

        except Exception as e:
            print(f"[WARNING] Entity consistency check failed: {e}")
            return {
                "entity_consistency": True,
                "entity_issues": []
            }

    def _evaluate_claims(self, abstract: str, summary: str) -> List[ClaimEvaluation]:
        """
        Evaluate each claim in the summary against the abstract.

        Returns:
            List of ClaimEvaluation objects
        """
        try:
            # Break summary into sentences
            sentences = [s.strip() for s in summary.split('.') if s.strip()]

            # Format claims for the prompt
            claims_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])

            prompt = summary_evaluation_prompt.format(
                article=abstract,
                claims=claims_text
            )

            # Use structured output with Pydantic schema
            chain = self.llm.with_structured_output(FactualEvaluationResponse)

            result = chain.invoke(prompt)

            # Convert to ClaimEvaluation list
            return result.claims

        except Exception as e:
            print(f"[WARNING] Claim evaluation failed: {e}")
            # Return empty list on failure
            return []

    def _generate_feedback(
        self,
        quality_score: QualityScore,
        hallucination_result: Dict,
        people_first_result: Dict,
        entity_result: Dict,
        claim_evaluations: List[ClaimEvaluation]
    ) -> str:
        """
        Generate actionable feedback for improvement.

        Returns:
            Feedback string
        """
        feedback_parts = []

        # Quality score feedback
        if quality_score.overall_score < self.quality_threshold:
            feedback_parts.append(f"Overall quality score: {quality_score.overall_score:.1f}/100 (threshold: {self.quality_threshold})")

            if quality_score.factual_accuracy < 70:
                feedback_parts.append(f"- Factual accuracy is low ({quality_score.factual_accuracy:.1f}/100). Ensure all claims are directly supported by the abstract.")

            if quality_score.completeness < 70:
                feedback_parts.append(f"- Completeness is low ({quality_score.completeness:.1f}/100). Include key findings and conclusions from the abstract.")

            if quality_score.clarity < 70:
                feedback_parts.append(f"- Clarity is low ({quality_score.clarity:.1f}/100). Simplify language and improve structure.")

            if quality_score.people_first_language < 70:
                feedback_parts.append(f"- People-first language score is low ({quality_score.people_first_language:.1f}/100). Use 'people who smoke' instead of 'smokers', etc.")

        # Hallucination feedback
        if hallucination_result["hallucination_detected"]:
            feedback_parts.append(f"- Hallucinations detected: {len(hallucination_result['hallucination_examples'])} unsupported claims found.")
            for example in hallucination_result["hallucination_examples"][:3]:  # Show up to 3 examples
                feedback_parts.append(f"  • \"{example}\"")

        # People-first language feedback
        if people_first_result["violations"]:
            feedback_parts.append(f"- People-first language violations: {len(people_first_result['violations'])} found.")
            for violation in people_first_result["violations"][:3]:  # Show up to 3
                feedback_parts.append(f"  • {violation}")

        # Entity consistency feedback
        if not entity_result["entity_consistency"]:
            feedback_parts.append(f"- Entity extraction issues: {len(entity_result['entity_issues'])} found.")
            for issue in entity_result["entity_issues"][:3]:  # Show up to 3
                feedback_parts.append(f"  • {issue}")

        # Claim evaluation feedback
        not_mentioned = [c for c in claim_evaluations if c.label == LabelEnum.not_mentioned]
        contradicted = [c for c in claim_evaluations if c.label == LabelEnum.contradicted]

        if not_mentioned:
            feedback_parts.append(f"- {len(not_mentioned)} claim(s) not supported by abstract:")
            for claim in not_mentioned[:3]:  # Show up to 3
                feedback_parts.append(f"  • \"{claim.claim}\" - {claim.explanation}")

        if contradicted:
            feedback_parts.append(f"- {len(contradicted)} claim(s) contradict the abstract:")
            for claim in contradicted[:3]:  # Show up to 3
                feedback_parts.append(f"  • \"{claim.claim}\" - {claim.explanation}")

        if not feedback_parts:
            return "Summary meets quality standards. No issues found."

        return "\n".join(feedback_parts)

    def _create_empty_evaluation(
        self,
        article_id: str,
        reason: str,
        processing_time_ms: int
    ) -> Dict[str, Any]:
        """
        Create an evaluation result for articles that cannot be evaluated.

        Args:
            article_id: Article identifier
            reason: Reason why evaluation was skipped
            processing_time_ms: Processing time in milliseconds

        Returns:
            Dictionary with empty evaluation result
        """
        evaluation_result = EvaluationResult(
            article_id=article_id,
            quality_score=QualityScore(
                factual_accuracy=0.0,
                completeness=0.0,
                clarity=0.0,
                people_first_language=0.0,
                overall_score=0.0
            ),
            hallucination_detected=False,
            hallucination_examples=[],
            people_first_violations=[],
            entity_consistency=True,
            entity_issues=[],
            claim_evaluations=[],
            feedback=f"Evaluation skipped: {reason}",
            passed=False,
            evaluated_at=datetime.now().isoformat()
        )

        metadata = EvaluationMetadata(
            evaluator_model=self.model_name,
            evaluation_version=self.evaluation_version,
            processing_time_ms=processing_time_ms,
            tokens_used=0,
            cost_usd=0.0
        )

        return {
            "evaluation": evaluation_result.model_dump(),
            "metadata": metadata.model_dump()
        }

    def _create_failed_evaluation(
        self,
        article_id: str,
        error: str,
        processing_time_ms: int
    ) -> Dict[str, Any]:
        """
        Create an evaluation result for failed evaluations.

        Args:
            article_id: Article identifier
            error: Error message
            processing_time_ms: Processing time in milliseconds

        Returns:
            Dictionary with failed evaluation result
        """
        evaluation_result = EvaluationResult(
            article_id=article_id,
            quality_score=QualityScore(
                factual_accuracy=0.0,
                completeness=0.0,
                clarity=0.0,
                people_first_language=0.0,
                overall_score=0.0
            ),
            hallucination_detected=False,
            hallucination_examples=[],
            people_first_violations=[],
            entity_consistency=True,
            entity_issues=[],
            claim_evaluations=[],
            feedback=f"Evaluation failed: {error}",
            passed=False,
            evaluated_at=datetime.now().isoformat()
        )

        metadata = EvaluationMetadata(
            evaluator_model=self.model_name,
            evaluation_version=self.evaluation_version,
            processing_time_ms=processing_time_ms,
            tokens_used=0,
            cost_usd=0.0
        )

        return {
            "evaluation": evaluation_result.model_dump(),
            "metadata": metadata.model_dump(),
            "error": error
        }


if __name__ == "__main__":
    # Test the evaluator
    print("Testing SummaryEvaluator...")

    evaluator = SummaryEvaluator()

    # Test with a sample analysis
    sample_analysis = {
        "article_id": "TEST001",
        "source_data": {
            "title": "Impact of electronic cigarettes on health",
            "abstract": "Electronic cigarettes have been studied for their health impacts. Research shows mixed results on cardiovascular effects.",
        },
        "analysis": {
            "summary": "Smokers of electronic cigarettes show mixed cardiovascular effects.",
            "entity": ["electronic cigarettes"],
            "subject": "E-cigarettes",
            "category": "Clinical Studies",
            "sentiment": "Neutral"
        }
    }

    result = evaluator.evaluate(sample_analysis)

    print(f"\n[OK] Evaluation complete!")
    print(f"     Quality Score: {result['evaluation']['quality_score']['overall_score']:.1f}/100")
    print(f"     Passed: {result['evaluation']['passed']}")
    print(f"     Feedback: {result['evaluation']['feedback'][:100]}...")
    print(f"     Processing Time: {result['metadata']['processing_time_ms']}ms")
