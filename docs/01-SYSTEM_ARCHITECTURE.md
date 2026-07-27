# System Architecture Documentation
## Tobacco Harm Reduction Research Analysis Platform

**Version:** 1.0  
**Date:** 2026-07-23  
**Project Type:** GenAI-Powered Scientific Literature Analysis

---

## Executive Summary

This system is a multi-stage GenAI pipeline that analyzes scientific research articles related to tobacco harm reduction (THR). It extracts structured metadata, generates leadership-ready summaries with people-first language, and validates factual accuracy through an automated fact-checking loop.

---

## System Overview

### Core Purpose
- **Domain**: Tobacco harm reduction research intelligence
- **Primary Users**: Research teams, policy analysts, leadership
- **Key Value**: Automated extraction and classification of scientific literature with built-in quality assurance

### High-Level Data Flow

```
Scientific Article (Raw Text)
    ↓
[Stage 1: Extraction & Classification]
    ↓
Structured Response (Pydantic Model)
    ↓
[Stage 2: Summary Validation]
    ↓
Factual Evaluation Report
    ↓
[Stage 3: Iterative Refinement] (if needed)
    ↓
Final Validated Output
```

---

## Component Architecture

### 1. Data Models (`schema.py`)

#### **Response Model** - Main Article Analysis
```python
Fields:
- articleID: str          # Publication identifier
- title: str              # Article title
- journal: str            # Publishing journal
- date: str               # Publication date (yyyy-mm-dd)
- abstract: str           # Full abstract text
- entity: List[EntityEnum]         # Topic tags (52 categories)
- subject: SubjectEnum             # Product category (HTP, e-cigarettes, etc.)
- summary: str                     # Plain-language summary (people-first language)
- category: CategoryEnum           # Research type (Clinical, Epidemiology, etc.)
- country: str                     # Study location
- sentiment: SentimentEnum         # Stance on THR (Positive/Negative/Neutral/Mixed)
- industry_affiliation: str        # Industry sponsors
```

**Key Design Decisions:**
- **Strict Enums**: Forces LLM outputs into predefined categories
- **Fallback Logic**: Defaults to 'others'/'n/a' when data is missing
- **People-First Language**: Enforced in summary generation
- **Title-Based Inference**: Handles missing abstracts gracefully

#### **FactualEvaluationResponse Model** - Fact-Checking
```python
ClaimEvaluation:
- claim: str              # Sentence from summary
- label: LabelEnum        # Supported/Contradicted/Not mentioned
- explanation: str        # Reasoning for label
```

**Quality Assurance Strategy:**
- Sentence-level verification
- Explicit evidence requirement (no inference allowed)
- Feedback loop for iterative improvement

---

### 2. Prompt Engineering System

#### **Stage 1: Initial Extraction** (`summarization_prompt`)

**Responsibilities:**
1. Parse XML-formatted article data
2. Extract metadata (title, journal, date, abstract)
3. Classify into predefined enums
4. Generate people-first language summary
5. Handle null/empty abstracts

**Key Features:**
- Structured XML input format
- Explicit enum value constraints
- People-first language guidelines (12+ pattern rules)
- Fallback instructions for missing abstracts

**People-First Language Enforcement:**
```
❌ Wrong: "smokers", "asthmatics", "diabetics"
✅ Right: "participants who smoke", "individuals with asthma"

Pattern: [Person-first noun] + [who/with] + [condition/behavior]
```

#### **Stage 2: Fact-Checking** (`summary_evaluation_prompt`)

**Responsibilities:**
1. Extract individual claims from generated summary
2. Verify each claim against source article
3. Classify relationship: Supported/Contradicted/Not mentioned
4. Provide evidence-based explanations

**Validation Criteria:**
- **Supported**: Explicitly stated or clearly implied
- **Contradicted**: Opposite meaning or conflicting evidence
- **Not mentioned**: Cannot be confirmed or adds new facts

#### **Stage 3: Schema Retry** (`revalidate_prompt`)

**Purpose**: Handle LLM output validation errors
**Trigger**: Pydantic schema validation failure
**Action**: Re-prompt with error details

#### **Stage 4: Iterative Refinement** (`reinfer_prompt`)

**Purpose**: Improve summary based on fact-check feedback
**Trigger**: Claims labeled as "Contradicted" or "Not mentioned"
**Strategy**: Show evaluation results + original abstract → regenerate summary

---

## Process Workflows

### Workflow 1: Article Analysis Pipeline

```
INPUT: Article data (ID, title, journal, date, abstract)
    ↓
STEP 1: Format as XML structure
    ↓
STEP 2: Call LLM with summarization_prompt
    ↓
STEP 3: Parse LLM response → Response model
    ↓
DECISION: Schema valid?
    NO → Apply revalidate_prompt → Retry
    YES → Continue
    ↓
STEP 4: Extract summary sentences
    ↓
STEP 5: Call LLM with summary_evaluation_prompt
    ↓
STEP 6: Parse LLM response → FactualEvaluationResponse
    ↓
DECISION: All claims supported?
    NO → Apply reinfer_prompt → Regenerate summary
    YES → Output final result
    ↓
OUTPUT: Validated Response object
```

### Workflow 2: Batch Processing (Implied)

```
For each article in batch:
    1. Run Article Analysis Pipeline
    2. Store results (database/file)
    3. Aggregate statistics
    4. Generate reports
```

---

## Data Classification System

### Entity Taxonomy (52 Categories)
**Product Categories:** electronic cigarettes, heated tobacco products, IQOS, JUUL, snus, hookah, cigars, nicotine pouches, e-liquids

**Substance-Related:** nicotine, tobacco, marijuana, alcohol, chemicals

**Health Topics:** asthma, cancer, cardiovascular disease, depression, mental health, addiction, cytotoxicity

**Population Segments:** youth, former smokers, current smokers, gender, gender differences

**Behaviors:** vaping, smoking, quitting, dual use, smoking cessation, smoking reduction, smoking initiation

**Policy/Public Health:** public health, harm reduction, tobacco control policies, FDA, health risks, harm perceptions, secondhand smoke

**Study Types:** Population Assessment of Tobacco and Health Study

**Other:** social media, advertising, nicotine replacement therapy, smokeless tobacco

### Research Category Taxonomy (9 Types)
1. **Aerosol Chemistry** - Chemical composition analysis
2. **Preclinical Studies** - Lab/animal studies
3. **Clinical Studies** - Human trials
4. **Behavior Studies** - User behavior research
5. **Epidemiology** - Population-level studies
6. **Case Studies** - Individual case reports
7. **Economic Studies** - Cost/market analysis
8. **Public Health Studies** - Policy and population health
9. **Other** - Uncategorized research

### Subject Taxonomy (5 Types)
1. Heated Tobacco Products (HTP)
2. E-cigarettes
3. Vaping
4. Oral Smokeless
5. Other

### Sentiment Scale (5 Levels)
- **Positive**: Pro-THR stance
- **Negative**: Anti-THR stance
- **Neutral**: Balanced/objective
- **Mixed**: Contains both pro and con views
- **Undefined**: Insufficient information

---

## Quality Assurance Mechanisms

### 1. Schema Enforcement
- Pydantic validation at runtime
- Type checking for all fields
- Enum constraint enforcement
- Custom validators (e.g., entity normalization)

### 2. Fact-Checking Loop
- Automated claim extraction
- Evidence-based verification
- Iterative refinement capability

### 3. Language Guidelines
- People-first language enforcement
- 12+ required patterns
- Emphasis on person before condition

### 4. Fallback Handling
- Graceful degradation for missing abstracts
- Title-based inference when needed
- Default values ('n/a', 'others')

---

## Technical Stack (Inferred)

### Core Technologies
- **Language**: Python 3.x
- **Schema Validation**: Pydantic 2.x
- **LLM Integration**: Likely Claude API (Anthropic) or similar
- **Data Format**: XML for prompts, JSON for outputs

### Likely Additional Components
- **Database**: PostgreSQL/MongoDB for article storage
- **API Framework**: FastAPI/Flask
- **Task Queue**: Celery for batch processing
- **Caching**: Redis for LLM response caching

---

## Design Patterns

### 1. Multi-Stage Validation
- Initial extraction → Schema validation → Fact-checking → Refinement
- Each stage has error recovery

### 2. Structured Output with Pydantic
- Type-safe LLM outputs
- Automatic validation
- Easy serialization

### 3. Few-Shot Prompting (Implied)
- People-first language examples
- Enum selection examples
- Classification guidelines

### 4. Error Recovery Loops
- Schema validation retry
- Fact-check feedback loop
- Progressive refinement

---

## Current Limitations & Assumptions

### Limitations
1. **No Multi-Document Analysis**: Each article processed independently
2. **No Citation Network**: No analysis of article relationships
3. **Static Entity List**: 52 predefined entities (new topics require code changes)
4. **Manual Quality Review**: No automated confidence scoring
5. **No Real-Time Monitoring**: Batch processing only (assumed)

### Assumptions
1. Articles provided in structured format (ID, title, journal, date, abstract)
2. English language only (implied)
3. Single LLM provider (likely Claude)
4. Synchronous processing (implied)

---

## Success Metrics (Inferred)

### Accuracy Metrics
- **Fact-Check Pass Rate**: % of summaries with all claims supported
- **Classification Accuracy**: Human validation vs. LLM predictions
- **People-First Language Compliance**: Automated pattern matching

### Performance Metrics
- **Articles Processed per Hour**: Throughput rate
- **Average Processing Time per Article**: End-to-end latency
- **Schema Validation Failure Rate**: Prompt quality indicator
- **Fact-Check Iteration Count**: Summary quality indicator

### Business Metrics
- **Leadership Summary Usage**: Adoption by stakeholders
- **Research Discovery Efficiency**: Time saved vs. manual review
- **Industry Affiliation Detection Rate**: COI transparency

---

## Next Steps for Advanced Prototype

See companion documents:
- `02-ADVANCED_FEATURES.md` - Proposed enhancements
- `03-TECHNICAL_REQUIREMENTS.md` - Implementation specifications
- `04-IMPLEMENTATION_ROADMAP.md` - Phased development plan
