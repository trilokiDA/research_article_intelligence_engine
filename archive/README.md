# Archived Documentation

This folder contains historical documentation from project setup and early development iterations.

## Why Archived?

These documents were useful during initial development but are now superseded by the current documentation structure:

- **README.md** (root) - Current quick start and features
- **ARCHITECTURE.md** (root) - System design and structure
- **DEVELOPMENT.md** (root) - Setup and development guide
- **ROADMAP.md** (root) - Future plans
- **docs/** - Specialized reference documentation

## Contents

### Historical Vision & Planning
- **PROJECT_SUMMARY.md** - Original v2.0 vision (project scaled down to v1.0)
- **QUICK_START.md** - Early quick start guide (now in README.md)
- **stage_1_2_implementation_plan.md** - Stage 1/2 planning document

### Setup & Status Documents
- **SETUP_COMPLETE.md** - One-time setup completion status
- **IMPLEMENTATION_SUMMARY.md** - Stage 1 implementation completion status
- **IMPLEMENTATION_COMPLETE_STAGE_1_2.md** - Stage 1/2 completion status
- **INSTALLATION.md** - Installation guide (now in DEVELOPMENT.md)

### Feature Documentation (Now in README.md)
- **TOPIC_QUERIES_GUIDE.md** - Topic-based query system guide
- **TOPIC_QUERIES_COMPLETE.md** - Topic query implementation status
- **DATA_VIEWING_GUIDE.md** - Database viewing guide

### Technical Documents (Moved/Consolidated)
- **MIGRATION_GUIDE.md** - DocumentDB migration (not applicable)
- **FUTURE_PIPELINE_PROPOSAL.md** - Future features (now in ROADMAP.md)
- **GENAI_SETUP.md** - GenAI setup (consolidated into GENAI_PIPELINE.md)
- **PROJECT_STRUCTURE.md** - Project structure (now in ARCHITECTURE.md)
- **SKIP_ALREADY_SUMMARIZED.md** - Implementation detail (in code comments)

### Git Artifacts
- **FOLDER_RENAME_SUMMARY.md** - Folder rename history

## Useful Historical Information

### Original v2.0 Vision
The project was originally envisioned as a comprehensive research intelligence platform with:
- Advanced RAG Q&A
- Citation network analysis
- Multi-document synthesis
- Real-time monitoring
- Collaborative features
- Interactive dashboards

See **PROJECT_SUMMARY.md** for full details.

**Current Status:** Project implemented as v1.0 (ingestion + GenAI analysis) with v2.0 features planned for future.

### Why Crossref Was Disabled
Crossref was included in initial design but disabled during implementation because:
- API returns no abstracts for most articles
- Without abstracts, GenAI analysis is impossible
- Code remains in codebase (commented out) for potential future use

See **IMPLEMENTATION_SUMMARY.md** for details.

### Topic-Based Query System
The topic query system was added to simplify searching for common research areas:
- Heat-Not-Burn (IQOS, HEETS, THS)
- E-Cigarettes (vaping, ENDS)
- Nicotine-Pouch
- Snus

See **TOPIC_QUERIES_GUIDE.md** for original implementation details.

### File-Based GenAI Pipeline
GenAI analysis saves results to JSON files (one per article) rather than database:
- Easier to review and validate
- Can be re-processed without database changes
- Skip logic based on file existence

See **SKIP_ALREADY_SUMMARIZED.md** for implementation rationale.

## When to Reference These Docs

- **Understanding original vision:** PROJECT_SUMMARY.md
- **Historical context for decisions:** IMPLEMENTATION_SUMMARY.md
- **Stage 1/2 planning:** stage_1_2_implementation_plan.md
- **Topic query implementation:** TOPIC_QUERIES_GUIDE.md

## Current Documentation

For up-to-date information, always refer to:

1. **README.md** - Quick start, features, current status
2. **ARCHITECTURE.md** - System design and components
3. **DEVELOPMENT.md** - Setup and development
4. **ROADMAP.md** - Future plans
5. **docs/GENAI_PIPELINE.md** - GenAI implementation
6. **docs/SCHEMA_REFERENCE.md** - Database schema
7. **docs/API_REFERENCE.md** - CLI and Python API

---

**Last Updated:** 2026-07-30  
**Reason for Archive:** Documentation consolidation and cleanup
