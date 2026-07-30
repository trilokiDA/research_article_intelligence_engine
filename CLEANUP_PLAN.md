# Documentation Cleanup Plan

**Date:** 2026-07-30  
**Status:** Proposed  
**Goal:** Consolidate and organize project documentation to reflect current state

---

## 🎯 Current State Analysis

### ✅ What's Working (Keep & Update)
1. **README.md** - Main project entry point
2. **docs/GENAI_PIPELINE.md** - GenAI implementation details
3. **docs/SCHEMA_MAPPING.md** - Database schema reference

### ⚠️ Outdated/Confusing (Consolidate or Archive)
1. **PROJECT_SUMMARY.md** - Contains v2.0 vision but project is v1.0 implementation
2. **QUICK_START.md** - Duplicate of README quick start, outdated structure
3. **IMPLEMENTATION_SUMMARY.md** - Historical doc, now outdated
4. **SETUP_COMPLETE.md** - One-time setup status doc
5. **TOPIC_QUERIES_GUIDE.md** - Should be merged into README
6. **TOPIC_QUERIES_COMPLETE.md** - Status doc (duplicate info)
7. **DATA_VIEWING_GUIDE.md** - Should be in README or separate USAGE.md
8. **INSTALLATION.md** - Duplicate of README setup
9. **docs/MIGRATION_GUIDE.md** - Not applicable (no DocumentDB migration happening)
10. **docs/FUTURE_PIPELINE_PROPOSAL.md** - Future features (should be ROADMAP.md)
11. **docs/GENAI_SETUP.md** - Duplicate of GENAI_PIPELINE.md setup section
12. **docs/PROJECT_STRUCTURE.md** - Should be in README or ARCHITECTURE.md
13. **docs/IMPLEMENTATION_COMPLETE_STAGE_1_2.md** - Historical status doc
14. **docs/SKIP_ALREADY_SUMMARIZED.md** - Implementation detail (move to code comments)
15. **docs/stage_1_2_implementation_plan.md** - Historical planning doc
16. **docs/FOLDER_RENAME_SUMMARY.md** - Git history artifact

---

## 📋 Proposed New Structure

```
radar/
├── README.md                           [UPDATED] Main entry point
├── ARCHITECTURE.md                     [NEW] System design & structure
├── DEVELOPMENT.md                      [NEW] Setup, running, testing
├── ROADMAP.md                          [NEW] Future plans & evaluation
├── CHANGELOG.md                        [NEW] Version history
│
├── docs/
│   ├── API_REFERENCE.md               [NEW] CLI & Python API docs
│   ├── DATA_SOURCES.md                [NEW] PubMed, Crossref details
│   ├── GENAI_PIPELINE.md              [KEEP] GenAI implementation
│   ├── SCHEMA_REFERENCE.md            [RENAMED] From SCHEMA_MAPPING.md
│   └── TROUBLESHOOTING.md             [NEW] Common issues & solutions
│
└── archive/                            [NEW] Historical docs
    ├── PROJECT_SUMMARY.md              [ARCHIVED]
    ├── QUICK_START.md                  [ARCHIVED]
    ├── IMPLEMENTATION_SUMMARY.md       [ARCHIVED]
    ├── SETUP_COMPLETE.md               [ARCHIVED]
    ├── ... (all historical/duplicate docs)
    └── README.md                       [NEW] Archive index
```

---

## 🔧 Cleanup Actions

### Phase 1: Create Core Documentation (Week 1)

#### 1. **README.md** (Update)
**Current issues:**
- References Crossref (commented out in code)
- Mentions Google Scholar (not implemented)
- Missing topic-based queries
- Missing file-based GenAI pipeline info

**New structure:**
```markdown
# Research Article Intelligence Engine

## Quick Start
- Installation (5 min)
- First search (PubMed only)
- Run GenAI analysis (file-based)

## Features
- ✅ PubMed ingestion
- ⚠️ Crossref (disabled - no abstracts)
- ✅ Topic-based queries (Heat-Not-Burn, E-Cigarettes, etc.)
- ✅ GenAI summarization (file-based, Groq LLMs)
- ✅ Smart filtering (skip existing summaries)
- ✅ SQLite database
- ✅ Full-text search (FTS5)

## Usage
- CLI commands (with topic examples)
- Database viewing
- Analysis pipeline

## Project Status
- Current: v1.0 - Data ingestion + GenAI analysis
- Next: Evaluation & revalidation
- Future: RAG, citation network, UI
```

#### 2. **ARCHITECTURE.md** (New)
**Purpose:** Technical design & structure

**Contents:**
```markdown
# System Architecture

## Overview
Two-stage pipeline: Ingestion → Analysis

## Components
1. Data Ingestion Layer
   - PubMed connector (active)
   - Crossref connector (disabled)
   - Topic query system
   
2. GenAI Analysis Layer
   - File-based pipeline
   - Groq LLM integration
   - Schema validation
   - Skip logic for existing summaries

3. Database Layer
   - SQLite (articles + article_analysis)
   - FTS5 search index
   
## Data Flow
[Diagrams]

## File Structure
backend/
├── app/
│   ├── db/          # Database layer
│   ├── ingestion/   # PubMed, Crossref connectors
│   ├── genai/       # Analysis pipeline
│   └── config/      # Topic queries
├── scripts/         # CLI tools
└── data/            # SQLite DB + analysis JSON files

## Technology Stack
- Python 3.11+
- Groq LLMs (llama-3.3-70b-versatile)
- SQLite + FTS5
- Biopython (PubMed)
```

#### 3. **DEVELOPMENT.md** (New)
**Purpose:** Setup, development, testing

**Contents:**
```markdown
# Development Guide

## Prerequisites
- Python 3.11+
- Virtual environment

## Installation
[Step by step]

## Environment Setup
[.env configuration]

## Running the System
### Ingestion
- Topic-based searches
- Custom queries
- Date filtering

### Analysis
- File-based pipeline
- Skip existing summaries
- Batch processing

## Testing
[Test commands]

## Troubleshooting
[Common issues]
```

#### 4. **ROADMAP.md** (New - from FUTURE_PIPELINE_PROPOSAL.md)
**Purpose:** Future plans

**Contents:**
```markdown
# Project Roadmap

## Current State (v1.0) ✅
- PubMed ingestion
- Groq LLM summarization
- File-based analysis
- Skip logic

## In Progress (v1.1)
- Evaluation pipeline
- Revalidation workflow
- Re-inference capabilities

## Planned (v2.0)
- RAG Q&A
- Citation networks
- Multi-document synthesis
- Web UI
- Advanced analytics

## Future (v3.0)
- Real-time monitoring
- Collaborative features
- API for external access
```

---

### Phase 2: Consolidate Documentation (Week 1)

#### Actions:

1. **Merge Topic Queries into README**
   - Source: TOPIC_QUERIES_GUIDE.md, TOPIC_QUERIES_COMPLETE.md
   - Target: README.md "Usage" section
   
2. **Merge Installation Guides**
   - Source: INSTALLATION.md, SETUP_COMPLETE.md
   - Target: DEVELOPMENT.md "Installation" section
   
3. **Extract Data Viewing**
   - Source: DATA_VIEWING_GUIDE.md
   - Target: docs/API_REFERENCE.md
   
4. **Consolidate GenAI Docs**
   - Source: docs/GENAI_SETUP.md, docs/GENAI_PIPELINE.md
   - Target: docs/GENAI_PIPELINE.md (keep only this)
   
5. **Extract Troubleshooting**
   - Source: All docs with "Troubleshooting" sections
   - Target: docs/TROUBLESHOOTING.md
   
6. **Create Data Sources Doc**
   - Source: README.md "Data Sources" section
   - Target: docs/DATA_SOURCES.md
   - Add: Why Crossref is disabled
   
7. **Rename Schema Mapping**
   - Source: docs/SCHEMA_MAPPING.md
   - Target: docs/SCHEMA_REFERENCE.md
   - Update: Current table structures only

---

### Phase 3: Archive Historical Docs (Week 1)

#### Create archive/ folder with README:

```markdown
# Archived Documentation

This folder contains historical documentation from project setup and early iterations.

## Why Archived?
These documents were useful during development but are now superseded by:
- README.md (current quick start)
- ARCHITECTURE.md (system design)
- DEVELOPMENT.md (setup guide)
- ROADMAP.md (future plans)

## Contents
- PROJECT_SUMMARY.md - Original v2.0 vision (scaled down to v1.0)
- IMPLEMENTATION_SUMMARY.md - Stage 1 completion status
- QUICK_START.md - Early quick start (now in README)
- MIGRATION_GUIDE.md - DocumentDB migration (not used)
- ... [all other archived docs]

## Useful Historical Info
- Original vision: See PROJECT_SUMMARY.md
- Stage 1/2 planning: See stage_1_2_implementation_plan.md
- Crossref rationale: Disabled due to no abstract availability
```

#### Move to archive/:
- PROJECT_SUMMARY.md
- QUICK_START.md
- IMPLEMENTATION_SUMMARY.md
- SETUP_COMPLETE.md
- TOPIC_QUERIES_GUIDE.md
- TOPIC_QUERIES_COMPLETE.md
- DATA_VIEWING_GUIDE.md
- INSTALLATION.md
- docs/MIGRATION_GUIDE.md
- docs/FUTURE_PIPELINE_PROPOSAL.md
- docs/GENAI_SETUP.md
- docs/PROJECT_STRUCTURE.md
- docs/IMPLEMENTATION_COMPLETE_STAGE_1_2.md
- docs/SKIP_ALREADY_SUMMARIZED.md (or move to code comments)
- docs/stage_1_2_implementation_plan.md
- docs/FOLDER_RENAME_SUMMARY.md

---

## 📊 Impact Analysis

### Before Cleanup
- **19 markdown files** (confusing, redundant)
- **Multiple sources of truth** (installation in 3+ places)
- **Outdated references** (Crossref active, v2.0 features)
- **Historical status docs** (setup complete, implementation complete)

### After Cleanup
- **9 markdown files** (clear purpose)
  - 4 in root (README, ARCHITECTURE, DEVELOPMENT, ROADMAP)
  - 5 in docs/ (specialized references)
- **Single source of truth** per topic
- **Current state only** (historical in archive/)
- **Clear next steps** (evaluation/revalidation)

### Benefits
✅ New contributors can onboard quickly (README → DEVELOPMENT)  
✅ Technical details are findable (ARCHITECTURE, docs/)  
✅ Future plans are clear (ROADMAP)  
✅ Historical context preserved (archive/)  
✅ No duplicate information  
✅ Reflects actual codebase state  

---

## 🚀 Implementation Steps

### Week 1: Core Documentation

**Day 1: Create new docs**
- [ ] Create ARCHITECTURE.md (system design)
- [ ] Create DEVELOPMENT.md (setup & development)
- [ ] Create ROADMAP.md (from FUTURE_PIPELINE_PROPOSAL.md)
- [ ] Create CHANGELOG.md (empty for now)

**Day 2: Update README.md**
- [ ] Remove Crossref from feature list (or mark as disabled)
- [ ] Remove Google Scholar references
- [ ] Add topic-based query examples
- [ ] Add file-based GenAI pipeline info
- [ ] Update quick start with current commands
- [ ] Link to new docs (ARCHITECTURE, DEVELOPMENT)

**Day 3: Create docs/ references**
- [ ] Create docs/API_REFERENCE.md (CLI + Python API)
- [ ] Create docs/DATA_SOURCES.md (PubMed, Crossref status)
- [ ] Create docs/TROUBLESHOOTING.md (extract from all docs)
- [ ] Rename docs/SCHEMA_MAPPING.md → docs/SCHEMA_REFERENCE.md
- [ ] Update docs/GENAI_PIPELINE.md (remove setup duplication)

**Day 4: Archive old docs**
- [ ] Create archive/ folder
- [ ] Create archive/README.md (index)
- [ ] Move all historical/duplicate docs to archive/
- [ ] Update any remaining links

**Day 5: Validation & cleanup**
- [ ] Check all internal links
- [ ] Verify no broken references
- [ ] Test quick start commands in README
- [ ] Remove truly obsolete files (like FOLDER_RENAME_SUMMARY.md)

---

## ✅ Success Criteria

1. **README.md accurately reflects current state**
   - No mentions of unimplemented features as active
   - Correct CLI examples
   - Clear next steps (evaluation/revalidation)

2. **New contributor can get started in 10 minutes**
   - Read README
   - Follow DEVELOPMENT.md setup
   - Run first command successfully

3. **Technical details are findable**
   - System design: ARCHITECTURE.md
   - API reference: docs/API_REFERENCE.md
   - Schema: docs/SCHEMA_REFERENCE.md
   - GenAI: docs/GENAI_PIPELINE.md

4. **No duplicate information**
   - Installation steps in ONE place (DEVELOPMENT.md)
   - Topic queries documented in ONE place (README.md)
   - GenAI setup in ONE place (docs/GENAI_PIPELINE.md)

5. **Clear project roadmap**
   - Current: v1.0 (ingestion + analysis)
   - Next: v1.1 (evaluation/revalidation)
   - Future: v2.0 (RAG, UI, citation networks)

---

## 💡 Quick Wins (Do First)

### Priority 1: Fix README.md (1 hour)
- Mark Crossref as disabled (commented in code)
- Remove Google Scholar (not implemented)
- Add topic query examples
- Add file-based analysis examples
- Link to proper docs

### Priority 2: Archive obvious duplicates (30 min)
- SETUP_COMPLETE.md → archive/
- TOPIC_QUERIES_COMPLETE.md → archive/
- IMPLEMENTATION_SUMMARY.md → archive/

### Priority 3: Create DEVELOPMENT.md (1 hour)
- Consolidate all installation instructions
- Add environment setup
- Add testing commands
- Add troubleshooting

---

## 📝 Notes

### Why Archive Instead of Delete?
- Historical context may be useful
- Git history is not easily browsable
- Original v2.0 vision may inform future work
- Implementation notes may help with debugging

### What About Code Comments?
Some .md files contain implementation details that belong in code:
- docs/SKIP_ALREADY_SUMMARIZED.md → Add comments in pipeline.py
- Stage planning → Remove (in Git history)

### Future Documentation Needs
After evaluation/revalidation implementation:
- docs/EVALUATION_GUIDE.md
- docs/REVALIDATION_GUIDE.md
- docs/REINFERENCE_GUIDE.md

---

## 🎯 Next Steps After Cleanup

1. **Review with stakeholders**
   - Does structure make sense?
   - Any missing information?

2. **Implement Phase 1** (create core docs)
   - Start with README.md update
   - Then ARCHITECTURE.md
   - Then DEVELOPMENT.md

3. **Implement Phase 2** (consolidate)
   - Merge duplicate content
   - Create specialized docs/

4. **Implement Phase 3** (archive)
   - Move historical docs
   - Create archive README
   - Clean up links

5. **Validate**
   - Test all commands in README
   - Check all doc links
   - Get feedback from new user

---

**Estimated Time:** 1 week (5 days)  
**Risk:** Low (only documentation, no code changes)  
**Impact:** High (much easier to understand and use project)

Ready to proceed with Phase 1?
