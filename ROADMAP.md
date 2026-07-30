# Project Roadmap

**Project:** Research Article Intelligence Engine  
**Current Version:** 1.0  
**Last Updated:** 2026-07-30

---

## Overview

This roadmap outlines the evolution from our current basic ingestion + analysis pipeline to a comprehensive research intelligence platform.

---

## Current State (v1.0) ✅

**Status:** Production (July 2026)  
**What Works:**

### Data Ingestion
- ✅ PubMed API integration with topic-based queries
- ✅ Predefined topics (Heat-Not-Burn, E-Cigarettes, Nicotine-Pouch, Snus)
- ✅ Date range filtering
- ✅ Duplicate detection
- ✅ SQLite storage with FTS5 search

### GenAI Analysis
- ✅ File-based pipeline (JSON output)
- ✅ Groq LLM integration (llama-3.3-70b, llama-3.1-8b)
- ✅ Structured output with Pydantic validation
- ✅ Auto-retry on schema errors
- ✅ Smart skip logic (existing JSON files)
- ✅ People-first language enforcement
- ✅ Batch processing with progress tracking

### Data Schema
- ✅ Entity extraction (52 categories)
- ✅ Category classification (9 types)
- ✅ Sentiment analysis (5 levels)
- ✅ Subject tagging (5 subjects)
- ✅ Industry affiliation detection
- ✅ Country extraction

### CLI Tools
- ✅ `ingest_cli.py` - Data ingestion
- ✅ `run_summarization.py` - GenAI analysis
- ✅ `view_data.py` - Results viewing

**Limitations:**
- No quality control gate before storage
- No evaluation/validation pipeline
- No re-inference capability
- Crossref disabled (no abstracts)
- Google Scholar not implemented

---

## In Progress (v1.1) - Q3 2026

**Goal:** Add quality control and iterative refinement

### 1. Evaluation Pipeline 🔄
**Status:** Planned  
**Priority:** P0 (Critical)

**Features:**
- Quality scoring system (0-100%)
- Fact-checking against original abstract
- Hallucination detection
- People-first language validation
- Entity/category consistency checks

**Implementation:**
```
raw/*.json → evaluation → score
   ↓
  >= 80% → approved/*.json
  < 80%  → reinfer with feedback
```

**Deliverables:**
- `backend/app/genai/evaluator.py` - Evaluation logic
- Evaluation prompt templates
- Quality metrics dashboard
- CLI: `python scripts/evaluate_summaries.py`

### 2. Revalidation Workflow 🔄
**Status:** Planned  
**Priority:** P0 (Critical)

**Features:**
- Manual review interface for failed evaluations
- Bulk revalidation of existing summaries
- Version tracking for summaries
- Confidence scoring

**Implementation:**
```
approved/*.json → revalidate → updated version
```

**Deliverables:**
- Revalidation CLI tool
- Version history in JSON files
- Batch revalidation script

### 3. Re-inference (Reinfer) Capability 🔄
**Status:** Planned  
**Priority:** P0 (Critical)

**Features:**
- Iterative refinement loop (max 3 attempts)
- Feedback-driven improvement
- Different model fallback (70b → 8b if still failing)
- Manual review queue for persistent failures

**Implementation:**
```
raw/*.json → evaluate → < 80% → reinfer with feedback → evaluate → ...
```

**File structure:**
```
data/analysis/
├── raw/           # Initial GenAI output
├── evaluated/     # With evaluation scores
├── reinfer/       # Retry attempts (attempt_1, attempt_2, ...)
├── approved/      # Final approved (>= 80%)
└── rejected/      # Failed after max retries (manual review)
```

**Deliverables:**
- `backend/app/genai/reinfer.py` - Reinfer logic
- Reinfer prompt with feedback injection
- CLI: `python scripts/reinfer.py`
- Manifest tracking file

### 4. Enhanced Documentation
- Evaluation pipeline docs
- Revalidation guide
- Reinfer guide
- Quality metrics reference

**Timeline:** 2-3 months (Aug-Oct 2026)

---

## Planned (v2.0) - Q1-Q2 2027

**Goal:** Advanced research intelligence features

### 1. Vector Embeddings & Semantic Search 📊
**Priority:** P1 (High)

**Features:**
- Sentence-transformers embeddings (all-MiniLM-L6-v2)
- ChromaDB/Qdrant vector storage
- Semantic similarity search
- "Find similar articles" functionality
- Topic clustering

**Tech Stack:**
- `sentence-transformers`
- `chromadb` (dev) or `qdrant` (prod)
- `faiss` (optional, for speed)

### 2. RAG Q&A System 🤖
**Priority:** P1 (High)

**Features:**
- Natural language questions across entire corpus
- Context-aware retrieval (top-K similar articles)
- Answer generation with citations
- Confidence scoring
- Multi-document synthesis

**Architecture:**
```
User Question
    ↓
Vector Search (retrieve top-K articles)
    ↓
LLM (generate answer with context)
    ↓
Response with citations
```

### 3. Citation Network Analysis 🕸️
**Priority:** P2 (Medium)

**Features:**
- Extract citations from articles
- Build citation graph (Neo4j)
- Influence scoring (PageRank-style)
- Research lineage tracking
- Author collaboration networks
- Interactive graph visualization

**Tech Stack:**
- `neo4j` (graph database)
- `networkx` (graph analysis)
- `d3.js` or `cytoscape.js` (visualization)

### 4. Multi-Document Synthesis 📝
**Priority:** P2 (Medium)

**Features:**
- Synthesize findings across 5-10 articles
- Contradiction detection
- Evidence aggregation
- Meta-analysis generation
- Consensus/disagreement identification

### 5. FastAPI REST API 🔌
**Priority:** P1 (High)

**Endpoints:**
- `/api/v1/articles` - List, search, filter
- `/api/v1/analysis` - Get analysis results
- `/api/v1/search` - Semantic search
- `/api/v1/qa` - RAG Q&A
- `/api/v1/citations` - Citation network
- `/api/v1/synthesize` - Multi-doc synthesis

### 6. React Frontend (Web UI) 💻
**Priority:** P2 (Medium)

**Features:**
- Article browser with filters
- Search interface (keyword + semantic)
- Analysis dashboard
- Q&A interface
- Citation graph visualization
- Export tools (CSV, JSON, BibTeX)

**Tech Stack:**
- React 18 + TypeScript
- TanStack Query (data fetching)
- Recharts (visualizations)
- Tailwind CSS (styling)

### 7. PostgreSQL Migration 🗄️
**Priority:** P2 (Medium)

**Rationale:**
- Handle >100K articles
- Concurrent writes
- Better performance for complex queries
- Production-ready

**Migration:**
- `SQLAlchemy` ORM
- Alembic for migrations
- Maintain SQLite for development

**Timeline:** 6-8 months (Jan-Aug 2027)

---

## Future (v3.0) - Q3-Q4 2027

**Goal:** Real-time intelligence & collaboration

### 1. Real-Time Monitoring 📡
**Features:**
- Daily PubMed ingestion (cron jobs)
- Topic-based alerts (email/Slack)
- Emerging trend detection
- Sentiment shift tracking
- New publication notifications

**Tech Stack:**
- `Celery` (task queue)
- `Redis` (broker)
- `APScheduler` (scheduling)

### 2. Automated Literature Reviews 📚
**Features:**
- Generate 5-10 page structured reviews
- Customizable templates (systematic, narrative, executive)
- Auto-generated bibliographies
- Export to DOCX/PDF
- Version history

### 3. Collaborative Features 👥
**Features:**
- Multi-user workspaces
- Annotations and comments on articles
- @mentions and threaded discussions
- Shared searches and reports
- Access control (read/write permissions)

**Tech Stack:**
- PostgreSQL (user management)
- JWT authentication
- WebSockets (real-time updates)

### 4. Interactive Dashboards 📊
**Features:**
- Executive overview (publication trends, sentiment)
- Entity-specific analysis
- Geographic heatmaps
- Custom report builder
- Drag-and-drop filters

**Tech Stack:**
- React + Recharts
- Plotly (advanced visualizations)
- Export to PowerPoint/PDF

### 5. Advanced Analytics 📈
**Features:**
- Predictive analytics (future trends)
- Topic modeling (LDA, BERTopic)
- Author reputation scoring
- Journal impact analysis
- Funding source tracking

### 6. API for External Access 🔗
**Features:**
- Public API with rate limiting
- API key management
- Usage analytics
- Webhook support
- SDKs (Python, JavaScript)

### 7. Export Integrations 📤
**Features:**
- Citation managers (Zotero, Mendeley, EndNote)
- Reference export (BibTeX, RIS, EndNote XML)
- Data export (CSV, JSON, Excel)
- Automated reporting (scheduled PDF reports)

**Timeline:** 6 months (Jul-Dec 2027)

---

## Long-Term Vision (v4.0+) - 2028+

### Multilingual Support 🌍
- Support for articles in multiple languages
- Machine translation integration
- Cross-language semantic search

### Regulatory Intelligence 📋
- Track regulatory documents (FDA, WHO, etc.)
- Policy change alerts
- Compliance monitoring

### Mobile Apps 📱
- iOS/Android apps
- Push notifications
- Offline reading mode

### Machine Learning Enhancements 🧠
- Custom fine-tuned models for tobacco research
- Transfer learning from PubMed abstracts
- Active learning for annotation

### Data Partnerships 🤝
- Integration with institutional repositories
- Conference proceedings ingestion
- Preprint server monitoring (bioRxiv, medRxiv)

---

## Technical Debt & Infrastructure

### Immediate (v1.1)
- Add unit tests (pytest)
- Set up CI/CD (GitHub Actions)
- Structured logging (JSON logs)
- Error tracking (Sentry)

### Short-Term (v2.0)
- Docker containers
- Docker Compose for local dev
- Monitoring (Prometheus + Grafana)
- Performance profiling

### Long-Term (v3.0+)
- Kubernetes orchestration
- Multi-region deployment
- CDN for static assets
- Load balancing

---

## Resource Requirements

### v1.1 (Evaluation Pipeline)
- **Team:** 1 ML engineer, 1 backend engineer (2 months)
- **Cost:** $0 (Groq free tier sufficient)
- **Infrastructure:** Current (SQLite + local files)

### v2.0 (Advanced Features)
- **Team:** 2 backend, 1 frontend, 1 ML engineer (6 months)
- **Cost:**
  - VPS: $40-80/month
  - Vector DB: $0 (ChromaDB open source)
  - Claude API: $100-300/month (RAG usage)
- **Infrastructure:** VPS + PostgreSQL + ChromaDB

### v3.0 (Real-Time + Collaboration)
- **Team:** 3 backend, 2 frontend, 1 DevOps (6 months)
- **Cost:**
  - VPS Cluster: $200-400/month
  - Redis: $20-40/month
  - Claude API: $300-500/month
- **Infrastructure:** Multi-node cluster + Redis + job queue

---

## Success Metrics

### v1.1 Metrics
- **Evaluation:** 95%+ of summaries pass 80% threshold
- **Reinfer:** <5% of articles need 3+ attempts
- **Quality:** User-validated accuracy >90%

### v2.0 Metrics
- **RAG Q&A:** 90%+ answer accuracy
- **Performance:** <3s query latency (p95)
- **Scale:** Support 100K+ articles
- **Users:** 50+ active users

### v3.0 Metrics
- **Real-time:** <1 hour latency for new publications
- **Collaboration:** 10+ active workspaces
- **Uptime:** 99.9% availability
- **Growth:** 200+ monthly active users

---

## Decision Points

### When to Move to v2.0?
- ✅ v1.1 evaluation pipeline working
- ✅ 10K+ articles with validated summaries
- ✅ User demand for semantic search
- ✅ Team capacity for 6-month project

### When to Move to PostgreSQL?
- ✅ >100K articles
- ✅ Concurrent write requirements
- ✅ Complex query performance issues
- ✅ Multiple production users

### When to Build UI?
- ✅ FastAPI backend stable
- ✅ 20+ users requesting web interface
- ✅ Frontend developer available
- ✅ Clear UX requirements

---

## Open Questions

### v1.1
- What evaluation threshold? (currently proposed: 80%)
- How many reinfer attempts? (currently: 3)
- Manual review workflow?

### v2.0
- Which vector DB? ChromaDB (simple) vs Qdrant (scalable)
- RAG model? Continue with Groq or switch to Claude?
- Citation extraction? Rule-based or ML?

### v3.0
- Authentication system? Self-hosted vs OAuth
- WebSocket vs polling for real-time?
- Hosting? Self-hosted vs managed Kubernetes

---

## Contributing

Want to help? Check out:
- **v1.1 Issues:** Evaluation, revalidation, reinfer
- **v2.0 Issues:** RAG, vector search, citation networks
- **Documentation:** Help improve guides and references

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions.

---

**Current Focus:** v1.1 - Evaluation Pipeline  
**Next Milestone:** Evaluation + Revalidation + Reinfer (Q3 2026)

For detailed implementation plans, see:
- [docs/FUTURE_PIPELINE_PROPOSAL.md](docs/FUTURE_PIPELINE_PROPOSAL.md) - v1.1 architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - Current system design
- [README.md](README.md) - Getting started
