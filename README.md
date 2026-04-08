# Spark Outreach

A complete local SaaS-style outreach platform with company profile enrichment, website scraping, semantic embeddings, AI-assisted retrieval, and a React-based admin UI.

## Project Summary

Spark Outreach combines:

- a FastAPI backend for company profiles, scraping, embeddings, and AI services
- a React + TypeScript frontend for auth, profile setup, campaign/lead management, and embedding validation
- MongoDB for persistent user, company, campaign, and lead data
- local semantic embedding generation using `sentence-transformers`

The system is designed to turn company profile data and website content into searchable, queryable knowledge for outreach and lead targeting.

---

## What the System Does

- Collects and stores company profile details
- Scrapes company websites and portfolio sources for real business content
- Generates rich 768-dimensional semantic embeddings locally
- Enables natural language company profile querying
- Provides a frontend testing UI for embedding quality
- Supports campaign and lead workflows with AI-assisted message generation

---

## Lead Discovery and Search

Spark Outreach is designed to go beyond static contacts and generate real company leads from public web signals.

### How we find leads

- The lead search service constructs a targeted discovery query from:
  - user-selected location and industry filters
  - service offerings and technology keywords
  - company profile context and target markets
- The backend scrapes public search results from DuckDuckGo and Bing HTML pages.
- Candidate URLs are filtered to exclude directories, listicles, job boards, review sites, and low-value domains.
- For each candidate company website, the system:
  - fetches the homepage and high-priority internal pages (About, Services, Solutions, Team, Portfolio)
  - extracts clean business content and removes menu/footer noise
  - captures metadata like company name, email, phone, summary, and website URL
- Discovered leads are stored with raw discovery metadata, quality scores, and a source URL.

### How we search leads

- Lead search leverages semantic embeddings and company fit scoring.
- The search endpoint is `POST /api/v1/leads/search`.
- Inputs include:
  - natural language `query`
  - optional `filters` such as `location`, `industry`, `services`, and `company_sizes`
  - optional `campaign_id` and sort settings
- The service re-discovers leads for every search to reflect changing query/filter combinations.
- Each lead is scored on:
  - company profile fit vs. the current user/company context
  - growth and hiring signals detected in the scraped content
  - semantic relevance to the user query
- Search results include contact-oriented lead fields such as email, phone, website, company name, industry, and fit/signal scores.

### Lead quality controls

- The pipeline rejects noise pages with terms like "top 10", "list of", "jobs", and "rankings".
- It skips known low-value domains such as Crunchbase, Clutch, Glassdoor, and other directory/review sources.
- It prefers actual company profile pages and business websites over generic headline or list pages.
- Leads are enriched with company summary and contact signals when available.

---

## Backend Overview

### Core Backend Files

- `backend/app/main.py`
  - FastAPI app bootstrap
  - CORS middleware
  - root and health endpoints
  - router registration for auth, campaigns, leads, AI, and company

- `backend/app/config.py`
  - environment and configuration settings

- `backend/app/database.py`
  - MongoDB initialization and cleanup

### Routers

- `backend/app/routers/auth.py`
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`

- `backend/app/routers/company.py`
  - `POST /api/v1/company/profile`
  - `GET /api/v1/company/profile`
  - `PUT /api/v1/company/profile`
  - `POST /api/v1/company/profile/generate-embeddings`
  - `POST /api/v1/company/profile/query`
  - `POST /api/v1/company/profile/generate-icp`
  - `POST /api/v1/company/profile/complete-setup`

- `backend/app/routers/campaigns.py`
  - campaign CRUD and campaign operations

- `backend/app/routers/leads.py`
  - lead CRUD, bulk import, contact actions, and lead status management

- `backend/app/routers/ai.py`
  - `POST /api/v1/ai/rag-search`
  - `POST /api/v1/ai/generate-message`
  - `POST /api/v1/ai/create-embeddings`

### Services

- `backend/app/services/company_service.py`
  - create/update company profile
  - build embedding text from profile and portfolio content
  - generate company embeddings locally
  - query company profile using embeddings
  - generate ICP / signal keywords
  - complete setup flow

- `backend/app/services/ai_service.py`
  - local embedding generation using `sentence-transformers`
  - query embeddings and similarity search
  - AI text completion support (optional Gemini/OpenAI)

- `backend/app/services/web_scraper.py`
  - homepage and internal page scraping
  - prioritized link extraction for About / Services / Solutions / Team pages
  - HTML cleaning to remove navigation, footer, modal, and menu noise
  - portfolio content aggregation from website, GitHub, LinkedIn, Upwork, and extra URLs

- `backend/app/services/campaign_service.py`
  - campaign data handling and business logic

- `backend/app/services/lead_service.py`
  - lead creation, update, and management logic

### Models

- `backend/app/models/user.py`
  - user account fields and authentication data

- `backend/app/models/company.py`
  - company profile fields, portfolio data, content cache, and embeddings

- `backend/app/models/campaign.py`
  - campaign metadata and status

- `backend/app/models/lead.py`
  - lead contact details and lifecycle status

- `backend/app/models/embedding.py`
  - optional saved embedding metadata

### Schemas

- `backend/app/schemas/user.py`
  - auth request/response models

- `backend/app/schemas/company.py`
  - company profile and query schemas

- `backend/app/schemas/campaign.py`
  - campaign request/response models

- `backend/app/schemas/lead.py`
  - lead request/response models

### Utilities

- `backend/app/utils/auth.py`
  - JWT handling, password hashing, and token validation

- `backend/app/utils/embeddings.py`
  - embedding helper utilities and chunking

- `backend/app/utils/response.py`
  - response serialization helpers

---

## Frontend Overview

### Core Frontend Files

- `src/main.tsx`
  - app bootstrap and rendering

- `src/App.tsx`
  - main routes and layout shell

- `src/index.css`, `src/App.css`
  - global styles and Tailwind config

- `src/services/api.ts`
  - centralized API client for auth, campaigns, leads, AI, and company endpoints
  - automatic Bearer token injection

### UI and Pages

- `src/pages/Index.tsx` — landing page
- `src/pages/Login.tsx` — login form
- `src/pages/Register.tsx` — registration form
- `src/pages/Dashboard.tsx` — dashboard overview
- `src/pages/CompanySetup.tsx` — company onboarding and profile setup
- `src/pages/Campaigns.tsx` — campaign management
- `src/pages/NewCampaign.tsx` — campaign creation
- `src/pages/ReviewQueue.tsx` — outreach review queue
- `src/pages/Prospects.tsx` — prospect list page
- `src/pages/LeadDashboard.tsx` — lead workspace
- `src/pages/LeadDetail.tsx` — lead detail page
- `src/pages/LeadResults.tsx` — lead results view
- `src/pages/LeadSearch.tsx` — lead search interface
- `src/pages/LeadSettings.tsx` — lead settings
- `src/pages/Settings.tsx` — user settings and embedding test console
- `src/pages/Analytics.tsx` — analytics and reporting
- `src/pages/AILearning.tsx` — AI insights and learning section
- `src/pages/NotFound.tsx` — 404 page

### Components

- `src/components/NavLink.tsx` — navigation link helper
- `src/components/ThemeProvider.tsx` — theme context provider
- `src/components/dashboard/` — dashboard layout components
- `src/components/landing/` — landing page sections
- `src/components/ui/` — shared UI primitives and shadcn/ui components

### State and Helpers

- `src/contexts/` — auth and global app contexts
- `src/hooks/` — custom hooks used by pages
- `src/lib/` — utility functions shared across the frontend

---

## Embedding and AI Details

- Local semantic model: `paraphrase-mpnet-base-v2`
- Embeddings are generated locally with `sentence-transformers`
- Company profile text is built from:
  - manual profile fields
  - services, expertise, technologies, industries, projects
  - website and portfolio content
  - GitHub / LinkedIn / Upwork signals
- Query against company profile uses embedding similarity plus exact keyword boosting for terms such as `.NET`, Azure, and Power Platform
- ICP generation uses completion prompt logic, with safe fallback handling if external AI completion is unavailable

---

## Setup Instructions

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create or update `backend/.env` with:

```env
APP_NAME=Spark Outreach API
DEBUG=True
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=spark_outreach
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=
OPENAI_API_KEY=
HF_API_KEY=
```

Run the backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
npm install
npm run dev
```

Open the frontend app at the Vite URL shown in the terminal, usually `http://localhost:5173`.

---

## Key API Endpoints

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Company

- `POST /api/v1/company/profile`
- `GET /api/v1/company/profile`
- `PUT /api/v1/company/profile`
- `POST /api/v1/company/profile/generate-embeddings`
- `POST /api/v1/company/profile/query`
- `POST /api/v1/company/profile/generate-icp`
- `POST /api/v1/company/profile/complete-setup`

### AI

- `POST /api/v1/ai/rag-search`
- `POST /api/v1/ai/generate-message`
- `POST /api/v1/ai/create-embeddings`

### Campaigns / Leads

- campaign and lead routes are available under `/api/v1/campaigns` and `/api/v1/leads`
- lead discovery/search endpoint: `POST /api/v1/leads/search`

---

## How to Use the Embedding Test

- Create or update a company profile
- Generate embeddings via backend or profile flow
- Open `Settings` and go to `Embedding Test`
- Enter a question about the company
- Run the test and review returned chunk text with scores

---

## Project Structure

- `backend/` — backend application code, models, schemas, services, and routers
- `src/` — frontend source code, pages, components, contexts, and API client
- `public/` — static web assets
- `package.json` — frontend dependencies and scripts
- `backend/requirements.txt` — backend Python dependencies
- `README.md` — project documentation

---

## Notes

- The web scraper is intentionally tuned to avoid navigation/menu noise and prioritize actual company content.
- External sources such as LinkedIn and Upwork may fail to scrape due to anti-bot restrictions; fallback signals are preserved.
- The local embedding pipeline does not require a paid API key, but optional AI completion features may use Gemini/OpenAI when configured.
- Use the frontend settings UI to validate embeddings before relying on retrieval results.

---

This README now documents the current system end-to-end, including backend architecture, frontend pages, AI/embedding behavior, and setup instructions.