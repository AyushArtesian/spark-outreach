# Spark Outreach Backend

**Enterprise-grade Python backend for AI-powered lead discovery and outreach automation.** Combines intelligent web scraping, LLM-based query planning, semantic lead scoring, and multi-channel outreach orchestration.

## 🎯 Core Features

### Lead Discovery & Enrichment
- **Intelligent Web Scraping**: Extract company websites with smart filtering (SaaS/product companies vs service providers)
- **LLM-Powered Query Planning**: Groq/Qwen generates prospect-finding queries using company context embeddings
- **Multi-Source Discovery**: Apollo, Serper/SerpAPI web search, job boards with fallback routing
- **Company Enrichment**: Automatic tech stack, decision-maker, signal detection via Apollo + web scraping
- **Hard Buyer Filtering**: Competitor/non-buyer disqualification gates at discovery and scoring stages

### AI/ML Capabilities  
- **Semantic Embeddings**: Paraphrase-MPN-Base (768D embeddings) for company context retrieval
- **RAG Pipeline**: Retrieve→Plan→Search→Score workflow with company context integration
- **Multi-LLM Support**: Groq (Qwen), OpenAI, Gemini with configurable inference parameters
- **Lead Scoring**: Transparent 0-100 score card (Company Fit 40 + Buyer Signals 40 + Accessibility 20)
- **Personalized Outreach**: Email/message generation using retrieved company context

### Infrastructure
- **FastAPI + Async**: High-performance REST API with full async/await support
- **MongoDB**: Document-based storage for flexible schema and embeddings
- **Rate Limiting & Exponential Backoff**: Graceful handling of API rate limits and network failures
- **SSL Fallback + User-Agent Rotation**: Anti-bot resilience with adaptive retry strategies

## 📋 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI 0.104+ with Uvicorn |
| **Database** | MongoDB (primary), SQLAlchemy ORM for migrations |
| **Auth** | JWT (python-jose), Bcrypt password hashing |
| **LLM Providers** | Groq API (Qwen 3.2 32B), OpenAI, Google Gemini |
| **Embeddings** | Sentence Transformers (paraphrase-mpnet-base-v2, 768D) |
| **Search APIs** | Serper, SerpAPI with fallback chain |
| **Data Validation** | Pydantic v2 |
| **Web Scraping** | BeautifulSoup4 + aiohttp with async HTML parsing |
| **Config** | Python-dotenv with Pydantic settings |

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI app initialization & routes binding
│   ├── config.py                        # Pydantic settings, env vars, constants
│   ├── database.py                      # MongoDB connection & session management
│   │
│   ├── models/                          # Data models (Mongoose-style)
│   │   ├── user.py                     # User authentication & profile
│   │   ├── campaign.py                 # Campaign definition & settings
│   │   ├── lead.py                     # Lead storage with raw_data payloads
│   │   ├── company.py                  # Company profiles + embeddings
│   │   └── embedding.py                # Chunk embeddings for RAG
│   │
│   ├── schemas/                         # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── campaign.py
│   │   ├── lead.py
│   │   ├── company.py
│   │   └── query_schemas.py            # LLM query planning schemas
│   │
│   ├── routers/                         # API route handlers (grouped by resource)
│   │   ├── auth.py                     # Auth: register, login, me
│   │   ├── campaigns.py                # Campaigns: CRUD + analytics
│   │   ├── leads.py                    # Leads: search, enrich, score, generate email
│   │   ├── company.py                  # Company: profile, context, embeddings
│   │   └── ai.py                       # AI ops: RAG, embeddings, scoring
│   │
│   ├── services/                        # Business logic & algorithms
│   │   ├── lead_service.py             # Lead discovery, filtering, constraint matching
│   │   ├── web_scraper.py              # Web scraping, domain validation, signal analysis
│   │   ├── ai_service.py               # LLM query planning, embedding generation
│   │   ├── apollo_service.py           # Apollo CRM API integration
│   │   ├── company_service.py          # Company context retrieval & enrichment
│   │   ├── query_generator.py          # Deterministic high-intent query generation
│   │   ├── query_scorer.py             # Query relevance ranking
│   │   ├── email_generator.py          # Personalized email template generation
│   │   ├── enrichment_service.py       # Tech stack & decision-maker enrichment
│   │   ├── campaign_service.py         # Campaign operations
│   │   ├── intent_monitor.py           # Real-time intent signal detection
│   │   ├── jobboard_service.py         # Job board integrations
│   │   ├── llm_provider.py             # LLM provider abstraction (Groq, OpenAI, Gemini)
│   │   ├── service_catalog.py          # Service inference & mapping
│   │   └── service_catalog.py          # Service type inference from text
│   │
│   ├── utils/                           # Utility functions & helpers
│   │   ├── auth.py                     # JWT token generation & validation
│   │   ├── embeddings.py               # Embedding service wrapper
│   │   ├── json_utils.py               # JSON parsing with fallbacks
│   │   └── response.py                 # Standard response formatting
│   │
│   └── __init__.py
│
├── requirements.txt                     # Python 3.13+ dependencies
├── manage_db.py                         # Database management script
├── route_inspect.py                     # Route introspection utility
├── test_*.py                            # Test files (pytest)
├── .env.example                         # Example environment configuration
├── .gitignore
└── README.md                            # This file
```

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.13+** (async features, performance)
- **MongoDB 5.0+** (document storage)
- **API Keys**: Groq, Serper/SerpAPI, Apollo (optional)

### 1. Clone & Environment Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy and edit configuration
cp .env.example .env
```

**Critical Environment Variables:**

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=spark_outreach

# JWT & Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_EXPIRATION_HOURS=72
DEBUG=False

# LLM Configuration
LLM_PROVIDER=groq                          # groq | openai | gemini
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=qwen/qwen3-32b
GROQ_TEMPERATURE=0.0                       # Deterministic output
GROQ_MAX_TOKENS=2048

# Search APIs
SERPER_API_KEY=your-serper-key
SERPAPI_KEY=your-serpapi-key

# Optional Integrations
APOLLO_API_KEY=your-apollo-key
OPENAI_API_KEY=your-openai-key

# Feature Flags
LEAD_QUERY_PLANNER_ENABLED=true
LEAD_QUERY_PLANNER_MAX_QUERIES=7
ENABLE_COMPANY_ENRICHMENT=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Initialize Database

```bash
# Create collections & indexes
python -c "from app.database import init_db; init_db()"
```

### 5. Run Backend

```bash
# Development (with auto-reload & debug)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With worker processes
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

**API Access:**
- RESTful API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

---

## 🌐 Web Scraper Service (`web_scraper.py`)

**Intelligent company website discovery and analysis with anti-bot resilience.**

### Core Capabilities

#### 1. **High-Intent Query Validation** (`_is_valid_planned_query`)
Filters LLM-generated queries to ensure execution quality:
- Min 4 words (reduced from 5) to catch concise queries
- Intent trigger matching (30+ signals): "hiring", "funded", "venture backed", "expanding", "digital transformation", etc.
- Balanced quote matching: Rejects malformed queries with unmatched quotes
- Location check optional: Queries can succeed without explicit location
- **Returns**: Boolean (query is executable)

#### 2. **Business Signal Analysis** (`analyze_business_signals`)
Deep signal detection on company content:

**Signal Categories** with confidence weights:
- **hiring** (0.30): "hiring", "open positions", "careers page", "now hiring"
- **scaling** (0.25): "scaling", "hypergrowth", "expanding", "rapid growth"
- **saas_platform** (0.22): "saas", "subscription", "multi-tenant", "product-led"
- **tech_heavy** (0.18): "api", "microservices", "devops", "backend", "cloud"
- **funding** (0.15): "series a", "vc funded", "venture capital", "raised funding"

**Service Relevance**: 0.25 base + 0.15 per matching service token (max 1.0)

**Semantic Bonuses**:
- `+0.18` for product indicators ("SaaS", "startup", "series a")
- `+0.10` for mid-strength indicators ("platform", "subscription")
- `-0.20` for service provider red flags ("outsourcing", "staff augmentation")

#### 3. **URL Content Fetching** (`_fetch_html` / `fetch_url_content`)
Robust async HTML retrieval with exponential backoff:
- **Retry strategy**: Max 3 retries with 0.5s × 2^attempt backoff
- **User-agent rotation**: Cycles through 3 popular UAs
- **SSL fallback**: Retries without SSL if cert fails
- **Rate limit handling**: 429 → wait & retry; 403 → skip
- **Timeout**: 12s with async cancellation

#### 4. **HTML Cleaning** (`_clean_html`)
Extracts relevant company text while removing noise:
- Removes nav/script/style/footer/header elements
- Prioritizes main, article, section.content blocks
- Filters single-word lines and nav phrases
- Result: Clean, paragraph-separated text for embeddings

#### 5. **Candidate Result Validation** (`_append_candidate_result`)
Multi-stage filtering to eliminate service providers & aggregators:

**Hard Blocks**:
- Low-value domains: crunchbase, g2, clutch, glassdoor, naukri, indeed, etc.
- Competitor domains: toptal, infosys, upwork, fiverr, etc.
- Path patterns: `/list`, `/jobs`, `/rank`, `/compare`
- Title patterns: "Top 100", "List of", job listings

**Service Provider Rejection** (Strict Gate):
```
IF (service_provider_keywords >= 1):
    IF (product_signals == 0):
        REJECT
    ELIF (product_signals == 1 AND "platform" NOT IN text):
        REJECT
    ELSE:
        ALLOW  (multiple strong product signals override)
```

#### 6. **Query Generation** (`generate_high_intent_queries`)
Context-aware deterministic queries:

**Two Modes**:
- **Provider Focus**: Queries for companies BUILDING solutions
  - "ecommerce solution providers mohali"
  - "custom ecommerce development companies"
  
- **Buyer Focus**: Queries for companies HIRING
  - "fintech companies hiring backend developers"
  - "venture backed saas startups"
  - "series a startups hiring engineers"

Features: 10-15 templates/mode, auto-deduplication, fallback generation

#### 7. **Web Search Integration** (`discover_company_websites`)
Main orchestration combining all pieces:

**Workflow**:
1. Validate/normalize LLM queries (accept/reject counting)
2. Generate heuristic fallback if < 2 LLM queries
3. Execute searches via SerpAPI (fallback to Serper)
4. Retry with relaxed query if zero results
5. Track zero-result streaks for adaptation
6. Validate domains and filter via `_append_candidate_result`
7. Return deduplicated results (max 20)

**Rate Handling**: 1.5s delay between queries, exponential backoff on errors

---

## 🤖 AI Service (`ai_service.py`)

**LLM query planning, embedding generation, and intelligent fallbacks**

### `plan_lead_discovery_queries()`
Main entry point for context-aware query planning:

**Workflow**:
1. Retrieve company context (5 chunks via embeddings)
2. Build strict planner constraints from request filters (especially `location`)
3. Call Groq and parse JSON/fallback text safely
4. Post-filter each query with hard guards:
   - must include the exact requested location
   - must not include other city/country tokens
   - must avoid vendor/agency finder intent
   - must pass executable/live-market checks
5. Rank candidate queries via `query_scorer`
6. If quality/effectiveness is low, run one refinement pass
7. If needed, merge deterministic fallback queries (also passed through the same hard post-filter)
8. Return only accepted queries

**Current Planner Guardrails**:
- `CRITICAL: ALL search queries MUST target this exact location`
- Never generate queries for other city/country
- Never generate queries that find IT vendors/software agencies
- Only generate queries for companies that BUY tech services

---

## 🔍 Lead Service (`lead_service.py`)

**Orchestration of discovery, filtering, scoring, and final ranking**

### Discovery Pipeline
1. Run source collectors: Apollo, web search, and jobboard intent discovery.
2. Merge candidates and pre-save dedupe by identity.
3. Apply hard gates before save:
   - duplicate domain/contact rejection
   - competitor disqualification (`DISQUALIFY_TYPES`, `DISQUALIFY_KEYWORDS`, domain token rules)
   - non-buyer/service-provider rejection (directory/listing/job-portal/agency-style entities)
   - source-specific quality + signal thresholds
4. Persist survivors with `raw_data.search_key` for search-intent scoping.

### Search Scope
- Compute deterministic search key from `(location, industry, services, query)`.
- Prefer records matching current `search_key`.
- Fallback to recent-window leads only when scoped matches are absent.

### Scoring-Time Hard Filters
Before score calculation, each lead is re-checked and can be skipped as:
- `skipped_constraints`
- `skipped_competitor`
- `skipped_non_buyer`

### Scoring Model (Current)
`total_score = company_fit(0-40) + buyer_signal_strength(0-40) + accessibility(0-20)`

Grade/action mapping:
- `A` (`>=80`) → `contact_immediately`
- `B` (`>=60`) → `add_to_sequence`
- `C` (`>=40`) → `nurture`
- `D` (`<40`) → `skip`

### Final Ranking + Dedupe
- Rank by combined score (or requested sort mode).
- Keep only best record per normalized identity key.
- Summary logs expose `collapsed_duplicates` and all skip counters.

---

## 📊 Complete API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login & get JWT
- `GET /api/v1/auth/me` - Get current user

### Campaigns  
- `POST /api/v1/campaigns` - Create campaign
- `GET /api/v1/campaigns` - List campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign details
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `POST /api/v1/campaigns/{id}/start` - Start campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign

### Leads
- `POST /api/v1/leads/search` - **Search leads with LLM query planning**
- `POST /api/v1/leads` - Create lead
- `POST /api/v1/leads/bulk` - Bulk create
- `GET /api/v1/leads/{id}` - Get lead details
- `GET /api/v1/leads/campaign/{id}` - List campaign leads
- `PUT /api/v1/leads/{id}` - Update lead
- `POST /api/v1/leads/{id}/enrich` - Enrich with company data
- `POST /api/v1/leads/{id}/generate-email` - Generate email
- `DELETE /api/v1/leads/{id}` - Delete lead

### Lead Search Workflow
**`POST /api/v1/leads/search`** (Main orchestration):
```json
{
  "campaigns": ["campaign_id"],
  "location": "mohali",
  "industry": "fintech",
  "services": ["web app development"],
  "use_query_planner": true
}
```

**Workflow**:
1. Load company profile and retrieve context chunks for planning.
2. Generate LLM queries with strict constraints:
   - exact target location only
   - no other city/country
   - buyer-company intent only (not IT vendor/agency discovery)
3. Post-filter generated queries (location fence + geo rejection + intent checks).
4. Discover candidates across Apollo + web + jobboard sources.
5. Run discovery-time hard filters and save only valid survivors.
6. Scope candidates by `search_key` for this exact search intent.
7. Re-filter at scoring time (`constraints`, `competitor`, `non_buyer`).
8. Score with `company_fit + buyer_signal_strength + accessibility`.
9. Rank, dedupe, and return top-K leads.

---

## ⚙️ Core Configuration

### Environment Variables (Complete)

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=spark_outreach

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=72
DEBUG=False

# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3-32b
GROQ_TEMPERATURE=0.0
GROQ_MAX_TOKENS=2048

# Search APIs
SERPER_API_KEY=...
SERPAPI_KEY=...

# Integrations
APOLLO_API_KEY=...
OPENAI_API_KEY=...

# Feature Flags
LEAD_QUERY_PLANNER_ENABLED=true
LEAD_QUERY_PLANNER_MAX_QUERIES=7
ENABLE_COMPANY_ENRICHMENT=true

# Web Scraper
MAX_INTERNAL_PAGES=25
REQUEST_TIMEOUT=12
REQUEST_DELAY=1.5

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test with coverage
pytest --cov=app tests/

# Test specific module
pytest tests/services/test_web_scraper.py -v
```

---

## 🔐 Security Best Practices

⚠️ **Critical**:
1. Change `SECRET_KEY` in production
2. Use HTTPS only in production
3. Rotate API keys quarterly
4. Store secrets in secure vaults (AWS Secrets Manager, HashiCorp Vault)
5. Use strong MongoDB credentials
6. Implement rate limiting for production
7. Enable CORS only for trusted origins
8. Update dependencies weekly

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `uvicorn app.main:app --port 8001` |
| MongoDB connection failed | Verify `MONGODB_URL` and server running |
| Groq API errors | Check API key, model name, rate limits |
| Web scraper timeout | Increase `REQUEST_TIMEOUT` or limit internal pages |
| No leads found | Check query planner logs; may need relaxed location gates |
| Too many similar/duplicate leads | Inspect scoring summary counters: `collapsed_duplicates`, `skipped_competitor`, `skipped_non_buyer`, and confirm `search_key` scoping is active |

---

## 📈 Performance Optimization

### Query Optimization
- Use async/await for all I/O
- Implement connection pooling for MongoDB
- Cache embeddings in MongoDB
- Use selective field queries (projection)

### Rate Limiting
- Default delays: 1.5s between web queries
- Exponential backoff: 0.5s × 2^attempt
- Max 3 retries per query
- Graceful fallback on 429/503 errors

### Scaling Considerations
- Horizontal: Deploy multiple workers with Gunicorn
- Vertical: Increase MongoDB replica set size
- Caching: Consider Redis for frequently-accessed leads
- Queueing: Use Celery for long-running tasks (future)

---

## 🚀 Deployment

### Docker
```bash
docker build -t spark-outreach-backend:latest .
docker run -p 8000:8000 --env-file .env spark-outreach-backend:latest
```

### Production Checklist
- [ ] Change SECRET_KEY
- [ ] Enable HTTPS with SSL/TLS
- [ ] Set DEBUG=False
- [ ] Use managed MongoDB (MongoDB Atlas)
- [ ] Configure CORS origins
- [ ] Set up logging/monitoring (ELK, DataDog)
- [ ] Enable database backups
- [ ] Configure rate limiting
- [ ] Use environment-specific configs

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Groq API**: https://console.groq.com
- **Serper API**: https://serper.dev
- **MongoDB Docs**: https://docs.mongodb.com
- **Sentence Transformers**: https://www.sbert.net

---

## 📝 License

TODO: Add license

## 🤝 Support

**Issues**: Create an issue in the repository
**Documentation**: See `/docs` folder
**Contributing**: Follow PEP 8 + add tests for new features
