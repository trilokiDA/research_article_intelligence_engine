# Migration Guide: v1.0 → v2.0
## Transitioning from Single-Article Analysis to Advanced Platform

**Version:** 2.0  
**Date:** 2026-07-23  
**Audience:** Development team migrating existing v1.0 code

---

## Overview

This guide helps you migrate the existing v1.0 system (schema.py + prompts) into the v2.0 platform while preserving all functionality and adding new capabilities.

---

## Migration Strategy

### Approach: **Incremental Migration with Parallel Operation**

**Phase 1:** Set up new infrastructure alongside v1.0  
**Phase 2:** Migrate v1.0 logic into v2.0 structure  
**Phase 3:** Add new v2.0 features  
**Phase 4:** Deprecate v1.0

**Benefits:**
- Zero downtime
- Test new system before switching
- Rollback option if issues arise

---

## Step-by-Step Migration

### Step 1: Repository Setup

#### 1.1 Create New Repository Structure
```bash
# Clone or create new repo
git init tobacco-research-platform

# Create directory structure
mkdir -p backend/app/{api/v1,core,models,schemas,services,db,tasks}
mkdir -p frontend/src/{components,pages,hooks,services}
mkdir -p infra/{terraform,k8s}
mkdir -p docs
mkdir -p tests
```

#### 1.2 Copy Existing v1.0 Files
```bash
# Copy schema.py to new location
cp /path/to/old/schema.py backend/app/schemas/schema.py

# Create prompts.py from your prompt strings
cat > backend/app/schemas/prompts.py << 'EOF'
"""Prompt templates from v1.0"""

summarization_prompt = """..."""  # Copy your prompt here
summary_evaluation_prompt = """..."""
revalidate_prompt = """..."""
reinfer_prompt = """..."""
EOF
```

---

### Step 2: Migrate Data Models

#### 2.1 Keep Existing Pydantic Models
Your existing `schema.py` models (Response, FactualEvaluationResponse) will be used as-is. No changes needed for v2.0 compatibility.

**File:** `backend/app/schemas/schema.py` (unchanged from v1.0)

#### 2.2 Add Database ORM Models
Create SQLAlchemy models that mirror your Pydantic schemas.

**File:** `backend/app/models/article.py`
```python
from sqlalchemy import Column, String, Date, Text, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(String(255), unique=True, nullable=False)  # External ID
    title = Column(Text, nullable=False)
    journal = Column(String(500))
    publication_date = Column(Date)
    abstract = Column(Text)
    
    # Extracted fields (from v1.0 Response model)
    entities = Column(JSONB)  # List of EntityEnum values
    subject = Column(String(100))
    category = Column(String(100))
    summary = Column(Text)
    sentiment = Column(String(50))
    country = Column(String(100))
    industry_affiliation = Column(String(500))
    
    # Analysis metadata
    confidence_scores = Column(JSONB)
    fact_check_status = Column(String(50))
    processed_at = Column(DateTime)
    processing_version = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_response_model(self):
        """Convert ORM model to Pydantic Response model (v1.0 compatible)"""
        from app.schemas.schema import Response, EntityEnum, SubjectEnum, CategoryEnum, SentimentEnum
        
        return Response(
            articleID=self.article_id,
            title=self.title,
            journal=self.journal or '',
            date=self.publication_date.isoformat() if self.publication_date else '',
            abstract=self.abstract or '',
            entity=[EntityEnum(e) for e in (self.entities or [])],
            subject=SubjectEnum(self.subject),
            summary=self.summary or '',
            category=CategoryEnum(self.category),
            country=self.country or 'n/a',
            sentiment=SentimentEnum(self.sentiment),
            industry_affiliation=self.industry_affiliation or 'n/a'
        )
```

#### 2.3 Create Database Migration
**File:** `backend/alembic/versions/001_initial_schema.py`
```python
"""Initial schema

Revision ID: 001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('article_id', sa.String(255), unique=True, nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('journal', sa.String(500)),
        sa.Column('publication_date', sa.Date),
        sa.Column('abstract', sa.Text),
        sa.Column('entities', postgresql.JSONB),
        sa.Column('subject', sa.String(100)),
        sa.Column('category', sa.String(100)),
        sa.Column('summary', sa.Text),
        sa.Column('sentiment', sa.String(50)),
        sa.Column('country', sa.String(100)),
        sa.Column('industry_affiliation', sa.String(500)),
        sa.Column('confidence_scores', postgresql.JSONB),
        sa.Column('fact_check_status', sa.String(50)),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('processing_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_articles_date', 'articles', ['publication_date'])
    op.create_index('idx_articles_sentiment', 'articles', ['sentiment'])
    op.execute('CREATE INDEX idx_articles_entities ON articles USING GIN(entities)')

def downgrade():
    op.drop_table('articles')
```

---

### Step 3: Migrate LLM Integration

#### 3.1 Create LLM Service (Abstraction Layer)
**File:** `backend/app/services/llm.py`
```python
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Type, TypeVar, Optional
import json
import hashlib
from app.core.config import settings
from app.db.redis import get_redis

T = TypeVar('T', bound=BaseModel)

class LLMService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.redis = get_redis()
        self.cache_ttl = 3600 * 24 * 7  # 7 days
    
    def _cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key from prompt and model"""
        content = f"{model}:{prompt}"
        return f"llm:cache:{hashlib.sha256(content.encode()).hexdigest()}"
    
    async def call_with_structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
        use_cache: bool = True
    ) -> T:
        """
        Call Claude with structured output (Pydantic model).
        This replaces your v1.0 manual JSON parsing logic.
        """
        # Check cache
        cache_key = self._cache_key(prompt, model) if use_cache else None
        if cache_key:
            cached = await self.redis.get(cache_key)
            if cached:
                return response_model.model_validate_json(cached)
        
        # Call Claude API with structured output
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "name": "provide_structured_output",
                "description": "Provide structured output matching the schema",
                "input_schema": response_model.model_json_schema()
            }],
            tool_choice={"type": "tool", "name": "provide_structured_output"}
        )
        
        # Extract structured output
        tool_use = next((block for block in response.content if block.type == "tool_use"), None)
        if not tool_use:
            raise ValueError("No structured output returned")
        
        result = response_model.model_validate(tool_use.input)
        
        # Cache result
        if cache_key:
            await self.redis.setex(cache_key, self.cache_ttl, result.model_dump_json())
        
        return result
    
    async def call_text(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 2048
    ) -> str:
        """Simple text completion (no structured output)"""
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

llm_service = LLMService()
```

#### 3.2 Migrate Article Analysis Logic
**File:** `backend/app/services/analysis.py`
```python
from app.services.llm import llm_service
from app.schemas.schema import Response, FactualEvaluationResponse, ClaimEvaluation
from app.schemas.prompts import (
    summarization_prompt,
    summary_evaluation_prompt,
    revalidate_prompt,
    reinfer_prompt
)
from pydantic import ValidationError
from typing import Optional
import re

class ArticleAnalysisService:
    """Migrated v1.0 analysis logic"""
    
    async def analyze_article(
        self,
        doc_id: str,
        title: str,
        journal: str,
        date: str,
        abstract: str,
        max_retries: int = 3
    ) -> Response:
        """
        Main analysis function (v1.0 logic).
        Returns validated Response object.
        """
        # Stage 1: Initial extraction
        prompt = summarization_prompt.format(
            doc_id=doc_id,
            title=title,
            journal=journal,
            date=date,
            abstract=abstract
        )
        
        # Retry loop for schema validation
        for attempt in range(max_retries):
            try:
                response = await llm_service.call_with_structured_output(
                    prompt=prompt,
                    response_model=Response,
                    model="claude-sonnet-4-6"
                )
                
                # Stage 2: Fact-checking
                if response.summary:
                    fact_check = await self.fact_check_summary(response.abstract, response.summary)
                    
                    # Stage 3: Iterative refinement (if needed)
                    if self._needs_refinement(fact_check):
                        response = await self._refine_summary(response, fact_check)
                
                return response
                
            except ValidationError as e:
                if attempt < max_retries - 1:
                    # Stage 4: Schema retry
                    error_json = e.json()
                    prompt += "\n\n" + revalidate_prompt.format(error_json=error_json)
                else:
                    raise
        
        raise ValueError("Failed to analyze article after max retries")
    
    async def fact_check_summary(
        self,
        article: str,
        summary: str
    ) -> FactualEvaluationResponse:
        """
        Fact-check generated summary (v1.0 logic).
        """
        # Split summary into sentences
        claims = self._split_sentences(summary)
        
        prompt = summary_evaluation_prompt.format(
            article=article,
            claims="\n".join(f"- {claim}" for claim in claims)
        )
        
        return await llm_service.call_with_structured_output(
            prompt=prompt,
            response_model=FactualEvaluationResponse,
            model="claude-haiku-4-5"  # Use Haiku for cost savings
        )
    
    async def _refine_summary(
        self,
        response: Response,
        fact_check: FactualEvaluationResponse
    ) -> Response:
        """Regenerate summary based on fact-check feedback"""
        prompt = reinfer_prompt.format(
            abstract=response.abstract,
            summary=response.summary,
            claims=self._format_claims(fact_check.claims)
        )
        
        # Re-extract with refinement prompt
        refined_response = await llm_service.call_with_structured_output(
            prompt=prompt,
            response_model=Response,
            model="claude-sonnet-4-6",
            use_cache=False  # Don't cache refinements
        )
        
        # Preserve original metadata, update only summary
        refined_response.articleID = response.articleID
        refined_response.title = response.title
        refined_response.journal = response.journal
        refined_response.date = response.date
        refined_response.abstract = response.abstract
        
        return refined_response
    
    def _needs_refinement(self, fact_check: FactualEvaluationResponse) -> bool:
        """Check if any claims are contradicted or not mentioned"""
        return any(
            claim.label in ["Contradicted", "Not mentioned"]
            for claim in fact_check.claims
        )
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences"""
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    def _format_claims(self, claims: list[ClaimEvaluation]) -> str:
        """Format claims for prompt"""
        return "\n".join(
            f"- {claim.claim} [{claim.label}]: {claim.explanation}"
            for claim in claims
        )

analysis_service = ArticleAnalysisService()
```

---

### Step 4: Create API Endpoints

#### 4.1 Article Analysis Endpoint (v1.0 Compatible)
**File:** `backend/app/api/v1/articles.py`
```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.analysis import analysis_service
from app.models.article import Article
from app.db.postgres import get_db
from app.schemas.schema import Response
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter(prefix="/articles", tags=["articles"])

class AnalyzeRequest(BaseModel):
    article_id: str
    title: str
    journal: str
    date: str
    abstract: str

class AnalyzeResponse(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    result: Optional[Response] = None

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze article (v1.0 logic, now async).
    Returns job ID for async processing.
    """
    # Check if already processed
    existing = db.query(Article).filter(Article.article_id == request.article_id).first()
    if existing:
        return AnalyzeResponse(
            job_id=str(existing.id),
            status="completed",
            result=existing.to_response_model()
        )
    
    # Process in background (for large batches)
    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        _analyze_and_store,
        job_id,
        request.article_id,
        request.title,
        request.journal,
        request.date,
        request.abstract,
        db
    )
    
    return AnalyzeResponse(job_id=job_id, status="processing")

async def _analyze_and_store(
    job_id: str,
    article_id: str,
    title: str,
    journal: str,
    date: str,
    abstract: str,
    db: Session
):
    """Background task for article analysis"""
    try:
        # Call v1.0 analysis service
        result = await analysis_service.analyze_article(
            doc_id=article_id,
            title=title,
            journal=journal,
            date=date,
            abstract=abstract
        )
        
        # Store in database
        article = Article(
            id=job_id,
            article_id=article_id,
            title=title,
            journal=journal,
            publication_date=result.date,
            abstract=abstract,
            entities=[e.value for e in result.entity],
            subject=result.subject.value,
            category=result.category.value,
            summary=result.summary,
            sentiment=result.sentiment.value,
            country=result.country,
            industry_affiliation=result.industry_affiliation,
            processed_at=datetime.utcnow(),
            processing_version="2.0-migrated"
        )
        db.add(article)
        db.commit()
        
    except Exception as e:
        # Log error, update job status
        print(f"Analysis failed for {article_id}: {e}")
        raise

@router.get("/{article_id}", response_model=Response)
async def get_article(article_id: str, db: Session = Depends(get_db)):
    """Retrieve analyzed article (v1.0 compatible response)"""
    article = db.query(Article).filter(Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article.to_response_model()
```

---

### Step 5: Testing Migration

#### 5.1 Unit Tests for v1.0 Logic
**File:** `backend/tests/test_analysis_migration.py`
```python
import pytest
from app.services.analysis import analysis_service
from app.schemas.schema import Response, EntityEnum

@pytest.mark.asyncio
async def test_analyze_article_v1_parity():
    """Test that v2.0 produces same results as v1.0"""
    result = await analysis_service.analyze_article(
        doc_id="PMID12345",
        title="Effects of E-Cigarettes on Youth",
        journal="Tobacco Control",
        date="2024-01-15",
        abstract="This study examines the prevalence of e-cigarette use among adolescents..."
    )
    
    assert isinstance(result, Response)
    assert result.articleID == "PMID12345"
    assert EntityEnum.youth in result.entity
    assert len(result.summary) > 0
    # Add more assertions based on your v1.0 behavior

@pytest.mark.asyncio
async def test_fact_check_logic():
    """Test fact-checking produces valid output"""
    fact_check = await analysis_service.fact_check_summary(
        article="E-cigarettes contain nicotine.",
        summary="E-cigarettes deliver nicotine to users."
    )
    
    assert len(fact_check.claims) > 0
    assert fact_check.claims[0].label in ["Supported", "Contradicted", "Not mentioned"]
```

#### 5.2 Integration Tests
**File:** `backend/tests/test_api_migration.py`
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_endpoint_v1_compatible():
    """Test that API accepts v1.0 input format"""
    response = client.post("/api/v1/articles/analyze", json={
        "article_id": "PMID99999",
        "title": "Test Article",
        "journal": "Test Journal",
        "date": "2024-01-01",
        "abstract": "This is a test abstract about vaping."
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["processing", "completed"]

def test_get_article_returns_v1_schema():
    """Test that GET returns v1.0 Response schema"""
    response = client.get("/api/v1/articles/PMID99999")
    
    assert response.status_code == 200
    data = response.json()
    assert "articleID" in data
    assert "entity" in data
    assert "summary" in data
```

---

### Step 6: Data Migration (If Existing v1.0 Database)

If you have existing analyzed articles in v1.0 format, migrate them:

**File:** `backend/scripts/migrate_v1_data.py`
```python
import json
from app.db.postgres import SessionLocal
from app.models.article import Article

def migrate_v1_json_to_v2():
    """
    Migrate existing v1.0 JSON files to v2.0 database.
    Assumes v1.0 stored results as JSON files.
    """
    db = SessionLocal()
    
    # Load v1.0 data (adjust path)
    with open("/path/to/v1_articles.json") as f:
        v1_articles = json.load(f)
    
    for v1_article in v1_articles:
        # Convert to ORM model
        article = Article(
            article_id=v1_article["articleID"],
            title=v1_article["title"],
            journal=v1_article["journal"],
            publication_date=v1_article["date"],
            abstract=v1_article["abstract"],
            entities=v1_article["entity"],
            subject=v1_article["subject"],
            category=v1_article["category"],
            summary=v1_article["summary"],
            sentiment=v1_article["sentiment"],
            country=v1_article["country"],
            industry_affiliation=v1_article["industry_affiliation"],
            processing_version="1.0-migrated"
        )
        
        db.add(article)
    
    db.commit()
    db.close()
    print(f"Migrated {len(v1_articles)} articles")

if __name__ == "__main__":
    migrate_v1_json_to_v2()
```

---

## Checklist: Migration Complete

- [ ] **Step 1:** Repository structure created
- [ ] **Step 2:** Pydantic models (schema.py) copied
- [ ] **Step 3:** Database ORM models created
- [ ] **Step 4:** LLM service abstraction implemented
- [ ] **Step 5:** Article analysis service migrated
- [ ] **Step 6:** API endpoints created (/articles/analyze, /articles/{id})
- [ ] **Step 7:** Unit tests passing
- [ ] **Step 8:** Integration tests passing
- [ ] **Step 9:** Existing v1.0 data migrated (if applicable)
- [ ] **Step 10:** Docker Compose setup working
- [ ] **Step 11:** CI/CD pipeline configured
- [ ] **Step 12:** Documentation updated

---

## Backward Compatibility

### API Compatibility
All v1.0 endpoints preserved:
- `POST /articles/analyze` - Same input/output schema
- `GET /articles/{id}` - Returns v1.0 Response model

### Code Reuse
- `schema.py` - Used as-is
- `prompts.py` - Extracted into separate file
- Analysis logic - Wrapped in service layer, same behavior

### Data Compatibility
- v1.0 results can be imported to v2.0 database
- v2.0 can export to v1.0 JSON format (for compatibility)

---

## Next Steps After Migration

Once v1.0 logic is running in v2.0 infrastructure:

1. **Add embeddings generation** (Sprint 3)
2. **Build semantic search** (Sprint 3)
3. **Implement multi-document synthesis** (Sprint 4)
4. **Add citation network** (Sprint 6)
5. **Build dashboards** (Sprint 7)

See `04-IMPLEMENTATION_ROADMAP.md` for full schedule.

---

## Troubleshooting

### Issue: Schema validation failing more in v2.0
**Solution:** Claude API's structured output is stricter. Add retry logic with revalidate_prompt.

### Issue: LLM costs higher than expected
**Solution:** Enable prompt caching in LLMService (already implemented).

### Issue: Slow performance vs. v1.0
**Solution:** Use async endpoints, Celery for batch processing, Redis caching.

### Issue: Different results than v1.0
**Solution:** Check prompt formatting (whitespace, XML tags). Claude is sensitive to formatting changes.

---

## Support

For migration issues:
- Review `01-SYSTEM_ARCHITECTURE.md` for v1.0 details
- Check `03-TECHNICAL_REQUIREMENTS.md` for v2.0 architecture
- Contact tech lead or open GitHub issue
