# Data Sources

**Last Updated:** 2026-07-30

This document provides detailed information about data sources, their status, capabilities, and limitations.

---

## Overview

The system is designed to ingest research articles from multiple scientific databases. Currently:

- ✅ **PubMed** - Active and primary source
- ⚠️ **Crossref** - Available but disabled (no abstracts)
- ❌ **Google Scholar** - Not implemented

---

## PubMed (NCBI) ✅

### Status
**ACTIVE** - Primary data source

### Overview
PubMed is a free search engine accessing primarily the MEDLINE database of references and abstracts on life sciences and biomedical topics. Maintained by the National Center for Biotechnology Information (NCBI) at the U.S. National Library of Medicine (NLM).

### Coverage
- **Total Articles:** 35+ million biomedical articles
- **Date Range:** 1946 to present
- **Update Frequency:** Daily
- **Content Type:** Journal articles, reviews, clinical trials
- **Full Text:** Links to full text when available
- **Abstracts:** Almost all articles include abstracts

### API Access
**E-utilities API** (Entrez Programming Utilities)

**Documentation:** https://www.ncbi.nlm.nih.gov/books/NBK25501/

**Endpoints Used:**
- `esearch.fcgi` - Search for PMIDs
- `efetch.fcgi` - Fetch article details

### Rate Limits
- **Without API Key:** 3 requests/second
- **With API Key:** 10 requests/second
- **Burst:** Short bursts allowed, but sustained rate must comply

**Recommendation:** Get an API key for production use (free)

### Getting an API Key

1. Create NCBI account: https://www.ncbi.nlm.nih.gov/account/
2. Go to Settings → API Key Management
3. Create new API key
4. Add to `.env` file:
   ```env
   NCBI_API_KEY=your-api-key-here
   NCBI_EMAIL=your-email@example.com
   ```

### Data Fields Available
- **PMID** - PubMed ID (unique identifier)
- **DOI** - Digital Object Identifier
- **Title** - Article title
- **Abstract** - Article abstract (usually available)
- **Journal** - Journal name
- **Authors** - List of authors with affiliations
- **Publication Date** - Date published
- **Keywords** - Author keywords
- **MeSH Terms** - Medical Subject Headings (controlled vocabulary)
- **Publication Types** - Article type (Journal Article, Review, Clinical Trial, etc.)
- **Country** - Extracted from first author affiliation

### Query Syntax

**Basic Search:**
```
tobacco harm reduction
```

**Boolean Operators:**
```
electronic cigarettes AND adolescents
IQOS OR HEETS OR "heated tobacco"
nicotine NOT smoking
```

**Field-Specific Search:**
```
"electronic cigarettes"[Title/Abstract]
Smith J[Author]
2024[Publication Date]
```

**Wildcards:**
```
cigarette*     # Matches cigarette, cigarettes, etc.
```

**Date Ranges:**
```
2024/01/01:2024/12/31[Publication Date]
```

### Best Practices

1. **Use Email in Requests** - Required by NCBI Terms of Service
   ```env
   NCBI_EMAIL=your-email@example.com
   ```

2. **Get API Key** - For faster rate limits (3x speedup)

3. **Batch Requests** - Fetch up to 200 articles per request

4. **Respect Rate Limits** - Don't exceed 10 req/sec even with API key

5. **Use Specific Queries** - More specific = better results
   ```
   Good: "IQOS"[Title/Abstract] AND "clinical trial"[Publication Type]
   Bad: IQOS
   ```

### Limitations

- **Rate Limits** - 3-10 req/sec maximum
- **No Full Text** - Only abstracts (links to full text provided)
- **Biomedical Focus** - Primarily medical/health sciences
- **English Bias** - Most articles in English
- **Indexing Delay** - New articles may take days to appear

### Cost
**FREE** - No charge for API access

---

## Crossref ⚠️

### Status
**DISABLED** - Code available but commented out

### Why Disabled?

During implementation, we discovered that Crossref API **does not return abstracts** for most articles. Since GenAI analysis requires abstracts to generate summaries, Crossref became unusable for our primary use case.

**Example:**
```json
{
  "DOI": "10.1234/example",
  "title": ["Article title"],
  "author": [...],
  "published-print": {"date-parts": [[2024, 1, 15]]},
  "abstract": null  // ❌ No abstract!
}
```

**Impact:** Without abstracts:
- Cannot generate meaningful summaries
- Cannot perform entity extraction
- Cannot analyze sentiment
- Cannot classify research

### When Crossref Might Be Useful

Crossref is still valuable for:
- **Citation data** - Who cited what
- **DOI resolution** - Convert DOI to metadata
- **Metadata enrichment** - Fill gaps in PubMed data
- **Full-text links** - Links to publisher pages

### Potential Future Use

Crossref could be re-enabled if:
1. **Full text scraping** added (from publisher links)
2. **Alternative use case** emerges (citation analysis, not summarization)
3. **Hybrid approach** - Crossref for metadata, other source for abstracts

### Current Implementation

Code exists in `backend/app/ingestion/crossref_connector.py` but is:
- Commented out in orchestrator
- Not exposed in CLI
- Documented as disabled

**To re-enable:**
1. Uncomment in `orchestrator.py`
2. Add back to CLI sources
3. Update documentation

### API Details (For Reference)

**Base URL:** https://api.crossref.org

**Documentation:** https://api.crossref.org/swagger-ui/index.html

**Rate Limits:**
- **Anonymous:** ~50 requests/second (polite pool)
- **With Email:** Same, but faster response
- **Recommendations:** Add email to User-Agent header

**Query Example:**
```bash
curl "https://api.crossref.org/works?query=tobacco+harm+reduction&rows=10"
```

**Data Fields Available:**
- DOI, title, authors, journal, publication date
- Citation count
- Subject keywords
- Links to full text (when available)
- **NOT abstracts** ❌

### Cost
**FREE** - No charge for API access

---

## Google Scholar ❌

### Status
**NOT IMPLEMENTED** - Planned for future

### Why Not Implemented Yet?

1. **No Official API** - Google Scholar has no official API
2. **Scraping Required** - Must scrape HTML pages
3. **Rate Limiting** - Aggressive anti-bot measures
4. **Legal Concerns** - Terms of Service prohibit scraping
5. **Reliability Issues** - Scrapers break when HTML changes

### Potential Implementation

**Option 1: Use scholarly library**
```python
from scholarly import scholarly

# Search for articles
search_query = scholarly.search_pubs('tobacco harm reduction')
articles = list(search_query)
```

**Limitations:**
- Very slow (~100 articles/hour)
- Frequently blocked
- Requires proxies
- Against ToS

**Option 2: Use SerpAPI**
- Commercial API for Google Scholar
- $50-200/month
- Legal and reliable
- Rate limits apply

**Option 3: Wait for Official API**
- Google has not announced plans for Scholar API
- Unlikely in near future

### Coverage (If Implemented)

- **Total Articles:** 500+ million
- **Date Range:** Varies widely
- **Content Type:** Articles, books, theses, conference papers
- **Full Text:** Sometimes available
- **Abstracts:** Usually available
- **Unique Strength:** Includes non-PubMed sources

### Current Status

- Code stubbed out in `backend/app/ingestion/` (placeholder)
- Not exposed in CLI
- Documentation references removed

### Future Plans

**v2.0 Roadmap:**
- Evaluate SerpAPI vs scholarly
- Implement if cost-benefit favorable
- Focus on articles not in PubMed

---

## Data Source Comparison

| Feature | PubMed | Crossref | Google Scholar |
|---------|--------|----------|----------------|
| **Status** | ✅ Active | ⚠️ Disabled | ❌ Not Implemented |
| **Coverage** | 35M+ | 130M+ | 500M+ |
| **Abstracts** | ✅ Yes | ❌ No | ✅ Yes (usually) |
| **API** | ✅ Official | ✅ Official | ❌ No |
| **Rate Limit** | 3-10 req/sec | 50 req/sec | ~100/hour (scraped) |
| **Cost** | FREE | FREE | $50-200/month (SerpAPI) |
| **Quality** | High | High | Variable |
| **Biomedical Focus** | ✅ Yes | ✅ Partial | ❌ No |
| **Citation Data** | Limited | ✅ Excellent | ✅ Excellent |
| **Full Text** | Links only | Links only | Sometimes |

---

## Recommended Strategy

### Current (v1.0)
**Use PubMed exclusively** for:
- Tobacco harm reduction research
- Medical/health sciences
- High-quality peer-reviewed articles

### Future (v1.1+)
**Add Crossref** for:
- Citation network analysis
- DOI resolution
- Metadata enrichment

### Future (v2.0+)
**Add Google Scholar** via SerpAPI for:
- Conference proceedings
- Theses and dissertations
- Non-PubMed journals
- Broader coverage

---

## Query Strategy by Topic

### Heat-Not-Burn (IQOS, HEETS, THS)
**Best Source:** PubMed  
**Why:** Medical focus, most HTP research is biomedical  
**Query:** Complex query covering product names, see `search_queries.json`

### E-Cigarettes / Vaping
**Best Source:** PubMed  
**Why:** Extensive coverage, medical focus  
**Alternative:** Google Scholar for non-medical perspectives

### Nicotine Pouches
**Best Source:** PubMed  
**Why:** Emerging research area, medical focus  
**Note:** Limited articles available

### Snus / Smokeless Tobacco
**Best Source:** PubMed  
**Why:** Long research history, medical focus  
**Alternative:** Google Scholar for Swedish studies

---

## Data Quality Considerations

### PubMed
**Strengths:**
- Peer-reviewed articles
- High-quality abstracts
- Consistent metadata
- MeSH term indexing

**Weaknesses:**
- Biomedical bias
- English language bias
- Indexing delay (days)

### Missing Data Handling

**No Abstract:**
- Skip article (cannot analyze)
- Log as "no abstract available"

**No Author Affiliations:**
- Country extraction may fail
- Industry affiliation detection may fail

**No Keywords:**
- Rely on MeSH terms
- Or extract from title/abstract

**Invalid Date:**
- Use publication year only
- Log warning

---

## Future Data Sources (Under Consideration)

### bioRxiv / medRxiv
**Preprint servers** for biomedical research
- Earlier access to research
- Not peer-reviewed
- Growing importance

### Europe PMC
**European equivalent** of PubMed
- Similar coverage
- Additional European journals
- Free API

### Web of Science / Scopus
**Citation databases**
- Excellent for citation analysis
- Expensive ($$$)
- Academic institution access

### Institutional Repositories
**University collections**
- Theses and dissertations
- Working papers
- Variable quality

---

## Data Ingestion Best Practices

1. **Start with PubMed** - Best quality, most reliable
2. **Use Topic Queries** - Pre-optimized for coverage
3. **Set Date Ranges** - Control volume and relevance
4. **Monitor Rate Limits** - Respect API terms
5. **Validate Data** - Check for missing abstracts
6. **Log Failures** - Track what couldn't be ingested
7. **Deduplicate** - Same article may appear multiple times
8. **Enrich Metadata** - Add country, affiliations from text

---

**For implementation details:**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
- [API_REFERENCE.md](API_REFERENCE.md) - CLI commands
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Setup and development
