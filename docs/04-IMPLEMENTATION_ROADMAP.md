# Implementation Roadmap
## Advanced Tobacco Harm Reduction Research Platform v2.0

**Version:** 2.0  
**Date:** 2026-07-23  
**Timeline:** 8 months (4 phases)  
**Team Size:** 5-7 engineers

---

## Project Overview

### Objectives
1. Build advanced prototype with multi-document synthesis, RAG, and citation network
2. Deploy MVP to 20+ beta users within 4 months
3. Scale to 100+ users by month 8
4. Achieve 90%+ user satisfaction (NPS score 4.5+)

### Success Criteria
- **Functionality**: All P1 features operational
- **Performance**: <3s RAG query latency (p95)
- **Quality**: 95%+ fact-check pass rate
- **Adoption**: 100 MAU by month 8

---

## Team Structure

### Core Team
```
1x Tech Lead / Architect
2x Backend Engineers (Python, LLM integration)
1x Frontend Engineer (React, TypeScript)
1x ML Engineer (embeddings, NLP)
1x DevOps / Platform Engineer
1x Product Manager (part-time)
```

### Optional Support
```
1x Data Engineer (for large-scale ingestion)
1x UX Designer (for dashboard design)
Domain Expert (tobacco research - advisory)
```

---

## Phase Breakdown

### Phase 1: Foundation (Months 1-2)
**Goal:** Core infrastructure + migrated v1.0 functionality

#### Sprint 1 (Weeks 1-2): Infrastructure Setup
**Deliverables:**
- [ ] Repository structure (monorepo with backend/frontend/infra)
- [ ] Docker Compose setup for local development
- [ ] PostgreSQL + Redis + Neo4j configured
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] AWS infrastructure (Terraform/CloudFormation)
  - [ ] ECS cluster / EKS setup
  - [ ] RDS PostgreSQL
  - [ ] ElastiCache Redis
  - [ ] S3 buckets
  - [ ] CloudWatch logging
- [ ] Development environment documentation

**Team Focus:**
- DevOps: Infrastructure provisioning
- Backend: Database schema migration
- Frontend: React app scaffold

**Acceptance Criteria:**
- ✅ All developers can run full stack locally
- ✅ CI pipeline runs tests on PR
- ✅ Staging environment deployed

---

#### Sprint 2 (Weeks 3-4): Core API + v1.0 Migration
**Deliverables:**
- [ ] FastAPI app structure
  - [ ] Authentication (OAuth 2.0 + JWT)
  - [ ] User management endpoints
  - [ ] Rate limiting middleware
- [ ] Article analysis endpoints (migrate v1.0)
  - [ ] POST /articles/analyze (with Pydantic Response model)
  - [ ] GET /articles/{id}
  - [ ] GET /articles (with pagination, filters)
- [ ] Celery task queue setup
  - [ ] Article analysis job
  - [ ] Fact-checking job
  - [ ] Schema validation retry logic
- [ ] Claude API integration
  - [ ] Prompt management (from v1.0)
  - [ ] Response parsing
  - [ ] Error handling + retries
  - [ ] Cost tracking

**Team Focus:**
- Backend: API development
- Backend: LLM integration
- DevOps: Queue infrastructure

**Acceptance Criteria:**
- ✅ Can analyze article via API (same quality as v1.0)
- ✅ Fact-checking loop functional
- ✅ Results stored in PostgreSQL
- ✅ Unit tests for core logic (80% coverage)

---

#### Sprint 3 (Weeks 5-6): Basic Frontend + Vector Search
**Deliverables:**
- [ ] React frontend
  - [ ] Authentication pages (login, OAuth callback)
  - [ ] Article list view (table with filters)
  - [ ] Article detail view (show all extracted fields)
  - [ ] Bulk upload interface (CSV/JSON)
- [ ] Vector embedding pipeline
  - [ ] sentence-transformers integration
  - [ ] Batch embedding job (Celery)
  - [ ] pgvector storage
  - [ ] Similarity search endpoint
- [ ] Basic semantic search
  - [ ] POST /search (keyword + semantic)
  - [ ] Hybrid search (BM25 + vector)
  - [ ] Result ranking

**Team Focus:**
- Frontend: UI development
- Backend: Vector search
- ML Engineer: Embedding model selection

**Acceptance Criteria:**
- ✅ Users can login and view articles
- ✅ Semantic search returns relevant results
- ✅ Search latency <2s (p95)

---

#### Sprint 4 (Weeks 7-8): Multi-Document Synthesis
**Deliverables:**
- [ ] Synthesis endpoint: POST /synthesis
  - [ ] Input: List of article IDs or query
  - [ ] Retrieval: Get top-N relevant articles
  - [ ] Synthesis prompt design
    - [ ] Multi-document aggregation
    - [ ] Contradiction detection
    - [ ] Citation generation
  - [ ] Output: Synthesis text + citations + confidence
- [ ] Synthesis UI
  - [ ] Select multiple articles (checkboxes)
  - [ ] View synthesis result
  - [ ] Inline citations (clickable)
  - [ ] Export to PDF

**Team Focus:**
- Backend: Synthesis logic
- Backend: Long-context LLM handling (Claude Opus)
- Frontend: Synthesis UI

**Acceptance Criteria:**
- ✅ Can synthesize 5-10 articles
- ✅ Synthesis includes proper citations
- ✅ Contradictions highlighted
- ✅ Export works

**Phase 1 Milestone: Internal Demo**
- Demonstrate v1.0 parity + synthesis + search to stakeholders

---

### Phase 2: Intelligence Layer (Months 3-4)
**Goal:** RAG Q&A + Citation Network + Dashboards

#### Sprint 5 (Weeks 9-10): Advanced RAG
**Deliverables:**
- [ ] RAG pipeline
  - [ ] Query understanding (entity extraction, intent detection)
  - [ ] Multi-stage retrieval (keyword → semantic → reranking)
  - [ ] Context window optimization (select most relevant passages)
  - [ ] Answer generation with citations
  - [ ] Confidence scoring
- [ ] POST /ask endpoint
  - [ ] Input: Natural language question
  - [ ] Output: Answer + sources + confidence
- [ ] Reranking model integration (optional)
  - [ ] Cohere Rerank API or cross-encoder
- [ ] RAG UI
  - [ ] ChatGPT-style interface
  - [ ] Streaming responses (SSE)
  - [ ] Show sources with snippets

**Team Focus:**
- Backend: RAG pipeline
- ML Engineer: Retrieval tuning
- Frontend: Chat UI

**Acceptance Criteria:**
- ✅ Answers factual questions correctly (manual evaluation on 50 questions)
- ✅ Cites 3-5 relevant sources per answer
- ✅ Query latency <3s (p95)

---

#### Sprint 6 (Weeks 11-12): Citation Network Foundation
**Deliverables:**
- [ ] Citation data ingestion
  - [ ] Scrape/API PubMed for citation links
  - [ ] Parse reference lists from articles
  - [ ] Store in Neo4j (Article nodes, CITES edges)
- [ ] Network analysis endpoints
  - [ ] GET /network/citations/{article_id}
  - [ ] GET /network/authors/{author_name}
  - [ ] Network metrics (centrality, clustering)
- [ ] Graph visualization (frontend)
  - [ ] react-force-graph integration
  - [ ] Interactive nodes (click to view article)
  - [ ] Filter by date range, entity

**Team Focus:**
- Backend: Citation ingestion
- Backend: Neo4j queries
- Frontend: Graph visualization

**Acceptance Criteria:**
- ✅ Citation graph displays for 100+ articles
- ✅ Network metrics calculated correctly
- ✅ Graph interactive and responsive

---

#### Sprint 7 (Weeks 13-14): Interactive Dashboards
**Deliverables:**
- [ ] Executive dashboard
  - [ ] Publication volume over time (line chart)
  - [ ] Sentiment distribution (pie chart)
  - [ ] Top entities (bar chart / word cloud)
  - [ ] Geographic heatmap (if country data available)
  - [ ] Industry affiliation breakdown
- [ ] Deep-dive dashboards
  - [ ] Entity-specific page (e.g., "All IQOS Research")
  - [ ] Sentiment timeline for entity
  - [ ] Related articles table
- [ ] Filter panel (global)
  - [ ] Date range picker
  - [ ] Entity multi-select
  - [ ] Subject, category, sentiment filters
  - [ ] Apply filters across all views

**Team Focus:**
- Frontend: Dashboard development (Recharts / Plotly)
- Backend: Aggregation queries
- Product: Dashboard design

**Acceptance Criteria:**
- ✅ All charts render with real data
- ✅ Filters work correctly
- ✅ Dashboard loads in <2s

---

#### Sprint 8 (Weeks 15-16): Confidence Scoring & Beta Launch
**Deliverables:**
- [ ] Confidence scoring system
  - [ ] Per-field confidence (entity, sentiment, etc.)
  - [ ] Sentence-level confidence in summaries
  - [ ] Aggregate article confidence
  - [ ] Flag low-confidence for review
- [ ] Explainability UI
  - [ ] "Why this classification?" tooltip
  - [ ] Highlight supporting text spans
  - [ ] Show chain-of-thought reasoning
- [ ] Admin panel
  - [ ] User management
  - [ ] System stats (articles processed, LLM costs)
  - [ ] Manual review queue (low-confidence items)
- [ ] Beta user onboarding
  - [ ] User documentation
  - [ ] Tutorial videos
  - [ ] Feedback mechanism

**Team Focus:**
- Backend: Confidence scoring
- Frontend: Admin panel + explainability
- Product: Onboarding materials

**Acceptance Criteria:**
- ✅ Confidence scores calibrated (90%+ accuracy)
- ✅ Admin panel functional
- ✅ Documentation complete

**Phase 2 Milestone: Beta Launch**
- Launch to 20 internal/trusted users
- Collect feedback for 2 weeks

---

### Phase 3: Collaboration & Automation (Months 5-6)
**Goal:** Multi-user features + Live monitoring + Literature review generator

#### Sprint 9 (Weeks 17-18): Multi-User Collaboration
**Deliverables:**
- [ ] Workspaces
  - [ ] Create/edit/delete workspace
  - [ ] Add/remove members with roles (owner, editor, viewer)
  - [ ] Add articles to workspace
- [ ] Annotations
  - [ ] Highlight text in article
  - [ ] Add comments
  - [ ] Tag colleagues (@mention)
  - [ ] Threaded discussions
- [ ] Notifications
  - [ ] Email notifications (mentions, replies)
  - [ ] In-app notification center
  - [ ] WebSocket for real-time updates

**Team Focus:**
- Backend: Workspace + annotation APIs
- Frontend: Collaboration UI
- DevOps: WebSocket infrastructure

**Acceptance Criteria:**
- ✅ Users can create workspaces and invite others
- ✅ Annotations visible to workspace members
- ✅ Real-time updates work

---

#### Sprint 10 (Weeks 19-20): Live Publication Monitoring
**Deliverables:**
- [ ] Publication ingestion pipeline
  - [ ] PubMed E-utilities API integration
  - [ ] Scheduled jobs (daily/weekly)
  - [ ] Deduplication logic
  - [ ] Auto-analysis on new articles
- [ ] Alert system
  - [ ] User-defined alert rules (e.g., "Notify on new IQOS studies")
  - [ ] Email/Slack notifications
  - [ ] Alert dashboard
- [ ] Trend detection
  - [ ] Topic modeling (BERTopic)
  - [ ] Emerging topic alerts
  - [ ] Sentiment shift detection

**Team Focus:**
- Backend: Ingestion pipeline
- ML Engineer: Topic modeling
- Backend: Alert engine

**Acceptance Criteria:**
- ✅ New PubMed articles ingested daily
- ✅ Alerts trigger correctly
- ✅ Emerging topics identified

---

#### Sprint 11 (Weeks 21-22): Literature Review Generator
**Deliverables:**
- [ ] Review generation endpoint: POST /reviews/generate
  - [ ] Input: Research question, date range, filters
  - [ ] Retrieval: Relevant articles
  - [ ] Generation: Structured review
    - [ ] Introduction
    - [ ] Methods comparison
    - [ ] Findings synthesis
    - [ ] Contradictions/gaps
    - [ ] Conclusion
  - [ ] Output: Markdown/DOCX with citations
- [ ] Review templates
  - [ ] Systematic review
  - [ ] Narrative review
  - [ ] Executive summary
- [ ] Review UI
  - [ ] Input form (question, filters)
  - [ ] Progress indicator (async generation)
  - [ ] View/edit generated review
  - [ ] Export to DOCX/PDF

**Team Focus:**
- Backend: Review generation logic
- Backend: Long-context handling (Claude Opus 200K)
- Frontend: Review builder UI

**Acceptance Criteria:**
- ✅ Generates coherent 5-page review
- ✅ All claims cited
- ✅ Export works

---

#### Sprint 12 (Weeks 23-24): API & Integrations
**Deliverables:**
- [ ] Public API
  - [ ] API key management
  - [ ] Rate limiting (per key)
  - [ ] OpenAPI documentation (Swagger UI)
  - [ ] API usage dashboard
- [ ] Export formats
  - [ ] CSV, JSON, Excel (articles)
  - [ ] BibTeX, RIS, EndNote XML (citations)
  - [ ] PDF reports (branded templates)
- [ ] Third-party integrations
  - [ ] Zotero API (export collections)
  - [ ] Slack webhook (notifications)
  - [ ] Zapier connector (optional)

**Team Focus:**
- Backend: API development
- Backend: Export logic
- DevOps: API gateway setup

**Acceptance Criteria:**
- ✅ API documented and testable
- ✅ Export works for all formats
- ✅ Slack integration functional

**Phase 3 Milestone: Feature Complete (Core)**
- All P1 & P2 features operational
- Expand to 50 beta users

---

### Phase 4: Advanced Features & Scale (Months 7-8)
**Goal:** Advanced analytics + Performance optimization + Public launch

#### Sprint 13 (Weeks 25-26): Methodology Extraction
**Deliverables:**
- [ ] Study design classifier
  - [ ] NER for methodology terms (RCT, observational, cross-sectional)
  - [ ] Sample size extraction
  - [ ] Study duration extraction
- [ ] Methodology comparison tool
  - [ ] Side-by-side comparison UI
  - [ ] Highlight differences
  - [ ] Quality checklist (CONSORT, STROBE)

**Team Focus:**
- ML Engineer: NER model fine-tuning
- Backend: Extraction pipeline
- Frontend: Comparison UI

**Acceptance Criteria:**
- ✅ Extracts methodology correctly (80%+ accuracy)
- ✅ Comparison tool useful for analysts

---

#### Sprint 14 (Weeks 27-28): Performance Optimization
**Deliverables:**
- [ ] Query optimization
  - [ ] Database index tuning
  - [ ] Slow query analysis (pg_stat_statements)
  - [ ] Caching layer (Redis for common queries)
- [ ] LLM cost optimization
  - [ ] Prompt caching (hash-based)
  - [ ] Model tiering (use Haiku where possible)
  - [ ] Batch processing optimization
- [ ] Frontend performance
  - [ ] Code splitting
  - [ ] Lazy loading
  - [ ] CDN for static assets
- [ ] Load testing
  - [ ] Simulate 100 concurrent users
  - [ ] Identify bottlenecks
  - [ ] Auto-scaling tuning

**Team Focus:**
- Backend: Query optimization
- Backend: LLM cost reduction
- Frontend: Performance tuning
- DevOps: Load testing

**Acceptance Criteria:**
- ✅ Query latency <1s (p95)
- ✅ LLM costs reduced by 30%+
- ✅ Frontend load time <2s
- ✅ System stable under load

---

#### Sprint 15 (Weeks 29-30): Predictive Analytics
**Deliverables:**
- [ ] Trend forecasting
  - [ ] Time-series models (ARIMA, Prophet)
  - [ ] Predict publication volume by topic
  - [ ] Identify declining research areas
- [ ] Sentiment trajectory
  - [ ] Sentiment over time charts
  - [ ] Predict sentiment inflection points
- [ ] Gap analysis dashboard
  - [ ] Under-researched topics
  - [ ] Methodological gaps
  - [ ] Suggested research priorities

**Team Focus:**
- ML Engineer: Time-series modeling
- Backend: Forecasting endpoints
- Frontend: Predictive analytics dashboard

**Acceptance Criteria:**
- ✅ Forecasts directionally accurate (manual validation)
- ✅ Gap analysis actionable

---

#### Sprint 16 (Weeks 31-32): Public Launch Prep
**Deliverables:**
- [ ] Security audit
  - [ ] Penetration testing
  - [ ] OWASP Top 10 review
  - [ ] Fix critical vulnerabilities
- [ ] Compliance
  - [ ] Privacy policy, Terms of Service
  - [ ] GDPR compliance (data export, deletion)
  - [ ] Cookie consent (if applicable)
- [ ] Marketing materials
  - [ ] Landing page
  - [ ] Demo video
  - [ ] Case studies
- [ ] Launch plan
  - [ ] Phased rollout (10 → 50 → 100 users)
  - [ ] Support plan (help desk, documentation)
  - [ ] Monitoring & on-call rotation

**Team Focus:**
- DevOps: Security audit
- Product: Marketing materials
- All: Bug fixing, polish

**Acceptance Criteria:**
- ✅ No critical security issues
- ✅ Legal docs in place
- ✅ Ready for public traffic

**Phase 4 Milestone: Public Launch**
- Open to 100+ users
- Press release / blog post
- Monitor for issues

---

## Post-Launch (Months 9+)

### Ongoing Maintenance
- [ ] Bug fixing (prioritize by severity)
- [ ] User support (help desk, tutorials)
- [ ] Monitoring & alerting

### Iteration Based on Feedback
- [ ] Weekly user feedback review
- [ ] Prioritize new features
- [ ] A/B testing for UX improvements

### Potential Future Features (Post-Launch)
- [ ] Multilingual support (translate articles)
- [ ] Biomarker & outcome extraction
- [ ] Regulatory intelligence module
- [ ] Mobile app (React Native)
- [ ] White-label version for clients

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API downtime | Medium | High | Implement retry logic, fallback models, cache responses |
| Database performance issues | Medium | Medium | Query optimization, read replicas, caching |
| Vector search accuracy low | Medium | High | Hybrid search (semantic + keyword), reranking, fine-tuning |
| Citation data incomplete | High | Medium | Fallback to manual entry, multiple data sources (Crossref, OpenAlex) |
| Graph rendering slow (1000+ nodes) | Medium | Low | Pagination, sub-graph views, WebGL rendering |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Feature creep | High | High | Strict scope control, prioritize P1 features |
| Key engineer leaves | Low | High | Knowledge sharing, documentation, backup |
| Dependencies delayed | Medium | Medium | Buffer time in schedule, parallel work streams |
| Beta user feedback requires major changes | Medium | High | Early feedback (sprint 8), iterate quickly |

### Budget Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM costs exceed budget | Medium | Medium | Prompt caching, model tiering, usage alerts |
| Cloud costs spike | Low | Medium | Auto-scaling limits, cost monitoring, reserved instances |
| Scope increases budget | High | High | Change control process, approve budget increases upfront |

---

## Budget Estimate

### Personnel (8 months)
```
Tech Lead: $120K/yr → $80K (8 months)
Backend Engineers (2): $200K/yr → $133K
Frontend Engineer: $100K/yr → $67K
ML Engineer: $110K/yr → $73K
DevOps Engineer: $100K/yr → $67K
Product Manager (0.5 FTE): $50K/yr → $33K

Total Personnel: ~$450K
```

### Infrastructure (8 months)
```
AWS/Cloud Services:
- Compute (ECS/EKS): $1,500/month → $12K
- RDS PostgreSQL: $500/month → $4K
- Redis: $200/month → $1.6K
- S3, CloudWatch: $200/month → $1.6K

LLM APIs (Claude):
- Development: $500/month → $4K
- Production: $2,000/month (months 5-8) → $8K

Vector Database (Pinecone):
- $140/month → $1.1K

Total Infrastructure: ~$32K
```

### Third-Party Services
```
- OAuth providers: Free (Google, Microsoft)
- Monitoring (DataDog/New Relic): $200/month → $1.6K
- Email service (SendGrid): $100/month → $800
- Slack/communication: $100/month → $800
- Design tools (Figma): $45/month → $360

Total Third-Party: ~$3.6K
```

### Contingency (20%)
```
$97K
```

### **Total Budget: ~$582K**

---

## Success Metrics

### Phase 1 (Month 2)
- ✅ v1.0 feature parity achieved
- ✅ Multi-document synthesis working
- ✅ 5+ internal users testing

### Phase 2 (Month 4)
- ✅ 20 beta users onboarded
- ✅ RAG answering questions correctly (80%+ accuracy)
- ✅ Citation network visualized
- ✅ Dashboards used weekly by users

### Phase 3 (Month 6)
- ✅ 50 active users
- ✅ Collaboration features adopted (10+ workspaces created)
- ✅ Literature reviews generated (5+ per week)
- ✅ Live monitoring detecting new articles

### Phase 4 (Month 8)
- ✅ 100 active users
- ✅ NPS score 4.5+ (user satisfaction)
- ✅ 95%+ fact-check pass rate
- ✅ System stable (99.9% uptime)
- ✅ LLM costs within budget (<$2K/month)

---

## Communication Plan

### Weekly Standups
- **When:** Monday, Wednesday, Friday (30 min)
- **Who:** Engineering team
- **Agenda:** Progress, blockers, next steps

### Sprint Planning (Bi-Weekly)
- **When:** Start of sprint (2 hours)
- **Who:** Full team + PM
- **Agenda:** Review backlog, commit to sprint goals

### Sprint Review (Bi-Weekly)
- **When:** End of sprint (1 hour)
- **Who:** Team + stakeholders
- **Agenda:** Demo completed features, gather feedback

### Monthly Stakeholder Update
- **When:** Last Friday of month (1 hour)
- **Who:** Team leads + stakeholders
- **Agenda:** Progress report, risks, budget status

---

## Go-Live Checklist

### Pre-Launch (1 week before)
- [ ] All P1 features complete and tested
- [ ] Security audit passed
- [ ] Load testing passed
- [ ] Documentation complete (user guides, API docs)
- [ ] Terms of Service, Privacy Policy live
- [ ] Support plan in place (email, Slack channel)
- [ ] Monitoring & alerting configured
- [ ] Backup & disaster recovery tested
- [ ] Rollback plan documented

### Launch Day
- [ ] Deploy to production (blue-green)
- [ ] Run smoke tests
- [ ] Monitor dashboards (errors, latency, costs)
- [ ] Send launch announcement (email, blog, social media)
- [ ] Be available for on-call support

### Post-Launch (1 week after)
- [ ] Daily check-ins on stability
- [ ] Address critical bugs within 24 hours
- [ ] Collect user feedback
- [ ] Review metrics (usage, errors, costs)
- [ ] Post-mortem meeting (what went well, what didn't)

---

## Next Actions

1. **Review Documentation**: Share with stakeholders for feedback
2. **Finalize Scope**: Lock in P1 features for MVP
3. **Team Staffing**: Hire/assign engineers
4. **Kickoff Meeting**: Align team on vision and roadmap
5. **Sprint 1 Start**: Provision infrastructure

**Target Kickoff Date:** 2 weeks from approval

---

## Appendix: Repository Structure

```
tobacco-research-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── articles.py
│   │   │   │   ├── search.py
│   │   │   │   ├── synthesis.py
│   │   │   │   ├── rag.py
│   │   │   │   ├── network.py
│   │   │   │   └── auth.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── article.py
│   │   │   ├── user.py
│   │   │   └── workspace.py
│   │   ├── schemas/
│   │   │   ├── schema.py (from v1.0)
│   │   │   ├── response.py
│   │   │   └── request.py
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   ├── rag.py
│   │   │   ├── synthesis.py
│   │   │   └── citation.py
│   │   ├── db/
│   │   │   ├── postgres.py
│   │   │   ├── neo4j.py
│   │   │   └── redis.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py
│   │   │   ├── analysis.py
│   │   │   └── ingestion.py
│   │   └── main.py
│   ├── tests/
│   ├── alembic/ (database migrations)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── infra/
│   ├── terraform/ (or cloudformation)
│   ├── k8s/
│   └── docker-compose.yml
├── docs/
│   ├── 01-SYSTEM_ARCHITECTURE.md
│   ├── 02-ADVANCED_FEATURES.md
│   ├── 03-TECHNICAL_REQUIREMENTS.md
│   ├── 04-IMPLEMENTATION_ROADMAP.md
│   └── API.md
├── scripts/
│   ├── seed_database.py
│   ├── run_migration.sh
│   └── deploy.sh
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── README.md
└── docker-compose.yml
```
