# Quick Start Guide
## Get Your Advanced Prototype Running in 30 Minutes

**Version:** 2.0  
**Date:** 2026-07-23  
**Audience:** Developers starting the project

---

## 📋 What You'll Build

A research intelligence platform that:
- Ingests articles from PubMed/Crossref/Google Scholar
- Analyzes them with Claude AI (extraction + fact-checking)
- Enables semantic search and Q&A across all articles
- Visualizes citation networks
- Generates automated literature reviews

**Tech Stack:** Python, FastAPI, React, SQLite, Claude API

---

## ⚡ 30-Minute Setup

### Prerequisites
```bash
# Install required tools
- Python 3.11+
- Node.js 20+
- Docker Desktop
- Git
```

### Step 1: Clone & Setup (5 minutes)

```bash
# Create project directory
mkdir tobacco-research-platform
cd tobacco-research-platform

# Initialize Git
git init

# Create directory structure
mkdir -p backend/app/{api/v1,core,models,schemas,services,db,tasks,ingestion}
mkdir -p frontend/src/{components,pages,hooks,services}
mkdir -p data
mkdir -p docs
mkdir -p scripts

# Copy existing v1.0 files
# (You have: schema.py with Response/FactualEvaluationResponse models)
# (You have: prompts from v1.0)
```

### Step 2: Backend Setup (10 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.110.0
uvicorn[standard]==0.27.0
pydantic==2.6.0
anthropic==0.31.0
sqlalchemy==2.0.27
alembic==1.13.1
celery==5.3.6
redis==5.0.1
sentence-transformers==2.5.1
biopython==1.83
scholarly==1.7.11
httpx==0.26.0
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./data/articles.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
EOF

# Copy your existing schema.py
cp /path/to/your/schema.py app/schemas/schema.py

# Create database initialization script
cat > app/db/sqlite.py << 'EOF'
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "./data/articles.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Create tables if they don't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Create articles table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            source_metadata_id TEXT,
            doi TEXT,
            url TEXT,
            ingestion_status TEXT DEFAULT 'pending',
            article_type TEXT,
            title TEXT NOT NULL,
            abstract TEXT,
            journal TEXT,
            keywords JSON,
            authors JSON,
            publication_date TEXT,
            country TEXT,
            ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create article_analysis table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_analysis (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            subject TEXT,
            category TEXT,
            summary TEXT,
            entities JSON,
            sentiment TEXT,
            industry_affiliation TEXT,
            coi_details TEXT,
            author_affiliations JSON,
            citation_string TEXT,
            confidence_scores JSON,
            model_id TEXT,
            prompt_used TEXT,
            prompt_version TEXT,
            analyzed_at DATETIME,
            analysis_status TEXT DEFAULT 'pending',
            fact_check_status TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized!")

if __name__ == "__main__":
    init_db()
EOF

# Initialize database
python -m app.db.sqlite

# Create basic FastAPI app
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Tobacco Research Platform", version="2.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Tobacco Research Platform v2.0", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
EOF

# Test backend
uvicorn app.main:app --reload --port 8000
# Visit http://localhost:8000/docs to see API documentation
```

### Step 3: Frontend Setup (10 minutes)

```bash
cd ../frontend

# Create Vite React app
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install UI libraries
npm install @tanstack/react-query recharts lucide-react

# Create basic page
cat > src/App.tsx << 'EOF'
import { useQuery } from '@tanstack/react-query'
import './App.css'

function App() {
  const { data, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/health')
      return res.json()
    }
  })

  return (
    <div className="App">
      <h1>Tobacco Research Platform v2.0</h1>
      {isLoading ? (
        <p>Connecting to backend...</p>
      ) : (
        <p>Backend status: {data?.status}</p>
      )}
    </div>
  )
}

export default App
EOF

# Start frontend
npm run dev
# Visit http://localhost:3000
```

### Step 4: Docker Compose (5 minutes)

```bash
cd ..

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/articles.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
      - ./data:/app/data
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  redis_data:
EOF

# Create backend Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# Create frontend Dockerfile
cat > frontend/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
EOF

# Start everything
docker-compose up -d
```

---

## ✅ Verify Setup

### 1. Check Backend
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# View API docs
open http://localhost:8000/docs
```

### 2. Check Frontend
```bash
open http://localhost:3000
# Should see "Backend status: healthy"
```

### 3. Check Database
```bash
sqlite3 data/articles.db "SELECT name FROM sqlite_master WHERE type='table';"
# Expected: articles, article_analysis
```

### 4. Test Redis
```bash
redis-cli ping
# Expected: PONG
```

---

## 🚀 Next Steps (Day 1-7)

### Day 1: Migrate v1.0 Data
```bash
# Run migration script
python scripts/migrate_documentdb_to_sqlite.py \
  --mongo-uri "mongodb://your-host:27017" \
  --mongo-db "tobacco_research" \
  --sqlite-path "./data/articles.db"

# Verify migration
sqlite3 data/articles.db "SELECT COUNT(*) FROM articles;"
```

### Day 2: Add Article Analysis Endpoint
See `MIGRATION_GUIDE.md` for full code.

```python
# backend/app/api/v1/articles.py
from fastapi import APIRouter
from app.services.analysis import analysis_service

router = APIRouter()

@router.post("/analyze")
async def analyze_article(request: AnalyzeRequest):
    result = await analysis_service.analyze_article(
        doc_id=request.article_id,
        title=request.title,
        journal=request.journal,
        date=request.date,
        abstract=request.abstract
    )
    return result
```

### Day 3-4: Build Article List View (Frontend)
```typescript
// frontend/src/pages/ArticleList.tsx
// Show articles in table with filters
```

### Day 5: Add PubMed Ingestion
```python
# backend/app/ingestion/pubmed.py
# See 05-DATA_INGESTION_PIPELINE.md for full code
```

### Day 6-7: Add Semantic Search
```python
# Install sentence-transformers
# Generate embeddings for all articles
# Add search endpoint
```

---

## 📚 Key Documentation

**Must Read (in order):**
1. `docs/00-README.md` - Navigation guide
2. `docs/01-SYSTEM_ARCHITECTURE.md` - Understand v1.0
3. `docs/MIGRATION_GUIDE.md` - Migrate code step-by-step
4. `docs/05-DATA_INGESTION_PIPELINE.md` - Build connectors
5. `docs/06-OPEN_SOURCE_STACK.md` - Deployment options

**Reference:**
- `docs/SCHEMA_MAPPING.md` - Complete field mapping
- `docs/02-ADVANCED_FEATURES.md` - Feature roadmap
- `docs/03-TECHNICAL_REQUIREMENTS.md` - Architecture details
- `docs/04-IMPLEMENTATION_ROADMAP.md` - 8-month plan

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### "Database locked" error
```bash
# SQLite only allows one writer at a time
# Use PostgreSQL for production (see 06-OPEN_SOURCE_STACK.md)
```

### "CORS error" in frontend
```bash
# Check CORS middleware in backend/app/main.py
# Ensure allow_origins includes "http://localhost:3000"
```

### "Claude API error"
```bash
# Check your API key in .env
# Verify balance: https://console.anthropic.com/
```

---

## 💡 Pro Tips

1. **Use the docs:** Every feature has detailed code examples
2. **Start simple:** SQLite + local dev → Production later
3. **Test incrementally:** Don't build everything at once
4. **Ask for help:** Check `docs/` before Googling
5. **Git commit often:** Small commits = easy debugging

---

## 🎯 Week 1 Goal

By end of week 1, you should have:
- ✅ Local development environment running
- ✅ v1.0 data migrated to SQLite
- ✅ Basic article list view (frontend)
- ✅ Article analysis endpoint (backend)
- ✅ Fact-checking working
- ✅ First new article analyzed via API

**You're now ready to build advanced features!** 🚀

---

## 📞 Questions?

- **Code issues:** Check `MIGRATION_GUIDE.md`
- **Data questions:** Check `SCHEMA_MAPPING.md`
- **Architecture:** Check `01-SYSTEM_ARCHITECTURE.md`
- **Features:** Check `02-ADVANCED_FEATURES.md`
- **Deployment:** Check `06-OPEN_SOURCE_STACK.md`

**All docs are in `docs/` folder. Start with `docs/00-README.md`.**

Happy building! 🎉
