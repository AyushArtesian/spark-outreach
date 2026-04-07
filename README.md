# Spark Outreach

A full-stack outreach platform combining a React + Vite frontend with a FastAPI backend, local semantic embeddings, and website scraping for company profile enrichment.

## Project Summary

This system collects company context from multiple sources, generates semantic embeddings locally, and supports retrieval-based querying for company profiles, campaigns, and lead outreach.

The core functionality includes:

- Website scraper for company websites
- Semantic embedding generation and ranking
- Company profile creation and update flow
- AI-assisted campaign and lead message generation
- Frontend testing UI for embeddings and profile queries
- JWT authentication and protected backend APIs

---

## Complete System Inventory

### Backend (`backend/app`)

- `main.py`
  - FastAPI application entrypoint
  - CORS middleware and router registration
  - `/`, `/health` endpoints

- `config.py`
  - App settings and environment configuration

- `database.py`
  - MongoDB connection initialization and cleanup

- `routers/`
  - `auth.py` — registration, login, current user endpoint
  - `company.py` — create/update/get company profile, embeddings generation, query, ICP generation, complete setup
  - `campaigns.py` — campaign CRUD and campaign operations
  - `leads.py` — lead CRUD, bulk import, contact actions, status updates
  - `ai.py` — RAG search, message generation, campaign embedding creation

- `services/`
  - `ai_service.py` — local embedding generation and retrieval logic
  - `company_service.py` — company profile enrichment, semantic query logic, website content assembly
  - `campaign_service.py` — campaign data handling
  - `lead_service.py` — lead creation and management
  - `web_scraper.py` — HTML fetching, cleaning, prioritized internal link extraction, page content assembly

- `models/`
  - `user.py` — user accounts, authentication data
  - `company.py` — company profile fields and signals
  - `campaign.py` — campaign metadata and content
  - `lead.py` — lead contact data and status
  - `embedding.py` — stored embeddings and related metadata

- `schemas/`
  - `user.py` — registration, login, current user schemas
  - `company.py` — company profile create/update/query schemas
  - `campaign.py` — campaign request/response schemas
  - `lead.py` — lead request/response schemas

- `utils/`
  - `auth.py` — JWT creation/verification, password hashing
  - `embeddings.py` — embedding utility helpers
  - `response.py` — user serialization and response formatting

### Frontend (`src`)

- `main.tsx`
  - React application bootstrap

- `App.tsx`
  - Main app routes and layout

- `index.css`, `App.css`
  - Global styling and theme utilities

- `components/`
  - `NavLink.tsx`, `ThemeProvider.tsx`
  - `dashboard/` — layout components for dashboard view
  - `landing/` — landing page UI sections
  - `ui/` — shadcn-based UI primitives (button, input, card, dialog, table, etc.)

- `pages/`
  - `Index.tsx` — landing page/home
  - `Login.tsx` — login form
  - `Register.tsx` — registration form
  - `Dashboard.tsx` — user dashboard overview
  - `CompanySetup.tsx` — company onboarding flow
  - `Campaigns.tsx` — campaign list and management
  - `NewCampaign.tsx` — create a campaign
  - `ReviewQueue.tsx` — review messages or campaign results
  - `Prospects.tsx` — prospect list
  - `LeadDashboard.tsx` — lead workspace
  - `LeadDetail.tsx` — individual lead detail page
  - `LeadResults.tsx` — lead matching/results page
  - `LeadSearch.tsx` — search leads
  - `LeadSettings.tsx` — lead-specific settings
  - `Settings.tsx` — user settings, connected accounts, embedding test, notifications, billing
  - `Analytics.tsx` — analytics and reporting
  - `AILearning.tsx` — AI learning / insights screen
  - `NotFound.tsx` — 404 page

- `services/api.ts`
  - Centralized API client for all backend endpoints
  - Auth, campaigns, leads, AI, company API wrappers
  - Automatically attaches JWT token for authenticated requests

- `hooks/`
  - Custom React hooks used by frontend components

- `contexts/`
  - Authentication and global app state context providers

- `lib/`
  - Shared utility helpers used across the frontend

### Key Frontend Features

- User authentication with login/register flows
- Company onboarding and profile setup
- Embedding test UI in Settings
- Campaign creation, listing, and management
- Lead import, search, and detail management
- AI-assisted message generation and search
- Notifications and sending limit controls
- Analytics and dashboards

---

## Core Backend Features

### Authentication

- Register new users
- Login with JWT token
- Protected routes via `Authorization: Bearer <token>`
- Current user profile endpoint

### Company Profile & Enrichment

- Save company website, GitHub, LinkedIn, Upwork, and portfolio URLs
- Generate embeddings from website content and company profile fields
- Query company profile with natural language
- Generate ICP / signals from company data
- Complete profile setup flow

### Website Scraper

- Fetch homepage and prioritized internal pages
- Extract content from About, Services, Solutions, Team, and product pages
- Remove navigational menus, headers, footers, CTA blocks, and repeated boilerplate
- Deduplicate repeated text
- Build a consolidated content payload for embedding

### Semantic Search & AI

- Local embeddings via `sentence-transformers`
- `paraphrase-mpnet-base-v2` model for 768-dimensional vectors
- Query company content and return top-k relevant chunks
- RAG search for campaign content
- AI lead message generation based on campaign and lead data

### Campaign & Lead Management

- CRUD operations for campaigns
- Lead creation, bulk lead upload, and campaign association
- Lead contact actions and status tracking
- Campaign-specific embedding creation

---

## API Endpoints

### Auth

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

### Other (campaigns, leads)

- Campaign and lead routes are available under `/api/v1/campaigns` and `/api/v1/leads`.

---

## Setup Instructions

### Backend

1. Open terminal in `backend/`.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Ensure MongoDB is running.
4. Run backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

1. Open terminal in project root.
2. Install packages:

```powershell
npm install
```

3. Run the frontend:

```powershell
npm run dev
```

4. Open the app in your browser at the Vite URL.

---

## Notes

- The README now documents the full system structure and features.
- If backend endpoints fail, verify the API base URL in `src/services/api.ts`.
- If embedding tests return poor results, refresh website content and regenerate embeddings.
- The web scraper is tuned to reduce noise and prioritize actual business content.

---

## Project Structure at a Glance

- `backend/`
  - `app/`
    - `main.py`, `config.py`, `database.py`
    - `routers/`, `services/`, `models/`, `schemas/`, `utils/`
- `src/`
  - `pages/`, `components/`, `services/`, `hooks/`, `contexts/`, `lib/`
- `package.json`, `tsconfig.json`, `vite.config.ts`
- `requirements.txt` (backend dependencies)

---

This README now reflects every major system component and clearly explains what is present in the project.
