# Spark Outreach

Spark Outreach is a local SaaS-style outreach platform that combines company profile enrichment, web discovery, semantic embeddings, AI-assisted search, and a React admin UI.

## What Spark Outreach Does

- Builds and stores company profile data, services, expertise, technologies, industries, and target markets
- Discovers real company leads from search results using SerpAPI and intelligent website scraping
- Generates local semantic embeddings using `sentence-transformers`
- Scores leads based on company profile fit, growth signals, and query relevance
- Provides campaign and lead workflows for outreach and follow-up
- Offers AI-assisted message generation, RAG-style search, and embedding quality validation

---

## Key Features

- FastAPI backend with MongoDB persistence
- React + TypeScript frontend with campaign, lead, and company profile management
- Local semantic model pipeline using `paraphrase-mpnet-base-v2`
- Lead discovery tuned to avoid low-value domains, directories, listicles, and job boards
- Provider-focused query generation for industry-specific services
- Search scoring that prioritizes company profile embeddings and business signals

---

## Architecture Overview

### Backend

- `backend/app/main.py` — FastAPI application bootstrap and router registration
- `backend/app/config.py` — environment-backed configuration
- `backend/app/database.py` — MongoDB startup and connection handling
- `backend/app/routers/` — auth, company, campaign, lead, and AI routes
- `backend/app/services/` — business logic for company profiles, lead discovery, scraping, embeddings, campaigns, and AI
- `backend/app/models/` — MongoDB document models
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/utils/` — reusable helpers for auth, embeddings, and responses

### Frontend

- `src/main.tsx` — app bootstrap
- `src/App.tsx` — route layout and page rendering
- `src/pages/` — auth, dashboard, company setup, campaigns, lead search, review queue, and settings
- `src/components/` — reusable UI and layout components
- `src/services/api.ts` — centralized API client
- `src/hooks/` — custom React hooks

---

## Lead Discovery & Search

Spark Outreach discovers leads using search-engine results and website scraping, then ranks them using company profile context.

### Discovery workflow

- The backend creates targeted search queries from industry, location, service focus, and company profile keywords
- It uses SerpAPI to retrieve search result URLs
- It filters out low-value results such as directories, review sites, rankings pages, and generic job boards
- It scrapes each candidate website for business content, contact details, and summary text
- It stores discovered leads with raw metadata, quality signals, and discovery relevance

### Search scoring

- Leads are scored using:
  - `company_fit` from company profile embeddings
  - growth/hiring signals detected on the page
  - semantic relevance to the current search query
- The search endpoint is: `POST /api/v1/leads/search`
- Search supports filters such as `location`, `industry`, `services`, and `campaign_id`

---

## Setup Instructions

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create or update `backend/.env` with the following values:

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
SERPAPI_KEY=
SERPER_API_KEY=
REDIS_URL=
```

Notes:
- `SERPAPI_KEY` is required for lead discovery and search discovery results.
- `HF_API_KEY` is optional for Hugging Face inference access.
- `HF_TOKEN` can also be used to speed up model downloads from Hugging Face.

Run the backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

---

## API Overview

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Company profile

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

### Campaigns and leads

- Campaign and lead routes are exposed under `/api/v1/campaigns` and `/api/v1/leads`
- Lead discovery/search endpoint: `POST /api/v1/leads/search`

---

## Embedding & AI Details

- Uses local semantic embeddings with `paraphrase-mpnet-base-v2`
- Company profile embeddings are generated from profile fields, services, expertise, technologies, industries, and portfolio content
- Lead discovery embeds website content and discovery context for better match quality
- Search ranking prioritizes company profile fit before query relevance
- Optional AI completion uses Gemini or OpenAI if keys are configured

---

## Troubleshooting

- If you see HF Hub warnings or slow model downloads, set `HF_TOKEN` in the environment
- If lead discovery fails with network `403` or SSL errors, your environment may be blocking outbound requests
- Ensure `SERPAPI_KEY` is present for search-based lead discovery
- Verify both backend and frontend are running during development
- Check `backend/app/config.py` for supported environment variables and default values

---

## Project Structure

- `backend/` — backend Python application
- `src/` — React frontend source
- `public/` — static assets
- `package.json` — frontend dependencies and scripts
- `backend/requirements.txt` — Python dependencies
- `README.md` — project documentation

---

## Notes

- The system is tuned to avoid low-value search results and prioritize actual business websites.
- The discovery pipeline now generates provider-focused queries for industry-specific services.
- For lead search, the system uses both company profile embeddings and business signal detection to improve relevance.
- Use the frontend company setup flow to populate services, expertise, and target industries for better matching.
