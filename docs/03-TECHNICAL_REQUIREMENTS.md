# Technical Requirements & System Design
## Advanced Tobacco Harm Reduction Research Platform

**Version:** 2.0  
**Date:** 2026-07-23  
**Target Deployment:** Open Source Stack (Local → Cloud when ready)  
**Philosophy:** Start with SQLite/local tools, upgrade to cloud/PostgreSQL as needed

---

## 🎯 Open Source First Strategy

**Core Principle:** Use 100% open-source technologies with no vendor lock-in.

### Development → Production Path
1. **Phase 1 (Local Dev):** SQLite, local embeddings, Docker Compose
2. **Phase 2 (Small Scale):** PostgreSQL, self-hosted vector DB, single server
3. **Phase 3 (Production):** Kubernetes, distributed databases, auto-scaling

All tools chosen have enterprise-grade free tiers or community editions.

---

## Technical Stack Recommendations

### Backend

#### **Core Application**
```
Language: Python 3.11+
Web Framework: FastAPI 0.110+
Async Runtime: asyncio + uvicorn
Task Queue: Celery + Redis (open source)
```

**Rationale:**
- FastAPI: Modern, fast, auto-generated OpenAPI docs, 100% free
- Async support: Handle concurrent LLM calls efficiently
- Type hints: Pydantic integration for validation
- Celery: Battle-tested async task queue (used by Instagram, Mozilla)

#### **LLM Integration**
```
Primary: Anthropic Claude API (Claude 4.x)
  - Claude Opus 4.8: Complex synthesis, literature reviews
  - Claude Sonnet 4.6: Standard article analysis
  - Claude Haiku 4.5: High-volume fact-checking

SDK: anthropic-sdk 0.31+ (open source SDK)

Open Source Alternatives (Future):
  - LiteLLM: Unified API for multiple providers
  - Ollama: Local LLM hosting (Llama 3, Mistral)
  - LocalAI: OpenAI-compatible local server
```

**Key Capabilities:**
- 200K context window (Claude Opus) for multi-document synthesis
- Structured outputs with Pydantic integration
- Prompt caching (cost optimization)
- Vision support (for figure/table extraction - future)

#### **Data Storage**

**Relational Database: SQLite → PostgreSQL Migration Path**
```
Phase 1 (Development): SQLite 3.45+
  - Zero configuration
  - Single file database
  - Perfect for <100K articles
  - Full-text search (FTS5)
  - JSON support
  - File path: ./data/articles.db

Phase 2 (Production): PostgreSQL 16+ (Open Source)
  - Drop-in replacement (via SQLAlchemy)
  - Extensions:
    - pgvector: Vector embeddings storage
    - pg_trgm: Fuzzy text search
    - pg_stat_statements: Query performance
  - Managed options: Supabase (free tier), Railway, Render
  - Self-hosted: Docker + persistent volume

Migration: Automated via Alembic (schema versioning)
```

**Vector Database: Qdrant (Open Source) or ChromaDB**
```
Primary: Qdrant (https://qdrant.tech)
  - 100% open source (Apache 2.0)
  - Self-hosted or cloud
  - High performance (Rust-based)
  - REST + gRPC APIs
  - Metadata filtering
  - Docker deployment: docker run -p 6333:6333 qdrant/qdrant

Alternative: ChromaDB
  - Python-native
  - Embedded mode (like SQLite for vectors)
  - Great for prototyping

Use Cases:
- Semantic search over abstracts
- RAG retrieval
- Similar article recommendations
- Clustering & topic modeling

Index Strategy:
- Abstract embeddings (384D - all-MiniLM-L6-v2)
- Full-text embeddings (768D - all-mpnet-base-v2)
- Metadata filtering (entity, subject, date range)
```

**Graph Database: Neo4j Community Edition (Open Source)**
```
Neo4j Community Edition (GPLv3)
  - Free forever for single-server deployments
  - Cypher query language
  - Graph algorithms library
  - Docker: docker run -p 7474:7474 -p 7687:7687 neo4j:community

Alternative: Apache AGE (PostgreSQL extension)
  - Adds graph capabilities to PostgreSQL
  - Cypher-compatible
  - No separate database needed

Use Cases:
- Citation network
- Author collaboration network
- Concept co-occurrence graph
- Entity relationships

Node Types:
- Article
- Author
- Entity
- Journal
- Institution

Edge Types:
- CITES
- AUTHORED_BY
- MENTIONS (entity)
- PUBLISHED_IN
- AFFILIATED_WITH
```

**Cache: Redis (Open Source)**
```
Redis 7+ (BSD License)
  - LLM response caching (prompt hash → response)
  - API rate limiting
  - Session management
  - Celery backend
  - Docker: docker run -p 6379:6379 redis:alpine
- Unstructured metadata
- User-generated content (reports, annotations)
```

**Cache: Redis 7+**
```
Use Cases:
- LLM response caching (prompt hash → response)
- API rate limiting
- Session management
- Real-time pub/sub for notifications
```

#### **Task Queue & Background Jobs**
```
Queue: Celery 5.x with Redis backend
Scheduler: Celery Beat for periodic tasks

Job Types:
- Article analysis pipeline
- Batch processing
- Citation network updates
- Publication monitoring (hourly/daily)
- Report generation
- Email digests
```

#### **Search Engine**
```
Option 1: PostgreSQL Full-Text Search (simple deployments)
Option 2: Elasticsearch 8.x (advanced features)

Use Cases:
- Keyword search over titles/abstracts
- Author name search
- Journal name search
- Faceted search (filters)
```

---

### Frontend

#### **Web Application**
```
Framework: React 18+ (TypeScript)
Build Tool: Vite 5+
UI Library: shadcn/ui (Radix UI + Tailwind CSS)
State Management: Zustand / TanStack Query
Routing: React Router v6
```

**Key Libraries:**
- **Visualization**: D3.js, Recharts, Plotly.js
- **Graph Rendering**: react-force-graph (for citation networks)
- **Data Tables**: TanStack Table (formerly React Table)
- **PDF Generation**: react-pdf/renderer
- **Rich Text**: Lexical (for annotations)
- **Forms**: React Hook Form + Zod validation

#### **Architecture Pattern**
```
Pattern: Micro-Frontend (optional for large teams)
- Core App (article browser, search)
- Dashboard Module
- Report Builder Module
- Admin Panel

Bundling: Module Federation or monorepo (Nx/Turborepo)
```

---

### AI/ML Pipeline

#### **Embedding Models**
```
Sentence Transformers (sentence-transformers library)
- all-MiniLM-L6-v2 (384D, fast, 80M params)
- all-mpnet-base-v2 (768D, accurate, 110M params)
- specter2 (768D, scientific papers specialized)

Hosting:
- Self-hosted: Modal, AWS SageMaker
- Managed: Cohere Embed API, OpenAI embeddings
```

#### **Classification Models** (Optional Fine-Tuning)
```
Base Model: BERT-based (PubMedBERT, BioBERT)
Tasks:
- Category classification (9 classes)
- Subject classification (5 classes)
- Sentiment classification (5 classes)

Training Strategy:
- Start with LLM zero-shot
- Collect labeled data (1000+ examples)
- Fine-tune lightweight classifier
- Use classifier for fast batch processing
- LLM for edge cases
```

#### **Entity Recognition**
```
Option 1: LLM-based (current approach)
Option 2: spaCy + custom NER model
  - scispacy models (en_ner_bc5cdr_md)
  - Fine-tune on domain entities

Hybrid Approach:
- spaCy for initial extraction
- LLM for disambiguation and classification
```

#### **Topic Modeling**
```
Library: BERTopic
Use Cases:
- Discover emerging topics
- Cluster similar articles
- Trend detection

Configuration:
- Embedding: sentence-transformers
- Dimensionality reduction: UMAP
- Clustering: HDBSCAN
- Topic representation: KeyBERT + LLM
```

---

### Infrastructure

#### **Deployment Architecture**

**Option A: AWS Cloud**
```
Compute:
- ECS Fargate / EKS (Kubernetes)
- Auto-scaling based on queue depth
- Spot instances for batch jobs

Databases:
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis (cluster mode)
- Neptune (graph database)
- OpenSearch (Elasticsearch alternative)

Storage:
- S3: Article PDFs, generated reports
- EFS: Shared file system for workers

AI Services:
- Bedrock: Claude API access (in-region)
- SageMaker: Custom model hosting

Monitoring:
- CloudWatch: Logs, metrics
- X-Ray: Distributed tracing
- Cost Explorer: Budget alerts
```

**Option B: Azure Cloud**
```
Compute:
- Azure Container Apps / AKS
- Azure Functions (for event-driven tasks)

Databases:
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Cosmos DB (MongoDB API / Gremlin for graph)

Storage:
- Blob Storage: Documents
- Azure Files: Shared storage

AI Services:
- Azure OpenAI Service: Claude alternatives
- Azure Cognitive Search: RAG retrieval

Monitoring:
- Application Insights
- Log Analytics
```

**Option C: GCP Cloud**
```
Compute:
- Cloud Run / GKE
- Cloud Functions

Databases:
- Cloud SQL PostgreSQL
- Memorystore Redis
- Firestore / Datastore

Storage:
- Cloud Storage: Documents

AI Services:
- Vertex AI: Model hosting
- Vertex AI Search: RAG retrieval

Monitoring:
- Cloud Logging
- Cloud Trace
```

#### **Containerization**
```
Base Images:
- python:3.11-slim (API)
- node:20-alpine (Frontend)
- postgres:16-alpine
- redis:7-alpine
- neo4j:5-community

Orchestration:
- Docker Compose (local dev)
- Kubernetes (production)
- Helm charts for deployment
```

---

### API Design

#### **REST API Endpoints**

**Article Management**
```
POST /api/v1/articles/analyze
  - Input: Article data (title, abstract, etc.)
  - Output: Response object (structured analysis)
  - Async: Returns job_id, poll for results

GET /api/v1/articles/{article_id}
  - Output: Full article data + analysis

GET /api/v1/articles
  - Query params: filters (entity, subject, date range, sentiment)
  - Output: Paginated article list

PATCH /api/v1/articles/{article_id}
  - Update article fields (e.g., manual corrections)
```

**Search & RAG**
```
POST /api/v1/search
  - Input: Query string, filters
  - Output: Ranked article list + relevance scores

POST /api/v1/ask
  - Input: Natural language question
  - Output: Answer + cited articles + confidence score

POST /api/v1/synthesis
  - Input: List of article IDs or query
  - Output: Multi-document synthesis with citations
```

**Citation Network**
```
GET /api/v1/network/citations/{article_id}
  - Output: Citation graph (nodes + edges)

GET /api/v1/network/authors/{author_name}
  - Output: Author collaboration network
```

**Reports & Exports**
```
POST /api/v1/reports/generate
  - Input: Template + article IDs
  - Output: Report URL (PDF/DOCX)

GET /api/v1/export
  - Query params: filters + format (json, csv, bibtex)
  - Output: Downloadable file
```

**User & Collaboration**
```
POST /api/v1/annotations
  - Input: Article ID, text selection, comment
  - Output: Annotation object

GET /api/v1/workspaces/{workspace_id}
  - Output: Workspace articles, members, shared notes
```

**Admin**
```
POST /api/v1/admin/ingest
  - Trigger batch ingestion from PubMed

GET /api/v1/admin/stats
  - System metrics (articles processed, LLM costs, etc.)
```

#### **WebSocket Endpoints**
```
WS /ws/jobs/{job_id}
  - Real-time job progress updates

WS /ws/notifications
  - User notifications (mentions, alerts)
```

#### **Authentication**
```
Method: OAuth 2.0 + JWT
Providers: Google, Microsoft, ORCID (for researchers)
Token Expiry: 1 hour (access), 7 days (refresh)
Rate Limiting: 100 req/min per user, 1000 req/hour for API keys
```

---

### Data Models

#### **Article Schema (PostgreSQL)**
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id VARCHAR(255) UNIQUE NOT NULL, -- External ID (PMID, DOI)
    title TEXT NOT NULL,
    journal VARCHAR(500),
    publication_date DATE,
    abstract TEXT,
    full_text TEXT, -- Optional
    
    -- Extracted fields
    entities JSONB, -- Array of EntityEnum values
    subject VARCHAR(100), -- SubjectEnum
    category VARCHAR(100), -- CategoryEnum
    summary TEXT,
    sentiment VARCHAR(50), -- SentimentEnum
    country VARCHAR(100),
    industry_affiliation VARCHAR(500),
    
    -- Metadata
    authors JSONB, -- Array of {name, affiliation}
    doi VARCHAR(255),
    pmid VARCHAR(50),
    pmcid VARCHAR(50),
    keywords JSONB,
    mesh_terms JSONB,
    
    -- Analysis metadata
    confidence_scores JSONB, -- {entity: 0.95, sentiment: 0.78, ...}
    fact_check_status VARCHAR(50), -- passed, failed, pending
    processed_at TIMESTAMP,
    processing_version VARCHAR(50), -- Track model version
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(abstract, '')), 'B')
    ) STORED
);

CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);
CREATE INDEX idx_articles_entities ON articles USING GIN(entities);
CREATE INDEX idx_articles_date ON articles(publication_date DESC);
CREATE INDEX idx_articles_sentiment ON articles(sentiment);
```

#### **Vector Embeddings Schema (PostgreSQL + pgvector)**
```sql
CREATE EXTENSION vector;

CREATE TABLE article_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    embedding_type VARCHAR(50), -- 'abstract', 'full_text', 'summary'
    embedding vector(768), -- Dimension depends on model
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_ivfflat ON article_embeddings 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
```

#### **Citation Network Schema (Neo4j)**
```cypher
// Article node
CREATE CONSTRAINT article_id FOR (a:Article) REQUIRE a.id IS UNIQUE;

// Article properties
(:Article {
    id: "UUID",
    article_id: "PMID/DOI",
    title: "string",
    publication_date: date,
    citation_count: int
})

// Author node
(:Author {
    id: "UUID",
    name: "string",
    orcid: "string",
    h_index: int
})

// Relationships
(:Article)-[:CITES]->(:Article)
(:Author)-[:AUTHORED]->(:Article)
(:Article)-[:MENTIONS {count: int}]->(:Entity)
(:Article)-[:PUBLISHED_IN]->(:Journal)
```

#### **User & Workspace Schema (PostgreSQL)**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50), -- admin, analyst, reviewer, viewer
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50), -- owner, editor, viewer
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE workspace_articles (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    added_by UUID REFERENCES users(id),
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, article_id)
);

CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    workspace_id UUID REFERENCES workspaces(id),
    text_selection JSONB, -- {start, end, selectedText}
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### Security & Compliance

#### **Data Protection**
```
Encryption:
- At Rest: AES-256 (database, S3)
- In Transit: TLS 1.3 (API, database connections)
- Secrets: AWS Secrets Manager / Azure Key Vault

Access Control:
- Row-Level Security (RLS) in PostgreSQL
- IAM roles for service-to-service auth
- API key rotation (90 days)
```

#### **Compliance** (If handling sensitive data)
```
GDPR:
- Data export API
- Right to deletion
- Audit logs for data access

HIPAA: (If articles contain PHI)
- BAA with cloud provider
- Encrypted backups
- Access logs

Research Ethics:
- No personal data from articles
- Public domain data only (PubMed, open access journals)
```

#### **Rate Limiting & DDoS Protection**
```
API Gateway:
- AWS API Gateway / Azure API Management
- 1000 requests/hour per API key
- 10 requests/second burst limit

WAF:
- CloudFlare / AWS WAF
- Block common attack patterns
- IP allowlisting for internal tools
```

---

### Monitoring & Observability

#### **Logging**
```
Structured Logging: JSON format
Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Key Events:
- API requests (method, path, status, latency)
- LLM calls (model, tokens, cost, latency)
- Database queries (slow query log)
- Background jobs (start, success, failure)
- User actions (login, article view, export)

Storage:
- CloudWatch Logs / Azure Log Analytics
- Retention: 30 days (hot), 1 year (archive)
```

#### **Metrics**
```
Application Metrics:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- LLM token usage (tokens/hour)
- LLM cost ($/hour)

Infrastructure Metrics:
- CPU, Memory, Disk usage
- Database connections
- Queue depth (Celery)
- Cache hit rate (Redis)

Business Metrics:
- Articles processed/hour
- Users online
- Reports generated/day
```

#### **Alerting**
```
PagerDuty / Opsgenie integration

Critical Alerts:
- API error rate > 5%
- Database CPU > 80%
- Queue depth > 1000
- LLM API failure

Warning Alerts:
- Response time p95 > 5s
- Disk usage > 70%
- Cost spike (>20% daily increase)
```

#### **Distributed Tracing**
```
Tool: OpenTelemetry + Jaeger / AWS X-Ray

Trace Spans:
- API request → Database query → LLM call → Response
- End-to-end latency breakdown
- Error propagation tracking
```

---

### Cost Optimization

#### **LLM Cost Management**
```
Strategies:
1. Prompt Caching: Cache by (prompt + abstract) hash → 90% cost reduction on re-analysis
2. Model Tiering:
   - Haiku for fact-checking (cheap, fast)
   - Sonnet for standard analysis
   - Opus for multi-doc synthesis
3. Batch Processing: Combine multiple articles in one prompt (up to context limit)
4. Fallback to Fine-Tuned Models: For high-volume classification tasks

Estimated Costs (Claude API):
- Haiku: $0.25 / 1M input tokens, $1.25 / 1M output tokens
- Sonnet: $3 / 1M input tokens, $15 / 1M output tokens
- Opus: $15 / 1M input tokens, $75 / 1M output tokens

Example Article Analysis:
- Input: ~2000 tokens (title + abstract + prompt)
- Output: ~500 tokens (structured response)
- Cost per article (Sonnet): $0.006 + $0.0075 = ~$0.014

For 10,000 articles/month: $140/month in LLM costs
```

#### **Database Cost Management**
```
PostgreSQL:
- Right-size instances (start small, scale up)
- Use read replicas for dashboards
- Archive old articles to cold storage (S3 Glacier)

Vector Database:
- Pinecone: ~$70/month for 1M vectors (starter plan)
- Weaviate self-hosted: Free (but infrastructure cost)
```

#### **Compute Cost Management**
```
- Use spot instances for batch jobs (70% cost savings)
- Auto-scaling: Scale to zero during off-hours
- Right-size containers (don't over-provision)
```

---

### Development & Deployment

#### **Development Workflow**
```
Version Control: Git + GitHub/GitLab
Branching: GitFlow (main, develop, feature/*, hotfix/*)
Code Review: Required for all PRs
CI/CD: GitHub Actions / GitLab CI

Pre-Commit Hooks:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- pytest (unit tests)
```

#### **Testing Strategy**
```
Unit Tests:
- pytest for backend
- Jest for frontend
- Coverage target: 80%+

Integration Tests:
- API endpoint tests (FastAPI TestClient)
- Database migrations (pytest-postgresql)
- LLM mocking (mock API responses)

End-to-End Tests:
- Playwright for frontend workflows
- Critical user journeys (login → search → export)

Load Tests:
- Locust / k6
- Simulate 100 concurrent users
- Target: <2s response time at p95
```

#### **CI/CD Pipeline**
```
On PR:
1. Lint + type check
2. Run unit tests
3. Build Docker images
4. Security scan (Snyk / Trivy)

On Merge to Main:
1. All PR steps
2. Integration tests
3. Deploy to staging
4. Run E2E tests
5. Manual approval
6. Deploy to production
7. Run smoke tests

Rollback Strategy:
- Blue-green deployment
- Automated rollback on health check failure
```

#### **Environment Configuration**
```
Dev:
- SQLite for quick iteration (or local Postgres)
- Mock LLM responses (no API costs)
- Hot reload (FastAPI, Vite)

Staging:
- Identical to production (smaller instances)
- Real database, LLM APIs
- Anonymized production data

Production:
- Full infrastructure
- Auto-scaling enabled
- Real-time monitoring
```

---

## Technology Decision Matrix

| Component | Option 1 | Option 2 | Recommendation | Reason |
|-----------|----------|----------|----------------|--------|
| Backend Framework | FastAPI | Flask | **FastAPI** | Async, auto docs, Pydantic integration |
| LLM Provider | Claude | GPT-4 | **Claude** | Longer context, better for scientific text |
| Vector DB | Pinecone | Weaviate | **Weaviate** | Self-hosted option, lower cost |
| Graph DB | Neo4j | Neptune | **Neo4j** | Better local dev, community edition |
| Frontend | React | Vue | **React** | Larger ecosystem, better libraries |
| Deployment | AWS | Azure | **AWS** | Bedrock for Claude, mature services |

---

## Next Steps

1. **Infrastructure Setup**: Provision cloud resources (see `04-IMPLEMENTATION_ROADMAP.md`)
2. **Repository Setup**: Initialize monorepo with backend/frontend/infra
3. **Database Schema Migration**: Implement PostgreSQL schema
4. **API Skeleton**: Create FastAPI app with core endpoints
5. **Frontend Scaffold**: React app with routing and auth

See implementation plan in next document.
