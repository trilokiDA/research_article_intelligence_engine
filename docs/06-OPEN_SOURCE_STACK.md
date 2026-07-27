# Open Source Technology Stack
## 100% Open Source, Zero Vendor Lock-In

**Version:** 2.0  
**Date:** 2026-07-23  
**Philosophy:** Start local with SQLite, scale to cloud with open-source tools

---

## 🎯 Core Principles

### 1. **Open Source First**
- All infrastructure components are open source
- No proprietary databases or vendor lock-in
- Community-supported tools with active development

### 2. **Progressive Enhancement**
- Start simple: SQLite + local embeddings + Docker Compose
- Scale up: PostgreSQL + Qdrant + Kubernetes
- Pay only for compute, not licenses

### 3. **Transparent Costs**
- Only paid component: Claude API (~$140/month for 10K articles)
- All other infrastructure: Free or self-hosted
- No surprise costs or usage limits

---

## Complete Open Source Stack

### **Backend** (100% Open Source)

| Component | Technology | License | Why? |
|-----------|-----------|---------|------|
| **Language** | Python 3.11+ | PSF License | Most popular for AI/ML |
| **Web Framework** | FastAPI 0.110+ | MIT | Modern, fast, auto-docs |
| **Task Queue** | Celery 5.x | BSD | Battle-tested async jobs |
| **Message Broker** | Redis 7+ | BSD | Fast, simple, reliable |
| **ORM** | SQLAlchemy 2.x | MIT | Database abstraction layer |
| **Migrations** | Alembic | MIT | Schema versioning |
| **HTTP Client** | httpx | BSD | Async HTTP requests |
| **Testing** | pytest | MIT | Industry standard |

### **Databases** (100% Open Source)

#### Phase 1: Local Development
```
SQLite 3.45+ (Public Domain)
├─ Zero setup, single file
├─ Full-text search (FTS5)
├─ JSON support
├─ Perfect for <100K articles
└─ File: ./data/articles.db

ChromaDB (Apache 2.0) - Embedded vector database
├─ Python-native
├─ Runs in-process
├─ No separate server needed
└─ Great for prototyping
```

#### Phase 2: Production (Small-Medium Scale)
```
PostgreSQL 16+ (PostgreSQL License - MIT-like)
├─ Drop-in replacement for SQLite
├─ pgvector extension (vector search)
├─ Full-text search built-in
├─ JSON/JSONB support
├─ Scales to millions of rows
└─ Deployment: Docker or managed (Supabase, Render, Railway)

Qdrant (Apache 2.0) - Production vector database
├─ Rust-based (high performance)
├─ REST + gRPC APIs
├─ Metadata filtering
├─ Scales horizontally
└─ Docker: docker run -p 6333:6333 qdrant/qdrant

Neo4j Community Edition (GPLv3)
├─ Graph database for citation network
├─ Cypher query language
├─ Graph algorithms library
└─ Docker: docker run -p 7474:7474 neo4j:community

Redis 7+ (BSD)
├─ Cache layer
├─ Session store
├─ Celery broker
└─ Docker: docker run -p 6379:6379 redis:alpine
```

### **AI/ML Stack** (100% Open Source)

| Component | Technology | License | Why? |
|-----------|-----------|---------|------|
| **LLM SDK** | anthropic-sdk | MIT | Official Claude API client |
| **Embeddings** | sentence-transformers | Apache 2.0 | SOTA embedding models |
| **NLP** | spaCy 3.x | MIT | Industrial-strength NLP |
| **Topic Modeling** | BERTopic | MIT | Transformer-based topics |
| **Data Science** | pandas, numpy, scikit-learn | BSD | Standard ML toolkit |

### **Frontend** (100% Open Source)

| Component | Technology | License | Why? |
|-----------|-----------|---------|------|
| **Framework** | React 18 | MIT | Industry standard |
| **Language** | TypeScript 5.x | Apache 2.0 | Type safety |
| **Build Tool** | Vite 5+ | MIT | Fast, modern bundler |
| **UI Components** | shadcn/ui (Radix + Tailwind) | MIT | Accessible, customizable |
| **Visualization** | Recharts, D3.js | MIT | Charts and graphs |
| **Graph Rendering** | react-force-graph | MIT | Citation networks |
| **State Management** | Zustand | MIT | Simple, fast state |
| **Data Fetching** | TanStack Query | MIT | Server state management |
| **Forms** | React Hook Form + Zod | MIT | Form validation |

### **Infrastructure** (100% Open Source)

| Component | Technology | License | Why? |
|-----------|-----------|---------|------|
| **Containerization** | Docker | Apache 2.0 | Standard container runtime |
| **Orchestration** | Docker Compose → Kubernetes | Apache 2.0 | Local dev → production |
| **Reverse Proxy** | Nginx | BSD | High performance |
| **Process Manager** | Supervisor / systemd | Multiple | Keep services running |
| **CI/CD** | GitHub Actions (free for public repos) | - | Automated testing & deployment |

### **Monitoring & Observability** (Open Source Options)

| Component | Technology | License | Notes |
|-----------|-----------|---------|-------|
| **Metrics** | Prometheus + Grafana | Apache 2.0 | Time-series metrics |
| **Logging** | Loki | Apache 2.0 | Log aggregation |
| **Tracing** | Jaeger | Apache 2.0 | Distributed tracing |
| **Uptime** | Uptime Kuma | MIT | Self-hosted uptime monitor |

---

## Data Ingestion (Open Source)

### Source Connectors (All Free APIs)

| Source | Access | Rate Limit | Cost |
|--------|--------|-----------|------|
| **PubMed** | E-utilities API | 10 req/sec with free API key | FREE |
| **Crossref** | REST API | 50 req/sec (polite pool) | FREE |
| **Google Scholar** | Scraping (via `scholarly` library) | ~100 req/hour | FREE (use cautiously) |
| **OpenAlex** | REST API | Unlimited | FREE |
| **Semantic Scholar** | API | 100 req/sec | FREE |

### Ingestion Libraries (Open Source)
```
Biopython (Bio.Entrez) - PubMed API client (BSD)
scholarly - Google Scholar scraper (Unlicense)
requests / httpx - HTTP clients (Apache 2.0)
BeautifulSoup4 - HTML parsing (MIT)
lxml - XML parsing (BSD)
```

---

## Development Tools (100% Open Source)

| Tool | Technology | License | Purpose |
|------|-----------|---------|---------|
| **Code Editor** | VS Code | MIT | Most popular IDE |
| **Version Control** | Git | GPLv2 | Standard VCS |
| **Code Hosting** | GitHub (free tier) | - | Repo + CI/CD |
| **API Testing** | Postman / Thunder Client | Free tier | API development |
| **Database Client** | DBeaver | Apache 2.0 | Universal DB GUI |
| **Graph Visualization** | Neo4j Browser | GPLv3 | Explore graph data |

---

## Cost Breakdown

### Development Environment (FREE)
```
SQLite: FREE
ChromaDB: FREE (self-hosted)
Redis: FREE (Docker)
Neo4j Community: FREE
Python + FastAPI: FREE
React + Vite: FREE
Docker: FREE
GitHub: FREE (public repos)

TOTAL: $0/month
```

### Small Production (10K articles, 10 users)
```
VPS (4 CPU, 8GB RAM): $20-40/month (Hetzner, DigitalOcean)
  ├─ PostgreSQL
  ├─ Qdrant
  ├─ Neo4j
  ├─ Redis
  └─ FastAPI + React

Claude API: ~$140/month (10K articles analyzed)
Domain + SSL: $12/year (Cloudflare free SSL)

TOTAL: ~$160-180/month
```

### Medium Production (100K articles, 100 users)
```
VPS Cluster (3 nodes, 8 CPU, 16GB each): $150-200/month
  ├─ Kubernetes cluster (k3s)
  ├─ PostgreSQL (primary + replica)
  ├─ Qdrant cluster
  ├─ Neo4j
  └─ Redis cluster

Claude API: ~$500/month (batched processing, caching)
CDN (Cloudflare): FREE
Backups (S3-compatible): $10/month (Wasabi, Backblaze B2)
Monitoring (self-hosted Grafana): FREE

TOTAL: ~$660-710/month
```

Compare to AWS equivalent: **$2,000-3,000/month** ✅ **70% cost savings**

---

## Deployment Options

### Option 1: Single VPS (Simple)
**Best for:** MVP, <20 users, <50K articles

```bash
# One command deployment
docker-compose up -d

# Includes:
- FastAPI backend
- React frontend (Nginx)
- PostgreSQL
- Qdrant
- Neo4j
- Redis
- Celery workers
```

**Cost:** $20-40/month (Hetzner, DigitalOcean, Linode)

### Option 2: Kubernetes Cluster (Scalable)
**Best for:** Production, 100+ users, 100K+ articles

```yaml
# Deploy with Helm
helm install tobacco-research ./charts/tobacco-research

# Auto-scaling, zero-downtime updates
# Horizontal pod autoscaling
# Self-healing
```

**Cost:** $150-300/month (3-node cluster)

### Option 3: Managed Services (Hybrid)
**Best for:** Less DevOps, focus on features

```
PostgreSQL: Supabase (free tier → $25/month)
Redis: Upstash (free tier → $10/month)
Qdrant: Qdrant Cloud (free tier → $25/month)
App Hosting: Render, Railway, Fly.io (free tier → $20/month)
```

**Cost:** $0-80/month (start free, pay as you grow)

---

## Migration Path: DocumentDB → SQLite → PostgreSQL

### Step 1: Migrate DocumentDB to SQLite
**Script:** `scripts/migrate_documentdb_to_sqlite.py`

```bash
# Export from DocumentDB
python scripts/migrate_documentdb_to_sqlite.py \
  --mongo-uri "mongodb://localhost:27017" \
  --mongo-db "tobacco_research" \
  --sqlite-path "./data/articles.db"

# Result: articles.db with v2.0 schema
```

### Step 2: Develop on SQLite
```python
# SQLAlchemy works identically for SQLite and PostgreSQL
DATABASE_URL = "sqlite:///./data/articles.db"
engine = create_engine(DATABASE_URL)
```

### Step 3: Migrate to PostgreSQL (When Ready)
```bash
# Change one environment variable
DATABASE_URL="postgresql://user:pass@localhost/tobacco_research"

# Run migrations
alembic upgrade head

# Optional: Import SQLite data to PostgreSQL
python scripts/sqlite_to_postgres.py
```

**Zero code changes needed!** SQLAlchemy abstracts the database.

---

## Open Source Alternatives to Proprietary Tools

| Proprietary Tool | Open Source Alternative | Notes |
|------------------|-------------------------|-------|
| **AWS RDS** | PostgreSQL (self-hosted or Supabase) | Same database, full control |
| **Pinecone** | Qdrant / ChromaDB | Open source vector databases |
| **MongoDB Atlas** | PostgreSQL (JSONB) / CouchDB | JSONB matches MongoDB features |
| **Elasticsearch** | PostgreSQL Full-Text / Meilisearch | Built-in search or Meilisearch |
| **AWS Lambda** | Celery + Redis / Modal | Async task processing |
| **Heroku** | Fly.io / Render / Railway | Modern PaaS, better pricing |
| **DataDog** | Prometheus + Grafana | Self-hosted monitoring |
| **Sentry** | GlitchTip / Sentry self-hosted | Error tracking |
| **Auth0** | Keycloak / Authentik | Self-hosted auth |

---

## Why Open Source?

### ✅ Benefits

1. **Cost Control**
   - No surprise bills
   - Predictable scaling costs
   - No license fees

2. **Transparency**
   - See exactly how it works
   - Audit for security
   - Fix bugs yourself

3. **Flexibility**
   - Self-host anywhere
   - Customize as needed
   - No platform restrictions

4. **Community**
   - Active development
   - Shared knowledge
   - Free support (forums, GitHub)

5. **No Lock-In**
   - Switch providers anytime
   - Own your data
   - Portable infrastructure

### ⚠️ Trade-offs

1. **DevOps Responsibility**
   - You manage updates
   - You handle backups
   - You monitor uptime
   - **Mitigation:** Docker Compose simplifies deployment

2. **Support**
   - No 24/7 paid support
   - Community forums instead
   - **Mitigation:** Most tools have excellent docs

3. **Integration**
   - More manual setup vs. managed services
   - **Mitigation:** Docker Compose orchestrates everything

**Verdict:** For a research prototype → production app, open source is ideal.

---

## Recommended Starting Point

### Day 1 Setup (30 minutes)
```bash
# Clone repo
git clone https://github.com/your-org/tobacco-research-platform
cd tobacco-research-platform

# Start all services
docker-compose up -d

# Services running:
✓ FastAPI (http://localhost:8000)
✓ React (http://localhost:3000)
✓ PostgreSQL (localhost:5432)
✓ Qdrant (http://localhost:6333)
✓ Neo4j (http://localhost:7474)
✓ Redis (localhost:6379)

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed with test data
docker-compose exec backend python scripts/seed_database.py

# Done! Visit http://localhost:3000
```

### Day 2-30: Build Features
All infrastructure is ready. Focus 100% on features.

### Month 2: Deploy to Production
```bash
# Deploy to Hetzner VPS
./deploy.sh production

# Same docker-compose.yml, different environment variables
```

---

## Summary: Complete Open Source Stack

```
Application Layer:
├─ Backend: FastAPI + Python (MIT)
├─ Frontend: React + TypeScript (MIT)
└─ Task Queue: Celery + Redis (BSD)

Data Layer:
├─ Relational: SQLite → PostgreSQL (Open Source)
├─ Vector: ChromaDB → Qdrant (Apache 2.0)
├─ Graph: Neo4j Community (GPLv3)
└─ Cache: Redis (BSD)

AI Layer:
├─ LLM: Claude API (only paid component)
├─ Embeddings: sentence-transformers (Apache 2.0)
├─ NLP: spaCy (MIT)
└─ Topic Modeling: BERTopic (MIT)

Infrastructure:
├─ Containers: Docker (Apache 2.0)
├─ Orchestration: Docker Compose → Kubernetes (Apache 2.0)
├─ Web Server: Nginx (BSD)
└─ CI/CD: GitHub Actions (free)

Data Sources:
├─ PubMed: Free API
├─ Crossref: Free API
├─ Google Scholar: Free (scraping)
└─ OpenAlex: Free API

TOTAL MONTHLY COST (Production):
├─ VPS: $20-200 (scale as needed)
├─ Claude API: $140-500 (pay per use)
└─ Everything else: FREE

NO VENDOR LOCK-IN. OWN YOUR STACK. 🚀
```

---

## Next Steps

1. **Review:** Share with team for feedback
2. **Setup:** Clone repo, run `docker-compose up`
3. **Migrate:** Run DocumentDB → SQLite migration script
4. **Develop:** Build features on local stack
5. **Deploy:** Push to VPS when ready

All tools documented in:
- `03-TECHNICAL_REQUIREMENTS.md` - Detailed architecture
- `05-DATA_INGESTION_PIPELINE.md` - Data connectors
- `MIGRATION_GUIDE.md` - v1.0 → v2.0 migration

**Open source = Freedom + Control + Cost savings** ✅
