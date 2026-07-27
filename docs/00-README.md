# Advanced Tobacco Harm Reduction Research Platform
## Project Documentation Overview

**Project Name:** Tobacco Harm Reduction Research Intelligence Platform v2.0  
**Domain:** Scientific Literature Analysis (GenAI-Powered)  
**Status:** Planning Phase  
**Created:** 2026-07-23

---

## 📋 Executive Summary

This project is an **advanced GenAI prototype** that builds upon an existing tobacco harm reduction research analysis system. The current v1.0 system analyzes individual scientific articles using LLMs (Claude API) to extract structured metadata, generate summaries with people-first language, and validate factual accuracy.

**v2.0 Goals:**
- Add **multi-document synthesis** and comparative analysis
- Implement **advanced RAG (Retrieval-Augmented Generation)** for Q&A across entire corpus
- Build **citation network analysis** for research influence tracking
- Create **interactive dashboards** for leadership insights
- Enable **real-time publication monitoring** and alerting
- Support **multi-user collaboration** with annotations and workspaces
- Generate **automated literature reviews**

**Expected Outcomes:**
- 3x increase in research coverage
- 80%+ time savings vs. manual review
- 100+ active users by month 8
- 95%+ fact-check accuracy maintained

---

## 📁 Documentation Structure

### 1. **[System Architecture](./01-SYSTEM_ARCHITECTURE.md)** (READ FIRST)
**Purpose:** Understand the existing v1.0 system

**Contents:**
- Current system overview and data flow
- Pydantic data models (Response, FactualEvaluationResponse)
- Prompt engineering system (4 stages: extract → validate → fact-check → refine)
- Classification taxonomies (52 entities, 9 categories, 5 subjects, 5 sentiments)
- Quality assurance mechanisms
- Current limitations and assumptions

**Read this if you need to:**
- Understand what already exists
- See the data models and enums
- Learn the v1.0 prompt strategies
- Identify gaps that v2.0 will address

---

### 2. **[Advanced Features Specification](./02-ADVANCED_FEATURES.md)**
**Purpose:** Define what v2.0 will add

**Contents:**
- 16 advanced features across 7 priority tiers:
  - **P1 (Critical):** Multi-doc synthesis, RAG, citation network
  - **P2 (High):** Live monitoring, dashboards, confidence scoring
  - **P3 (Medium):** Collaboration, API, literature review generator
  - **P4 (Nice-to-Have):** Methodology extraction, multilingual, regulatory intelligence
- User personas and use cases
- Success metrics per phase
- Feature prioritization matrix

**Read this if you need to:**
- Understand the product vision
- Prioritize features for MVP
- Design user experiences
- Estimate scope and complexity

---

### 3. **[Technical Requirements](./03-TECHNICAL_REQUIREMENTS.md)**
**Purpose:** Define how to build v2.0

**Contents:**
- **Tech stack recommendations:**
  - Backend: FastAPI, Python 3.11+, Celery, Claude API (Opus/Sonnet/Haiku)
  - Databases: PostgreSQL (pgvector), Neo4j, Redis, Pinecone/Weaviate
  - Frontend: React 18, TypeScript, shadcn/ui, D3.js
  - Infrastructure: AWS (ECS, RDS, S3, CloudWatch) or Azure/GCP alternatives
- **Data models:** SQL schemas, vector embeddings, graph database schema
- **API design:** 30+ REST endpoints, WebSocket for real-time
- **Security & compliance:** Encryption, GDPR, rate limiting
- **Cost optimization:** LLM caching, model tiering, ~$140/month for 10K articles
- **Development workflow:** CI/CD, testing strategy, deployment

**Read this if you need to:**
- Make technology decisions
- Design database schemas
- Estimate infrastructure costs
- Plan DevOps and deployment
- Write code / APIs

---

### 4. **[Implementation Roadmap](./04-IMPLEMENTATION_ROADMAP.md)**
**Purpose:** Plan the 8-month build

**Contents:**
- **4 phases, 16 sprints (2 weeks each):**
  - **Phase 1 (Months 1-2):** Foundation + v1.0 migration
  - **Phase 2 (Months 3-4):** RAG + citation network + dashboards
  - **Phase 3 (Months 5-6):** Collaboration + live monitoring + lit review generator
  - **Phase 4 (Months 7-8):** Advanced analytics + optimization + launch
- **Team structure:** 5-7 engineers (Tech Lead, 2 Backend, Frontend, ML, DevOps)
- **Budget estimate:** ~$582K (personnel + infrastructure + contingency)
- **Risk management:** Technical, schedule, and budget risks + mitigations
- **Success metrics:** Milestones per phase (20 users → 50 users → 100 users)
- **Go-live checklist:** Pre-launch, launch day, post-launch tasks

**Read this if you need to:**
- Understand the build timeline
- Staff the team
- Allocate budget
- Track progress against milestones
- Identify risks and dependencies

---

### 5. **[Data Ingestion Pipeline](./05-DATA_INGESTION_PIPELINE.md)** ⭐ NEW
**Purpose:** Understand how articles are collected from external sources

**Contents:**
- **Two-stage pipeline:** Data Engineer (ingestion) → GenAI (analysis)
- **Data sources:** PubMed, Crossref, Google Scholar (all FREE APIs)
- **v1.0 DocumentDB schema:** 29 columns mapped to v2.0 SQL schema
- **Source connectors:** Python code for PubMed, Crossref, Scholar scraping
- **Data normalization:** Unified schema across sources
- **Migration script:** DocumentDB → SQLite converter
- **Rate limiting & best practices**

**Read this if you need to:**
- Understand the existing DocumentDB structure
- Build data ingestion connectors
- Migrate from DocumentDB to SQLite/PostgreSQL
- Add new data sources
- Schedule automated ingestion jobs

---

### 6. **[Open Source Stack](./06-OPEN_SOURCE_STACK.md)** ⭐ NEW
**Purpose:** 100% open-source technology choices, zero vendor lock-in

**Contents:**
- **Progressive enhancement path:** SQLite (local) → PostgreSQL (production)
- **Complete open-source stack:**
  - Backend: FastAPI, Celery, Redis (all MIT/BSD)
  - Databases: SQLite → PostgreSQL, Qdrant (vectors), Neo4j (graph)
  - Frontend: React, TypeScript, shadcn/ui
  - Infrastructure: Docker, Kubernetes, GitHub Actions
- **Cost breakdown:**
  - Development: $0/month (100% local)
  - Small production (10K articles): ~$160/month
  - Medium production (100K articles): ~$660/month
  - Compare to AWS: **70% cost savings**
- **Deployment options:** Single VPS, Kubernetes, or managed services
- **Migration path:** DocumentDB → SQLite → PostgreSQL (zero code changes)

**Read this if you need to:**
- Understand why we chose open source
- Estimate infrastructure costs
- Deploy on a budget
- Avoid vendor lock-in
- Self-host everything

---

## 🎯 Quick Start Guide

### For Stakeholders / Decision Makers
1. Read **[01-SYSTEM_ARCHITECTURE.md](./01-SYSTEM_ARCHITECTURE.md)** (Sections: Executive Summary, System Overview)
2. Read **[02-ADVANCED_FEATURES.md](./02-ADVANCED_FEATURES.md)** (Sections: Vision Statement, Feature Prioritization Matrix)
3. Review **[04-IMPLEMENTATION_ROADMAP.md](./04-IMPLEMENTATION_ROADMAP.md)** (Sections: Budget Estimate, Success Metrics)

**Time Required:** 30 minutes  
**Outcome:** Understand what we're building, why, and at what cost

---

### For Product Managers
1. Read **[02-ADVANCED_FEATURES.md](./02-ADVANCED_FEATURES.md)** (All sections)
2. Read **[04-IMPLEMENTATION_ROADMAP.md](./04-IMPLEMENTATION_ROADMAP.md)** (Sections: Phase Breakdown, User Personas)
3. Skim **[03-TECHNICAL_REQUIREMENTS.md](./03-TECHNICAL_REQUIREMENTS.md)** (Section: API Design)

**Time Required:** 2 hours  
**Outcome:** Define MVP scope, prioritize features, plan user testing

---

### For Engineers / Tech Leads
1. Read **[01-SYSTEM_ARCHITECTURE.md](./01-SYSTEM_ARCHITECTURE.md)** (All sections)
2. Read **[03-TECHNICAL_REQUIREMENTS.md](./03-TECHNICAL_REQUIREMENTS.md)** (All sections)
3. Review **[04-IMPLEMENTATION_ROADMAP.md](./04-IMPLEMENTATION_ROADMAP.md)** (Sections: Sprint Breakdown, Repository Structure)

**Time Required:** 3-4 hours  
**Outcome:** Understand architecture, tech stack, and implementation plan

---

### For ML Engineers / Data Scientists
1. Read **[01-SYSTEM_ARCHITECTURE.md](./01-SYSTEM_ARCHITECTURE.md)** (Sections: Data Models, Prompt Engineering)
2. Read **[03-TECHNICAL_REQUIREMENTS.md](./03-TECHNICAL_REQUIREMENTS.md)** (Sections: AI/ML Pipeline, LLM Integration)
3. Read **[02-ADVANCED_FEATURES.md](./02-ADVANCED_FEATURES.md)** (Sections: RAG, Citation Network, Predictive Analytics)

**Time Required:** 2-3 hours  
**Outcome:** Understand LLM usage, embeddings strategy, and ML features

---

## 🔑 Key Concepts

### What is Tobacco Harm Reduction (THR)?
The principle that switching from combustible cigarettes to less harmful nicotine products (e-cigarettes, heated tobacco) can reduce smoking-related disease. This platform analyzes scientific research on THR topics.

### v1.0 vs v2.0 Comparison

| Capability | v1.0 (Current) | v2.0 (Target) |
|------------|----------------|---------------|
| **Analysis Scope** | Single article | Multi-document synthesis |
| **Search** | Keyword filters | Semantic search + RAG Q&A |
| **Insights** | Individual article summaries | Citation network, trend analysis |
| **Monitoring** | Manual ingestion | Real-time publication alerts |
| **Collaboration** | Single user | Multi-user workspaces + annotations |
| **Reporting** | N/A | Automated literature reviews |
| **Scale** | Batch processing | Real-time + batch |

### Core Technologies (100% Open Source)
- **LLM:** Anthropic Claude (Opus 4.8, Sonnet 4.6, Haiku 4.5) - only paid component
- **Framework:** FastAPI (Python), React (TypeScript) - MIT licensed
- **Databases:** 
  - SQLite → PostgreSQL (relational)
  - Qdrant / ChromaDB (vector search)
  - Neo4j Community Edition (graph)
  - Redis (cache)
- **Deployment:** Docker Compose (local) → Kubernetes (production)
- **AI/ML:** sentence-transformers, BERTopic, spaCy (all open source)
- **Data Sources:** PubMed, Crossref, Google Scholar (all FREE APIs)

---

## 📊 Project Scope at a Glance

### What's In Scope (v2.0)
✅ Multi-document synthesis with citations  
✅ Advanced RAG for Q&A across corpus  
✅ Citation network visualization  
✅ Interactive dashboards (executive + deep-dive)  
✅ Real-time publication monitoring + alerts  
✅ Multi-user collaboration (workspaces, annotations)  
✅ Automated literature review generation  
✅ API for programmatic access  
✅ Confidence scoring + explainability  

### What's Out of Scope (Post-v2.0)
❌ Multilingual support (English only for v2.0)  
❌ Mobile app (web only)  
❌ Full-text PDF parsing (abstracts only)  
❌ Automated peer review  
❌ Integration with proprietary databases (beyond PubMed)  

---

## 🚀 Next Steps

### Immediate Actions (Pre-Development)
1. **Stakeholder Review (Week 1)**
   - Share docs with client/users
   - Collect feedback on features and priorities
   - Finalize MVP scope

2. **Team Staffing (Week 2)**
   - Hire/assign 5-7 engineers
   - Define roles and responsibilities
   - Set up communication channels (Slack, Jira)

3. **Infrastructure Planning (Week 2)**
   - Choose cloud provider (AWS/Azure/GCP)
   - Provision accounts and budgets
   - Set up CI/CD tools (GitHub Actions)

4. **Kickoff Meeting (Week 3)**
   - Align team on vision
   - Review roadmap and milestones
   - Assign Sprint 1 tasks

### Development Start (Sprint 1, Weeks 3-4)
- Repository setup (monorepo structure)
- Docker Compose for local dev
- PostgreSQL + Redis + Neo4j configuration
- CI/CD pipeline (tests, linting, build)
- AWS infrastructure (Terraform)

**Target Go-Live:** Month 8 (after 16 sprints)

---

## 📞 Contact & Support

### Project Team
- **Tech Lead:** [TBD]
- **Product Manager:** [TBD]
- **Domain Expert:** [Client Contact]

### Documentation Feedback
- Found an error? Open an issue or email [your-email]
- Suggestions? Add comments in shared doc or Slack #project-channel

### Repository
- Code: [GitHub repo URL - TBD]
- Documentation: `docs/` folder

---

## 📝 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-23 | Claude Code | Initial documentation (4 docs: Architecture, Features, Tech, Roadmap) |

---

## 📚 Additional Resources

### External References
- **Pydantic Documentation:** https://docs.pydantic.dev/
- **Claude API Documentation:** https://docs.anthropic.com/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Neo4j Graph Database:** https://neo4j.com/docs/
- **Sentence Transformers:** https://www.sbert.net/

### Related Research
- People-First Language Guidelines: [APA Style](https://apastyle.apa.org/style-grammar-guidelines/bias-free-language/people-first-language)
- Tobacco Harm Reduction: [Wikipedia](https://en.wikipedia.org/wiki/Tobacco_harm_reduction)
- PubMed API: [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

---

**Happy Building! 🚀**
