from pydantic import BaseModel, Field, field_validator
from typing import List
from enum import Enum
 
class EntityEnum(str, Enum):
    electronic_cigarettes = 'electronic cigarettes'
    nicotine = 'nicotine'
    smoking_cessation = 'smoking cessation'
    cigarettes = 'cigarettes'
    youth = 'youth'
    vaping = 'vaping'
    smoking = 'smoking'
    snus = 'snus'
    tobacco_products = 'tobacco products'
    smokeless_tobacco = 'smokeless tobacco'
    public_health = 'public health'
    tobacco = 'tobacco'
    cigars = 'cigars'
    harm_reduction = 'harm reduction'
    iqos = 'iqos'
    hookah = 'hookah'
    dual_use = 'dual use'
    heated_tobacco_products = 'heated tobacco products'
    quitting = 'quitting'
    e_liquids = 'e-liquids'
    population_assessment_of_tobacco_and_health_study = 'population assessment of tobacco and health study'
    nicotine_replacement_therapy = 'nicotine replacement therapy'
    asthma = 'asthma'
    marijuana = 'marijuana'
    social_media = 'social media'
    addiction = 'addiction'
    juul = 'juul'
    cytotoxicity = 'cytotoxicity'
    former_smokers = 'former smokers'
    current_smokers = 'current smokers'
    gender = 'gender'
    mental_health = 'mental health'
    tobacco_control_policies = 'tobacco control policies'
    health_risks = 'health risks'
    smoking_reduction = 'smoking reduction'
    secondhand_smoke = 'secondhand smoke'
    cancer = 'cancer'
    depression = 'depression'
    FDA = 'FDA'
    alcohol = 'alcohol'
    harm_perceptions = 'harm perceptions'
    chemicals = 'chemicals'
    nicotine_pouches = 'nicotine pouches'
    smoking_status = 'smoking status'
    advertising = 'advertising'
    gender_differences = 'gender differences'
    smoking_initiation = 'smoking initiation'
    cardiovascular_disease = 'cardiovascular disease'
    ends = 'electronic nicotine delivery systems (ENDS)'
    others = 'others'
 
class CategoryEnum(str, Enum):
    aerosol_chemistry = "Aerosol Chemistry"
    preclinical_studies = "Preclinical Studies"
    clinical_studies = "Clinical Studies"
    behavior_studies = "Behavior Studies"
    epidemiology = "Epidemiology"
    case_studies = "Case Studies"
    economic_studies = "Economic Studies"
    public_health_studies = "Public Health Studies"
    other = "Other"
 
class SentimentEnum(str, Enum):
    positive = "Positive"
    negative = "Negative"
    neutral = "Neutral"
    mixed = "Mixed"
    undefined = "Undefined"
 
class SubjectEnum(str, Enum):
    heated_tobacco_products = "Heated Tobacco Products (HTP)"
    e_cigarettes = "E-cigarettes"
    vaping = "Vaping"
    oral_smokeless = "Oral Smokeless"
    other = "Other"
 
class Response(BaseModel):
    articleID: str = Field(description = "Publication ID of the article as given")
    title: str = Field(description = "Title of the scientific article")
    journal: str = Field(description = "Journal in which the article is published")
    date: str = Field(description = "Publication date of the article as given")
    abstract: str = Field(description = "Abstract text of the article as given")
    entity: List[EntityEnum] = Field(default_factory=lambda: [EntityEnum.others],description = "List of topic entities extracted from the article, mapped to predefined categories in EntityEnum. Prefer matching to an existing categort, only use 'other' if absolutely necessary")
    subject: SubjectEnum = Field(description = "Broad subject of the reasearch article, mapped to predefined categories in SubjectEnum. Prefer matching to an existing categort, only use 'other' if absolutely necessary. If abstract is empty or null, infer from article title.")
    summary: str = Field(description = "A concise, plain-language summary of the article, suitable for leadership review. If abstract is NULL or empty string return empty string only.")
    category: CategoryEnum = Field(description = "Broad research category of the research article, mapped to predefined categories in CategoryEnum. Prefer matching to an existing categort, only use 'other' if absolutely necessary. If abstract is empty or null, infer from article title.")
    country: str = Field(description = "Full official country name of study, or 'n/a' if not specified")
    sentiment: SentimentEnum = Field(description = "Sentiment towards Tobacco Harm Reduction (THR) expressed in the article")
    industry_affiliation: str = Field(description = "Industry affiliation (e.g., PMI, JTI, BAT) if mentioned, 'n/a' if not provided")
 
    @field_validator('entity', mode='before')
    def normalize_entity(cls, v):
        if v is None or (isinstance(v, list) and len(v) == 0) or (isinstance(v, str) and v.strip() == ''):
            return [EntityEnum.others]
        return v
 
class LabelEnum(str, Enum):
    supported = "Supported"
    contradicted = "Contradicted"
    not_mentioned = "Not mentioned"
 
class ClaimEvaluation(BaseModel):
    claim: str = Field(description="Summary sentence or factual claim being evaluated")
    label: LabelEnum = Field(description="Factual relationship between the claim and article")
    explanation: str = Field(
        default="No explanation provided",
        description="Short explanation for the label")
 
class FactualEvaluationResponse(BaseModel):
    article: str = Field(description="Source article in <article> xml tag")
    claims: List[ClaimEvaluation] = Field(description="List of claim evaluation")

class QualityScore(BaseModel):
    """Quality scoring breakdown (0-100 scale)"""
    factual_accuracy: float = Field(ge=0, le=100, description="Accuracy of claims vs source (40% weight)")
    completeness: float = Field(ge=0, le=100, description="Coverage of key findings (30% weight)")
    clarity: float = Field(ge=0, le=100, description="Readability and conciseness (20% weight)")
    people_first_language: float = Field(ge=0, le=100, description="Adherence to people-first language (10% weight)")
    overall_score: float = Field(ge=0, le=100, description="Weighted overall quality score")

class EvaluationResult(BaseModel):
    """Complete evaluation result for a summary"""
    article_id: str = Field(description="Article identifier (e.g., PMID001)")
    quality_score: QualityScore = Field(description="Quality score breakdown")
    hallucination_detected: bool = Field(description="Whether unsupported claims were found")
    hallucination_examples: List[str] = Field(default_factory=list, description="Examples of hallucinated claims")
    people_first_violations: List[str] = Field(default_factory=list, description="People-first language violations")
    entity_consistency: bool = Field(description="Whether entities match article content")
    entity_issues: List[str] = Field(default_factory=list, description="Entity extraction issues")
    claim_evaluations: List[ClaimEvaluation] = Field(description="Detailed claim-by-claim evaluation")
    feedback: str = Field(description="Actionable feedback for improvement")
    passed: bool = Field(description="Whether summary passes quality threshold (>=80%)")
    evaluated_at: str = Field(description="ISO timestamp of evaluation")

class EvaluationMetadata(BaseModel):
    """Metadata for evaluation process"""
    evaluator_model: str = Field(description="Model used for evaluation")
    evaluation_version: str = Field(description="Version of evaluation logic")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    tokens_used: int = Field(default=0, description="Tokens consumed during evaluation")
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")