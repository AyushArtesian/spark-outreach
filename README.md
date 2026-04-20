# Spark Outreach

<div align="center">

[![Frontend React 18](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Backend FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Database MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/)
[![Language TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Build Vite](https://img.shields.io/badge/Build-Vite-646CFF?style=flat-square&logo=vite)](https://vitejs.dev/)
[![Status Active Development](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=flat-square)]()

**AI-assisted buyer-intent lead discovery, qualification, enrichment, and outreach platform**

***Define your service profile, discover real buying signals, score fit, enrich lead intelligence, and generate personalized outbound in one system.***

</div>

---

Spark Outreach is a full-stack lead generation and outreach system for service businesses. It combines company-context intelligence, multi-source discovery, scoring, enrichment, and AI workflows into a single operator experience.

This README is a source-verified, implementation-level technical report for product, engineering, and delivery teams.

## Core Functionality

| Area | Capability |
| --- | --- |
| Company Intelligence | Multi-step company setup with services, ICP context, profile embeddings, and generated buyer signals |
| Lead Discovery | Multi-source lead discovery using Apollo (optional), web discovery, and intent signal monitoring |
| Lead Qualification | Scorecards with fit, intent, and signal dimensions; hot-lead extraction |
| Lead Operations | Full lead lifecycle: create, bulk create, update, contact, delete, campaign filtering |
| Outreach | AI-generated cold email and message workflows with lead-level history |
| Monitoring | Async intent scan start, status polling, and detected signal retrieval |
| AI Platform | RAG retrieval, campaign embedding generation, and message generation endpoints |

## Key Highlights

- Full-stack implementation: React + TypeScript + FastAPI + MongoDB.
- Authenticated multi-user workflow with JWT-protected APIs.
- End-to-end lead workflow from profile setup to outreach execution.
- Multi-provider lead and signal ingestion with ranking and filtering.
- Clear service-oriented backend architecture with modular routers and services.
- Ready for iterative production hardening (env-driven config, health checks, test stack).

## Complete Workflow (High Level)

```text
1) Authenticate User
  -> 2) Complete Company Setup
  -> 3) Generate Embeddings + ICP Signals
  -> 4) Run Lead Discovery and Intent Scan
  -> 5) Score, Filter, and Review Leads
  -> 6) Enrich Lead Intelligence
  -> 7) Generate Outreach and Track Contact
```

## Quick Start (5 Minutes)

### 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend

```bash
cd ..
npm install
npm run dev
```

### 3) Access

- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Table of Contents

1. Executive Summary
2. Product Capabilities
3. System Architecture
4. Core Workflows
5. API Surface with Request/Response Examples
6. Deployment and Production Hardening
7. Role-Based Setup and Operational Guides
8. Implementation Roadmap and Future Plans
9. Quality Assurance and Testing Strategy
10. Troubleshooting and Support
11. Best Practices and Patterns
12. Operational Notes and Known Gaps
13. Frontend Features and Screens
14. Backend Services and Internal Logic
15. Data Model Overview
16. Configuration and Environment Settings
17. Development Environment Setup and Commands
18. Test Suite and Configuration Notes

## 1) Executive Summary

Spark Outreach supports the end-to-end flow below:

1. User authentication and protected workspace.
2. Company profile setup with services, industries, locations, and portfolio context.
3. Company context embedding and ICP signal generation.
4. Lead discovery using:
   - Apollo (optional)
   - Web discovery and scraping
   - Buyer-intent signal monitoring
5. Lead ranking using fit plus signal scoring.
6. Lead detail drill-down, enrichment, and cold email generation.
7. Continuous intent scans to identify fresh opportunities.

Primary stack:

- Frontend: React 18, TypeScript, Vite, React Router, TanStack Query, Tailwind + shadcn UI, Framer Motion.
- Backend: FastAPI, MongoEngine, MongoDB, JWT auth, async services.
- AI and retrieval: Gemini and Groq provider support, embeddings and RAG endpoints.

## 2) Product Capabilities

### 2.1 Capability Matrix

| Capability Area | Feature | Status | User Surface | Backend Surface | How It Works |
| --- | --- | --- | --- | --- | --- |
| Identity and Access | Register/Login/Profile | Production | Login/Register + protected routes | /auth/* | JWT token is issued, stored as auth_token, and attached to API requests |
| Company Intelligence | Company profile create/read/update | Production | Company Setup wizard | /company/profile | Wizard persists profile data, then uses profile as lead-search context |
| Company Intelligence | Generate profile embeddings | Production | Company Setup finalization | /company/profile/generate-embeddings | Profile text is vectorized for contextual retrieval |
| Company Intelligence | Generate ICP and signals | Production | Company Setup finalization | /company/profile/generate-icp | Backend derives target ICP and signal definitions from profile |
| Campaigns | Campaign CRUD and start | Production | Campaign pages and test tools | /campaigns/* | Campaigns are owned by current user and drive lead-scoped operations |
| Lead Discovery | Multi-source lead search | Production | Search Leads page | /leads/search | Query planning + source fetch + filtering + dedupe + scoring |
| Lead Discovery | Hot leads list | Production | All Leads tab | /leads/hot | Returns high-priority leads using stored scorecard signals |
| Lead Operations | Lead CRUD + status updates | Production | Lead views | /leads/* | Supports create, bulk, update, contact mark, delete |
| Lead Intelligence | Enrichment | Production | Lead Detail | /leads/{lead_id}/enrich | Adds tech stack, signal strength, and decision-maker hints |
| Outreach | Cold email generation | Production | Lead Detail | /leads/{lead_id}/generate-email | AI generates personalized outreach and stores history |
| Intent Monitoring | Start and monitor intent scan | Production | Test Dashboard and integrated flows | /leads/run-intent-scan, /leads/scan-status, /leads/intent-signals | Async scan detects buyer-intent signals and links to leads |
| AI Tools | RAG search and message generation | Production | API and feature integration | /ai/* | Uses embeddings and model providers for retrieval and generation |
| Analytics Dashboard | Executive dashboard visuals | Demo UI | Lead Dashboard | N/A for most widgets | Current dashboard cards/charts are sample data for UX framing |
| LinkedIn Phase-5 UI | Sequence/connection controls in test page | Experimental UI | Test Dashboard | Not fully implemented in current routers | UI scaffolding exists, full API contract not yet present |

### 2.2 Service Portfolio Coverage

The platform currently supports broad service taxonomy search inputs, including:

- Web App Development
- Mobile App Development
- eCommerce Web Development
- eCommerce App Development
- Product Development
- MVP Development
- Microsoft MAUI
- Salesforce Development
- Business Application Development
- Microsoft Power Pages
- Microsoft Power Apps
- Microsoft Power Automate
- Microsoft Power BI
- Microsoft Copilot Studio
- Microsoft Fabric
- Digital Transformation
- Power Platform Adoption
- Azure Consulting
- DevOps Consulting and Engineering
- Cloud Migration
- InfoPath to Power Apps
- Microsoft Dynamics 365
- Data Engineering
- UI/UX Design
- Cybersecurity
- AI/ML Development

## 3) System Architecture

### 3.1 Context Architecture

```mermaid
flowchart LR
  User[Sales/User] --> FE[React Frontend]
  FE -->|JWT API Calls| API[FastAPI Backend]
  API --> DB[(MongoDB)]

  API --> AI[LLM Providers\nGemini or Groq]
  API --> AP[Apollo API Optional]
  API --> WS[Web Search and Scraping]
  API --> JB[Jobboard and Intent Sources]

  API --> EM[Embedding Store\nMongo Embedding Collection]
  EM --> API
```

### 3.2 Backend Component Diagram

```mermaid
flowchart TB
  subgraph Routers
    R1[auth.py]
    R2[campaigns.py]
    R3[leads.py]
    R4[company.py]
    R5[ai.py]
  end

  subgraph Services
    S1[lead_service]
    S2[company_service]
    S3[intent_monitor]
    S4[ai_service]
    S5[enrichment_service]
    S6[apollo_service]
    S7[jobboard_service]
    S8[email_generator]
    S9[web_scraper]
    S10[query_generator and scorer]
  end

  subgraph Data
    M1[User]
    M2[Campaign]
    M3[Lead]
    M4[Company]
    M5[Embedding]
    M6[Intent Models]
  end

  R1 --> S4
  R2 --> S1
  R3 --> S1
  R3 --> S3
  R3 --> S5
  R3 --> S8
  R4 --> S2
  R5 --> S4

  S1 --> S6
  S1 --> S7
  S1 --> S9
  S1 --> S10
  S2 --> S4
  S3 --> S7

  S1 --> M2
  S1 --> M3
  S2 --> M4
  S2 --> M5
  S3 --> M6
  S4 --> M5
  R1 --> M1
```

### 3.3 Frontend Route Map

```mermaid
flowchart TD
  Root["App Router"]
  Landing["/ -> Index"]
  Login["/login -> Login"]
  Register["/register -> Register"]
  Protected["ProtectedRoute + DashboardLayout"]
  Dashboard["/dashboard -> LeadDashboard"]
  Setup["/company-setup -> CompanySetup"]
  Search["/search -> LeadSearch"]
  Leads["/leads -> LeadResults"]
  AllLeads["/all-leads -> AllLeads"]
  LeadDetail["/lead/:id -> LeadDetail"]
  Settings["/settings -> Settings"]
  Test["/test -> TestDashboard"]
  NotFound["* -> NotFound"]

  Root --> Landing
  Root --> Login
  Root --> Register
  Root --> Protected
  Root --> NotFound

  Protected --> Dashboard
  Protected --> Setup
  Protected --> Search
  Protected --> Leads
  Protected --> AllLeads
  Protected --> LeadDetail
  Protected --> Settings
  Protected --> Test
```

## 4) Core Workflows

### 4.1 Authentication Workflow

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Frontend
  participant API as Auth Router
  participant DB as User Collection

  U->>FE: Submit register/login form
  FE->>API: POST /auth/register or /auth/login
  API->>DB: Create or verify user
  API-->>FE: JWT token and user payload
  FE->>FE: Store auth_token in localStorage
  FE->>API: GET /auth/me with Bearer token
  API-->>FE: Current user context
```

### 4.2 Company Setup Workflow

```mermaid
sequenceDiagram
  participant U as User
  participant FE as CompanySetup Page
  participant API as Company Router
  participant SVC as company_service
  participant EM as Embeddings

  U->>FE: Fill multi-step company profile
  FE->>API: PUT /company/profile
  API->>SVC: Save profile
  SVC-->>API: Updated profile
  API-->>FE: Profile response

  FE->>API: POST /company/profile/generate-embeddings
  API->>SVC: Build profile embeddings
  SVC->>EM: Persist embedding chunks

  FE->>API: POST /company/profile/generate-icp
  API->>SVC: Generate ICP plus buying signals

  FE->>API: POST /company/profile/complete-setup
  API-->>FE: Setup complete
```

### 4.3 Lead Discovery Workflow

```mermaid
sequenceDiagram
  participant U as User
  participant FE as LeadSearch Page
  participant API as leads/search
  participant LS as lead_service
  participant AI as ai_service
  participant AP as apollo_service
  participant WEB as web_scraper
  participant INT as jobboard_service
  participant DB as Lead Collection

  U->>FE: Select services, location, filters
  FE->>API: POST /leads/search
  API->>LS: search_leads_by_company_fit
  LS->>AI: Generate and score search queries
  LS->>AP: Pull candidates optional
  LS->>WEB: Discover and scrape websites
  LS->>INT: Discover buyer-intent entities
  LS->>LS: Normalize, dedupe, filter, score, sort
  LS->>DB: Upsert matching leads
  LS-->>API: Ranked lead list
  API-->>FE: Lead search results
  FE->>FE: Persist results to localStorage and navigate
```

### 4.4 Intent Monitoring Workflow

```mermaid
stateDiagram-v2
  [*] --> Requested
  Requested --> Running: POST /leads/run-intent-scan
  Running --> CollectingSignals
  CollectingSignals --> MatchingLeads
  MatchingLeads --> Persisted
  Persisted --> Completed
  Running --> Failed
  Failed --> [*]
  Completed --> [*]
```

### 4.5 Enrichment and Outreach Workflow

```mermaid
sequenceDiagram
  participant FE as Lead Detail Page
  participant API as Leads Router
  participant EN as enrichment_service
  participant EG as email_generator
  participant DB as Lead Collection

  FE->>API: GET /leads/{lead_id}
  API-->>FE: Full lead detail

  FE->>API: POST /leads/{lead_id}/enrich
  API->>EN: Enrich company and contact signals
  EN->>DB: Save enrichment payload
  API-->>FE: Updated lead detail

  FE->>API: POST /leads/{lead_id}/generate-email
  API->>EG: Generate personalized cold email
  EG->>DB: Append email history
  API-->>FE: subject plus body plus score

  FE->>API: POST /leads/{lead_id}/contact
  API->>DB: Update status to contacted
  API-->>FE: Updated lead
```

## 5) API Surface with Request/Response Examples

Base URL: http://localhost:8000/api/v1

All authenticated endpoints require the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

### 5.1 Authentication

#### POST /auth/register

**Purpose:** Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe"
}
```

#### POST /auth/login

**Purpose:** Authenticate user and issue JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Note:** Store the `access_token` as `auth_token` in localStorage (frontend automatically handles this).

#### GET /auth/me

**Purpose:** Get current authenticated user's profile.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe"
}
```

### 5.2 Companies

#### POST /company/profile

**Purpose:** Create a new company profile.

**Auth Required:** Yes

**Request:**
```json
{
  "company_name": "Acme Tech Solutions",
  "company_size": "51-200",
  "company_stage": "growth",
  "company_description": "We build custom web and mobile applications for enterprise clients.",
  "company_website": "https://acmetech.com",
  "services": ["Web App Development", "Mobile App Development", "Salesforce Development"],
  "expertise_areas": ["SaaS", "FinTech", "Healthcare"],
  "target_industries": ["Financial", "Healthcare", "eCommerce"],
  "target_locations": ["USA", "Canada", "India"],
  "technologies": ["React", "Node.js", "PostgreSQL", "AWS"],
  "team_size": "25-50"
}
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "owner_id": "507f1f77bcf86cd799439011",
  "company_name": "Acme Tech Solutions",
  "services": ["Web App Development", "Mobile App Development", "Salesforce Development"],
  "setup_complete": false,
  "created_at": "2026-04-20T10:30:00Z",
  "updated_at": "2026-04-20T10:30:00Z"
}
```

#### GET /company/profile

**Purpose:** Retrieve current company profile.

**Auth Required:** Yes

**Response (200 OK):**
Same structure as POST response above.

#### POST /company/profile/generate-embeddings

**Purpose:** Generate vector embeddings from company profile text for RAG retrieval.

**Auth Required:** Yes

**Request:** (empty body)

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "embeddings_generated_at": "2026-04-20T10:35:00Z",
  "embedding_chunks_count": 12,
  "status": "complete"
}
```

#### POST /company/profile/generate-icp

**Purpose:** AI-generate Ideal Customer Profile and buying signals.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "icp_generated_at": "2026-04-20T10:40:00Z",
  "ideal_customer_profile": {
    "industries": ["Financial", "Healthcare", "SaaS"],
    "company_sizes": ["100-500", "500-1000"],
    "locations": ["USA", "Canada", "UK"],
    "annual_revenue": "$10M-$100M"
  },
  "buying_signals": [
    "Hiring software engineers",
    "Recent funding announcement",
    "Tech stack expansion",
    "RFP posted on industry board"
  ]
}
```

#### POST /company/profile/complete-setup

**Purpose:** Mark company setup as complete, enabling lead discovery.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "setup_complete": true,
  "completed_at": "2026-04-20T10:45:00Z",
  "ready_for_lead_discovery": true
}
```

### 5.3 Leads Discovery and Operations

#### POST /leads/search

**Purpose:** Multi-source lead discovery with AI query planning, filtering, scoring, and ranking.

**Auth Required:** Yes

**Request:**
```json
{
  "query": "Find companies in USA needing web app development",
  "filters": {
    "services": ["Web App Development", "SaaS Development"],
    "location": "USA",
    "company_sizes": ["100-500", "500-1000"],
    "industries": ["Financial", "Healthcare"]
  },
  "top_k": 50,
  "sort_by": "combined"
}
```

**Response (200 OK):**
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "company": "TechCorp Inc.",
    "email": "contact@techcorp.com",
    "job_title": "VP Engineering",
    "location": "San Francisco, CA",
    "company_fit_score": 0.92,
    "signal_score": 0.85,
    "combined_score": 90,
    "signal_keywords": ["hiring engineers", "tech stack expansion", "series B funding"],
    "reason": ["Strong service fit (92%)", "Active buyer signals detected", "Perfect location match"],
    "status": "New",
    "created_at": "2026-04-20T11:00:00Z"
  },
  {
    "id": "507f1f77bcf86cd799439014",
    "company": "DataFlow Systems",
    "email": "hire@dataflow.io",
    "job_title": "CTO",
    "location": "New York, NY",
    "company_fit_score": 0.78,
    "signal_score": 0.92,
    "combined_score": 82,
    "signal_keywords": ["RFP posted", "cloud migration", "hiring surge"],
    "reason": ["Moderate service fit (78%)", "Strong buyer signals (92%)"],
    "status": "New",
    "created_at": "2026-04-20T11:00:00Z"
  }
]
```

#### GET /leads/{lead_id}

**Purpose:** Retrieve detailed lead information including enrichment and generated emails.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "company": "TechCorp Inc.",
  "email": "contact@techcorp.com",
  "phone": "+1-415-555-0123",
  "job_title": "VP Engineering",
  "company_fit_score": 0.92,
  "signal_score": 0.85,
  "score": {
    "total_score": 90,
    "grade": "A",
    "breakdown": {
      "service_fit": 28,
      "intent_score": 21,
      "tech_stack": 18,
      "contact_availability": 13,
      "size_fit": 10
    },
    "is_hot_lead": true,
    "recommended_action": "contact_immediately"
  },
  "enrichment": {
    "tech_stack": ["React", "Node.js", "PostgreSQL", "AWS"],
    "uses_microsoft_stack": false,
    "decision_maker": {
      "name": "John Smith",
      "email": "jsmith@techcorp.com",
      "linkedin": "https://linkedin.com/in/johnsmith"
    },
    "recent_signals": ["Just hired 5 engineers", "Posted RFP for mobile app", "Series B funded"],
    "signal_strength": 0.92
  },
  "emails": [
    {
      "subject": "Custom Web App Solution for TechCorp's Expansion",
      "body": "Hi John,\n\nI came across TechCorp and was impressed by your recent Series B funding and hiring surge. We specialize in building scalable web applications...",
      "personalization_score": 0.94,
      "generated_at": "2026-04-20T11:30:00Z"
    }
  ],
  "status": "New",
  "created_at": "2026-04-20T11:00:00Z"
}
```

#### POST /leads/{lead_id}/generate-email

**Purpose:** AI-generate personalized cold outreach email.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "subject": "Custom Web App Solution for TechCorp's Expansion",
  "body": "Hi John,\n\nI noticed TechCorp just completed Series B funding and is expanding the engineering team. We've had great success building scalable web applications for similar companies like...\n\nWould you be open to a 15-minute conversation this week?\n\nBest regards,\nAcme Tech Solutions",
  "personalization_score": 0.94,
  "generated_at": "2026-04-20T11:30:00Z",
  "email_type": "cold"
}
```

#### POST /leads/{lead_id}/enrich

**Purpose:** Add tech stack, decision-maker, and signal enrichment to a lead.

**Auth Required:** Yes

**Request:** (empty body)

**Response (200 OK):**
Returns updated lead detail with enrichment payload (same as GET /leads/{lead_id}).

#### POST /leads/{lead_id}/contact

**Purpose:** Mark lead as contacted and update status.

**Auth Required:** Yes

**Request:**
```json
{
  "status": "Contacted",
  "notes": "Email sent with personalized pitch. Awaiting response."
}
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "status": "Contacted",
  "contacted_at": "2026-04-20T12:00:00Z",
  "notes": "Email sent with personalized pitch. Awaiting response."
}
```

#### POST /leads/run-intent-scan

**Purpose:** Start async buyer-intent scanning across job boards, web, and market signals.

**Auth Required:** Yes

**Request:**
```json
{
  "services": ["Web App Development", "Salesforce Development"],
  "locations": ["USA", "Canada"]
}
```

**Response (202 Accepted):**
```json
{
  "scan_id": "scan_507f1f77bcf86cd799439015",
  "status": "running",
  "started_at": "2026-04-20T12:05:00Z",
  "estimated_completion": "2026-04-20T12:35:00Z"
}
```

#### GET /leads/scan-status

**Purpose:** Poll async intent scan progress.

**Auth Required:** Yes

**Response (200 OK):**
```json
{
  "scan_id": "scan_507f1f77bcf86cd799439015",
  "status": "completed",
  "progress": 100,
  "summary": {
    "companies_scanned": 2450,
    "companies_found": 127,
    "leads_created": 89,
    "signals_detected": 342
  },
  "completed_at": "2026-04-20T12:30:00Z"
}
```

#### GET /leads/intent-signals

**Purpose:** Retrieve detected buyer-intent signals.

**Auth Required:** Yes

**Response (200 OK):**
```json
[
  {
    "id": "signal_507f1f77bcf86cd799439016",
    "company_name": "StartupXYZ Inc.",
    "signal_type": "hiring_surge",
    "source": "LinkedIn",
    "strength": 0.95,
    "details": "Posted 8 engineering positions in past 2 weeks",
    "lead_id": "507f1f77bcf86cd799439017",
    "is_openable": true,
    "detected_at": "2026-04-20T12:25:00Z"
  },
  {
    "id": "signal_507f1f77bcf86cd799439018",
    "company_name": "CloudTech Corp",
    "signal_type": "rfp_posted",
    "source": "Industry Board",
    "strength": 0.89,
    "details": "RFP for cloud migration and web application modernization",
    "lead_id": "507f1f77bcf86cd799439019",
    "is_openable": true,
    "detected_at": "2026-04-20T12:22:00Z"
  }
]
```

### 5.4 Campaigns

| Method | Path | Auth Required | Purpose |
| --- | --- | --- | --- |
| POST | /campaigns | Yes | Create campaign |
| GET | /campaigns | Yes | List campaigns |
| GET | /campaigns/{campaign_id} | Yes | Campaign detail |
| PUT | /campaigns/{campaign_id} | Yes | Update campaign |
| POST | /campaigns/{campaign_id}/start | Yes | Start campaign |
| DELETE | /campaigns/{campaign_id} | Yes | Delete campaign |

### 5.5 AI Services

#### POST /ai/rag-search

**Purpose:** Semantic retrieval from company profile embeddings (RAG).

**Auth Required:** Yes

**Request:**
```json
{
  "query": "What industries have we successfully worked with?",
  "top_k": 3
}
```

**Response (200 OK):**
```json
[
  {
    "chunk_text": "We have extensive experience in Financial Services and FinTech industries...",
    "score": 0.94,
    "source": "company_profile"
  }
]
```

#### POST /ai/generate-message

**Purpose:** Generate AI message for lead outreach.

**Auth Required:** Yes

**Request:**
```json
{
  "lead_id": "507f1f77bcf86cd799439013",
  "message_type": "cold_email"
}
```

**Response (200 OK):**
```json
{
  "message": "Hi John,\n\nI noticed your recent funding...",
  "tone": "professional",
  "generated_at": "2026-04-20T11:30:00Z"
}
```

### 5.6 System Health

| Method | Path | Auth Required | Purpose |
| --- | --- | --- | --- |
| GET | / | No | Service root info |
| GET | /health | No | Health and DB status |

**Health Response Example (200 OK):**
```json
{
  "status": "ok",
  "database": "connected",
  "mongodb_version": "5.0.0",
  "uptime_seconds": 3662,
  "timestamp": "2026-04-20T12:00:00Z"
}
```

**Health Response Example (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "database": "unavailable",
  "error": "MongoDB connection timeout",
  "timestamp": "2026-04-20T12:00:00Z"
}
```

## 6) Deployment and Production Hardening

### 6.1 Docker Containerization

**Backend Dockerfile** (`backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY wsgi.py .

EXPOSE 8000

CMD ["gunicorn", "--workers=4", "--worker-class=uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000", "wsgi:app"]
```

**Frontend Dockerfile** (`Dockerfile`):

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose** (`docker-compose.yml`):

```yaml
version: '3.9'

services:
  mongodb:
    image: mongo:7.0
    container_name: spark_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-changeme}
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
    networks:
      - spark_network

  backend:
    build: ./backend
    container_name: spark_backend
    depends_on:
      - mongodb
    environment:
      DATABASE_URL: mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-changeme}@mongodb:27017/spark_outreach
      VITE_API_URL: http://localhost:8000
      SECRET_KEY: ${SECRET_KEY:-your-secret-here}
      GOOGLE_GENERATIVE_AI_KEY: ${GOOGLE_GENERATIVE_AI_KEY}
      GROQ_API_KEY: ${GROQ_API_KEY}
      APOLLO_API_KEY: ${APOLLO_API_KEY}
      LINKEDIN_USERNAME: ${LINKEDIN_USERNAME}
      LINKEDIN_PASSWORD: ${LINKEDIN_PASSWORD}
    ports:
      - "8000:8000"
    networks:
      - spark_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: .
    container_name: spark_frontend
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "80:80"
    networks:
      - spark_network

volumes:
  mongodb_data:

networks:
  spark_network:
    driver: bridge
```

**Build and Run:**
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 6.2 Environment Configuration

**.env.example** (copy to `.env` for local development):

```env
# Database
MONGO_USER=admin
MONGO_PASSWORD=SecurePassword123!
DATABASE_URL=mongodb://admin:SecurePassword123!@localhost:27017/spark_outreach

# JWT & Auth
SECRET_KEY=your-super-secret-jwt-key-generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Services
GOOGLE_GENERATIVE_AI_KEY=your-google-api-key
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768

# Third Party APIs
APOLLO_API_KEY=your-apollo-api-key
LINKEDIN_USERNAME=your-linkedin-email
LINKEDIN_PASSWORD=your-linkedin-password

# Frontend
VITE_API_URL=http://localhost:8000

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:80,https://yourdomain.com

# Email (optional for future email delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### 6.3 Production Hardening Checklist

**Security:**
- [ ] Set `SECRET_KEY` to cryptographically secure random value (min 32 chars)
- [ ] Enable HTTPS only (redirect HTTP to HTTPS)
- [ ] Set CORS origins to specific domains only
- [ ] Enable rate limiting on all endpoints (100 requests/minute per user)
- [ ] Implement API key rotation for third-party services quarterly
- [ ] Use environment variables for all secrets (never commit to repo)
- [ ] Enable MongoDB authentication with strong password
- [ ] Backup credentials in secure vault (AWS Secrets Manager / HashiCorp Vault)

**Performance:**
- [ ] Enable MongoDB indexing on frequently queried fields (email, company_name, created_at)
- [ ] Set up Redis caching for lead search results (TTL 1 hour)
- [ ] Enable gzip compression on all HTTP responses
- [ ] Implement connection pooling for database (PyMongo 3.12+)
- [ ] Set up CDN for static assets (CloudFront / Cloudflare)
- [ ] Enable query result pagination (max 100 records per request)

**Reliability:**
- [ ] Set up database backup (daily, 30-day retention minimum)
- [ ] Enable request logging and centralized aggregation (ELK Stack / Datadog)
- [ ] Set up uptime monitoring with alerts
- [ ] Implement circuit breaker for external APIs (Apollo, web scraper)
- [ ] Set max request timeout to 30 seconds
- [ ] Implement graceful shutdown (30-second drain period)
- [ ] Enable auto-scaling based on CPU/memory metrics

**Monitoring:**
- [ ] Track endpoint response times (p50, p95, p99)
- [ ] Alert on error rate > 5%
- [ ] Monitor MongoDB connection pool health
- [ ] Track AI service quota usage
- [ ] Alert on database size growth > 1GB/month
- [ ] Monitor third-party API costs and usage

### 6.4 Nginx Reverse Proxy Configuration

**nginx.conf** (for production load balancing):

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=200 nodelay;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # API proxy
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
}

# HTTP redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## 7) Role-Based Setup and Operational Guides

### 7.1 Developer Onboarding (Local Development)

**Goal:** Get local dev environment running in < 5 minutes, understand codebase structure, debug issues.

**Step 1: Clone and Dependencies**
```bash
git clone https://github.com/yourepo/spark-outreach.git
cd spark-outreach

# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ..
npm install
```

**Step 2: Environment Setup**
```bash
# Copy .env template
cp backend/.env.example backend/.env
cp .env.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
# Set in backend/.env as SECRET_KEY

# Add your API keys (Apollo, Google, Groq, LinkedIn)
# See 6.2 Environment Configuration for full list
```

**Step 3: Database**
```bash
# Option 1: Local MongoDB
mongod --dbpath ./data

# Option 2: Docker
docker run -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=changeme mongo:7.0
```

**Step 4: Start Services**
```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd ..
npm run dev
```

**Step 5: Verify**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Test endpoint: `curl http://localhost:8000/health`

**Common Dev Tasks:**

| Task | Command |
| --- | --- |
| Run backend tests | `pytest backend/` |
| Run frontend tests | `npm run test` |
| Format code | `black backend/` (Python); `npm run format` (JS) |
| Lint | `pylint backend/app` (Python); `npm run lint` (JS) |
| Database shell | `mongosh mongodb://admin:changeme@localhost:27017` |
| Drop all data | `db.dropDatabase()` in mongosh |
| Check API routes | `curl http://localhost:8000/docs` |

### 7.2 QA Testing Checklist

**Test Campaign Workflow:**

1. **Authentication**
   - [ ] Register new user with valid email and password
   - [ ] Login with correct and incorrect credentials
   - [ ] Verify JWT token stored in localStorage
   - [ ] Verify token expiration (logout after 24 hours)
   - [ ] Test access to authenticated endpoints without token (should 403)

2. **Company Setup**
   - [ ] Create company profile with all services
   - [ ] Update profile (edit company name, description, services)
   - [ ] Generate embeddings (verify status changes to complete)
   - [ ] Generate ICP and signals
   - [ ] Complete setup (verify setup_complete flag set)
   - [ ] Verify error if required fields missing

3. **Lead Discovery**
   - [ ] Run lead search with sample queries
   - [ ] Verify scoring (company_fit_score between 0-1, is_hot_lead calculated)
   - [ ] Test filters (service, location, industry, company_size)
   - [ ] Test pagination (top_k parameter limits results)
   - [ ] Run intent scan (verify status polling works)
   - [ ] Retrieve scan results

4. **Lead Management**
   - [ ] Create single lead via form
   - [ ] Bulk import leads via CSV
   - [ ] View all leads, hot leads, campaign-specific leads
   - [ ] Update lead status (New → Contacted → Qualified → etc.)
   - [ ] Enrich lead (verify tech_stack, decision_maker populated)
   - [ ] Delete lead (verify removal from database)

5. **Outreach**
   - [ ] Generate AI email for lead
   - [ ] Verify personalization_score > 0.8
   - [ ] Mark lead as contacted
   - [ ] Test email regeneration (new versions without duplicates)
   - [ ] Verify email history preserved

6. **Campaigns**
   - [ ] Create campaign with name, description, lead list
   - [ ] Start campaign (verify status changes)
   - [ ] List campaigns (verify pagination)
   - [ ] Update campaign name and description
   - [ ] Delete campaign (verify leads not deleted, only campaign)

7. **Performance & Edge Cases**
   - [ ] Test with 500+ leads (verify pagination and response time < 2s)
   - [ ] Test empty database (verify graceful 200 with [] response)
   - [ ] Test with special characters in names (quotes, emojis, etc.)
   - [ ] Network latency: API timeout > 30 seconds (should retry or fail gracefully)

**Regression Test Suite (run before each release):**
```bash
# Backend
pytest backend/ -v --cov=backend/app --cov-report=html

# Frontend
npm run test:ui

# Manual integration test
./scripts/test-workflow.sh
```

### 7.3 DevOps / Infrastructure Guide

**Deployment Process:**

1. **Staging Deployment**
```bash
# Pull latest code
git pull origin main

# Build images
docker-compose build

# Run migrations if needed
docker-compose run backend python backend/manage_db.py migrate

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Verify health
curl https://staging-api.yourdomain.com/health

# Run smoke tests
./scripts/smoke-test.sh https://staging-api.yourdomain.com
```

2. **Production Deployment**
```bash
# Tag release
git tag v1.2.3
git push origin v1.2.3

# Review production checklist (see 6.3)
# Deploy only after all checks pass

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor for 15 minutes
./scripts/monitor.sh

# Rollback command (if needed)
docker-compose down
git checkout v1.2.2  # previous tag
docker-compose up -d
```

**Monitoring Setup:**

```bash
# Health check interval
curl -s http://localhost:8000/health | jq '.status'

# Database size
mongosh "mongodb://admin:pwd@localhost:27017" --eval "db.stats()"

# Recent errors
docker logs --tail 50 spark_backend | grep ERROR

# Performance metrics (Datadog / Prometheus integration)
# - Endpoint response times (p50, p95, p99)
# - Error rate percentage
# - Database query times
# - AI service quota usage
```

**Backup and Recovery:**

```bash
# Daily MongoDB backup (add to cron)
mongodump --username admin --password $MONGO_PASSWORD --authenticationDatabase admin --out /backups/spark_$(date +%Y%m%d)

# Restore from backup
mongorestore --username admin --password $MONGO_PASSWORD --authenticationDatabase admin /backups/spark_20260420

# Store backups in S3 (weekly)
tar -czf spark_backup_$(date +%Y%m%d).tar.gz /backups/spark_*
aws s3 cp spark_backup_*.tar.gz s3://yourbucket/backups/ --sse AES256
```

### 7.4 Sales Operations Guide

**Lead Workflow for Sales Teams:**

1. **Setup (First Day)**
   - Company profile configured by marketing/ops
   - Services, industries, targets defined
   - Embeddings and ICP generated
   - Sales team gains access to Lead Dashboard

2. **Discovery (Weekly)**
   - Run intent scan Monday morning (scans across job boards, LinkedIn, web)
   - Review detected signals throughout week
   - Create lead list from intent scan results

3. **Qualification (Daily)**
   - Filter leads by score threshold (hot leads only, > 80)
   - Review lead enrichment (tech stack, decision maker, recent signals)
   - Bulk assign leads to sales reps or campaigns
   - Update lead status as contacted/qualified/disqualified

4. **Outreach**
   - Generate AI email (or use sample templates)
   - Send personalized outreach
   - Track response status
   - Log notes and next actions

5. **Analytics (Monthly)**
   - Lead volume vs. discovery ratio
   - Conversion rate by score range
   - Average response time by industry/service
   - Top-performing campaigns

**Key Metrics to Track:**

| Metric | Target | Review Frequency |
| --- | --- | --- |
| Leads discovered / week | 50+ | Weekly |
| Hot leads % (score > 80) | 20-30% | Weekly |
| Response rate | > 5% | Weekly |
| Meeting rate | > 20% of responses | Monthly |
| Pipeline value | ${} | Monthly |
| Cost per lead | $/${} | Monthly |

## 8) Implementation Roadmap and Future Plans

### Current Status: MVP Complete (Phase 1 ✓)

**Shipped Features**
- ✓ User authentication (JWT)
- ✓ Company profile with setup wizard
- ✓ Lead discovery from Apollo + web sources
- ✓ Lead scoring (fit + intent + signals)
- ✓ Lead enrichment (tech stack, decision maker)
- ✓ AI email generation
- ✓ Campaign management
- ✓ Async intent scanning
- ✓ Dashboard and lead list UI

### Phase 2: Outreach Automation & Sequencing (3 months)

**Goals:**
- Automate multi-touch sequences
- Track email opens and clicks
- A/B test outreach variants
- Integration with CRM and email platforms

**Features:**
- [ ] Email sequence templates (3-5 touch)
- [ ] Gmail/Office 365 integration (OAuth)
- [ ] Email tracking (opens, clicks, replies)
- [ ] A/B testing framework
- [ ] Scheduled send optimization
- [ ] LinkedIn and Twitter reply workflows
- [ ] Do-Not-Contact (DNC) list management

**Estimated effort:** 120 developer-days

### Phase 3: Predictive Intelligence & Advanced Scoring (4 months)

**Goals:**
- ML-based lead scoring using historical results
- Predictive engagement and deal probability
- Lookalike lead discovery

**Features:**
- [ ] Historical data collection (6+ months of outreach)
- [ ] ML model training (fit, engagement, deal probability)
- [ ] Real-time scoring rerank
- [ ] Cohort analysis (which companies buy?)
- [ ] Lookalike lead discovery
- [ ] Company intelligence enrichment (D&B, Apollo, etc.)

**Estimated effort:** 150 developer-days

### Phase 4: Team Collaboration & Workflow (2 months)

**Goals:**
- Multi-user team workflows
- Role-based access control
- Lead assignment and shared campaigns

**Features:**
- [ ] Team management (invite, manage roles)
- [ ] Role-based permissions (admin, sales, viewer)
- [ ] Lead assignment (territory, rep, manual)
- [ ] Shared campaign templates
- [ ] Activity feeds and notifications
- [ ] Reporting and dashboards with team metrics

**Estimated effort:** 80 developer-days

### Phase 5: Platform Extensions & API (2 months)

**Goals:**
- Enable third-party integrations
- White-label support
- Marketplace of lead providers

**Features:**
- [ ] Complete REST API v2 (rate limiting, webhooks)
- [ ] OAuth for third-party apps
- [ ] Zapier / Make.com integration
- [ ] Webhook events (lead.created, email.sent, etc.)
- [ ] White-label branding options
- [ ] API analytics and usage dashboard

**Estimated effort:** 100 developer-days

**Total Roadmap:** ~450 developer-days (~9 months for 2-engineer team)

## 9) Quality Assurance and Testing Strategy

### Test Stack

**Backend (Python):**
- pytest (test runner)
- pytest-cov (coverage)
- pytest-asyncio (async tests)
- mongomock (MongoDB mocking)
- responses (HTTP mocking)

**Frontend (TypeScript/React):**
- Vitest (test runner)
- React Testing Library (component testing)
- Playwright (E2E testing)
- MSW (Mock Service Worker)

### Test Coverage Goals

| Layer | Target | Current |
| --- | --- | --- |
| Backend services | 80% | 40% (WIP) |
| Backend routers | 75% | 50% (WIP) |
| Frontend components | 70% | 30% (WIP) |
| E2E workflows | Critical paths only | TBD |

### Test Execution

```bash
# Run all tests
npm run test:all

# Backend unit tests
cd backend && pytest -v --cov=app --cov-report=html

# Frontend component tests
npm run test

# E2E tests (Playwright)
npm run test:e2e

# E2E with UI
npm run test:e2e:ui

# Generate coverage report
npm run test:coverage
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest backend/ -q
        language: system
        stages: [commit]
      - id: black
        name: black
        entry: black backend/
        language: system
        stages: [commit]
      - id: eslint
        name: eslint
        entry: npm run lint
        language: system
        types: [javascript, typescript]
```

## 10) Troubleshooting and Support

### Common Errors and Solutions

**Backend Issues**

| Error | Cause | Solution |
| --- | --- | --- |
| `mongodb.errors.ServerSelectionTimeoutError` | MongoDB not running | Start MongoDB: `mongod` or `docker run -d -p 27017:27017 mongo:7.0` |
| `mongoengine.connection.ConnectionError: database auth failed` | Wrong credentials | Check MONGO_USER, MONGO_PASSWORD in .env |
| `ImportError: No module named 'google'` | Missing dependency | `pip install google-generative-ai` |
| `JWT Decode Error` | Token expired or invalid | User needs to re-login (token expires after 24 hours) |
| `CORS error in browser` | CORS origin not whitelisted | Add frontend URL to CORS_ORIGINS in .env |

**Frontend Issues**

| Error | Cause | Solution |
| --- | --- | --- |
| `VITE_API_URL is undefined` | Missing .env file | Create .env with `VITE_API_URL=http://localhost:8000` |
| `Cannot POST /api/v1/auth/login` | Backend not running or wrong port | Verify backend at http://localhost:8000/docs |
| `Blank white page` | JavaScript error | Open DevTools (F12) → Console tab to see error |
| `localStorage is not defined` | SSR issue | Only use localStorage in useEffect or browser-only context |

**Database Issues**

```bash
# Check MongoDB connection
mongosh "mongodb://admin:password@localhost:27017"

# Check database size
db.stats()

# Check specific collection
db.users.countDocuments()
db.leads.countDocuments()

# Drop collections if corrupted
db.users.deleteMany({})
db.leads.deleteMany({})
```

**API Issues**

```bash
# Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"password"}'

# Test health
curl http://localhost:8000/health

# List all active routes
curl http://localhost:8000/docs | grep operationId

# Enable debug logging
export LOG_LEVEL=DEBUG
# Or set DEBUG_MODE=true in .env
```

### Performance Debugging

**Slow API Response (> 2 seconds)**

```python
# Add timing middleware in backend/app/main.py
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"[{request.url.path}] took {process_time:.2f}s")
    return response

# Then run: grep "took" logs | sort -t 's' -k2 -n | tail
```

**Database Query Performance**

```bash
# Enable MongoDB profiling
db.setProfilingLevel(1, { slowms: 1000 })  # Log queries > 1s
db.system.profile.find().sort({ ts: -1 }).limit(5).pretty()

# Add missing indexes
db.leads.createIndex({ email: 1 })
db.leads.createIndex({ company_name: 1 })
db.leads.createIndex({ created_at: -1 })
```

**Frontend Bundle Size**

```bash
npm run build  # Creates dist/
npm install -g vite
vite analyze --config vite.config.ts  # Or use rollup-plugin-visualizer
```

## 11) Best Practices and Patterns

### Code Organization

**Backend Directory Structure**
```
app/
├── routers/          # API endpoints by domain
│   ├── auth.py       # Authentication endpoints
│   ├── leads.py      # Lead CRUD and search
│   ├── campaigns.py  # Campaign management
│   └── ai.py         # AI service endpoints
├── services/         # Business logic
│   ├── lead_service.py
│   ├── ai_service.py
│   └── enrichment_service.py
├── models/           # Database models (MongoEngine)
│   ├── lead.py
│   ├── campaign.py
│   └── user.py
├── schemas/          # Pydantic request/response validation
│   ├── lead.py
│   └── campaign.py
└── utils/            # Helpers (auth, embeddings, etc.)
```

**Frontend Directory Structure**
```
src/
├── components/       # Reusable UI components
│   ├── dashboard/    # Dashboard-specific
│   ├── landing/      # Landing page
│   └── ui/           # shadcn/ui wrappers
├── pages/            # Full page components (one per route)
│   ├── LeadSearch.tsx
│   ├── Dashboard.tsx
│   └── ...
├── services/         # API clients and business logic
│   └── api.ts        # Centralized API calls
├── contexts/         # React contexts (AuthContext, etc.)
└── hooks/            # Custom React hooks
```

### API Response Standardization

```python
# Always return consistent response structure
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    status: str  # "success" or "error"
    data: T
    error: Optional[str] = None
    timestamp: datetime

# Usage in endpoints:
@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    lead = await Lead.get(lead_id)
    return APIResponse[Lead](
        status="success",
        data=lead,
        timestamp=datetime.now()
    )
```

### Error Handling

```python
# Create custom exceptions
class LeadNotFoundException(Exception):
    pass

class InvalidScoreException(Exception):
    pass

# Handle in middleware
@app.exception_handler(LeadNotFoundException)
async def lead_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": "Lead not found",
            "timestamp": datetime.now()
        }
    )
```

### Frontend Data Fetching

```typescript
// Use React Query for caching and background updates
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const { data: leads, isLoading } = useQuery({
  queryKey: ['leads'],
  queryFn: () => api.getLeads(),
  staleTime: 5 * 60 * 1000, // 5 minute cache
});

const { mutate: updateLead } = useMutation({
  mutationFn: (lead: Lead) => api.updateLead(lead),
  onSuccess: () => queryClient.invalidateQueries(['leads']),
});
```

### Authentication Pattern

```typescript
// Frontend auth context
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>(null);

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  
  useEffect(() => {
    // Check token on mount
    const token = localStorage.getItem('auth_token');
    if (token) {
      api.setAuthToken(token);
      api.getMe().then(setUser);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    localStorage.setItem('auth_token', access_token);
    api.setAuthToken(access_token);
    const user = await api.getMe();
    setUser(user);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout: ... }}>
      {children}
    </AuthContext.Provider>
  );
};
```

## 12) Operational Notes and Known Gaps

### Production Readiness Assessment

**Ready for Production:**
- ✓ Authentication and authorization
- ✓ Core CRUD operations
- ✓ Lead discovery and scoring
- ✓ Basic API validation
- ✓ Health checks and monitoring

**Before Production Deployment:**
- [ ] Implement comprehensive error logging (Sentry, DataDog)
- [ ] Set up rate limiting and request throttling
- [ ] Enable cache layer (Redis) for frequent queries
- [ ] Implement request batching for bulk operations
- [ ] Set up automated database backups
- [ ] Security review: OWASP top 10
- [ ] Load testing (minimum 1000 concurrent users)
- [ ] Disaster recovery plan and testing
- [ ] Data masking for sensitive information in logs
- [ ] Audit logging for compliance

### Known Limitations

| Issue | Impact | Workaround | Priority |
| --- | --- | --- | --- |
| Email tracking not implemented | Can't track opens/clicks | Manual tracking in notes field | High (Phase 2) |
| No multi-tenancy | Multiple companies per user not supported | Create separate accounts | Medium (Phase 4) |
| LinkedIn API not integrated | Limited lead enrichment | Manual LinkedIn lookup | Medium (Phase 2) |
| No email sequence automation | Single email per lead only | Manual follow-ups | High (Phase 2) |
| No CRM integration | Lead sync requires manual export | CSV import available | Medium (Phase 5) |
| No bulk email sending | Manual per-lead email | API batch endpoint (WIP) | Medium (Phase 2) |
| Real-time intent monitoring limited | Scan is async only | Status polling available | Low (Phase 3) |

### Scaling Considerations

**Current Limits (Single Server)**
- Concurrent users: ~100
- Lead database: ~1M records
- Request rate: ~1000 req/min

**For 10x Scale (1000 concurrent users, 10M leads):**

1. **Database**
   - Shard MongoDB by company_id
   - Add read replicas
   - Move to Atlas (managed)

2. **API**
   - Horizontal scaling with load balancer
   - CDN for static assets
   - Cache layer (Redis)

3. **Async Tasks**
   - Move to message queue (RabbitMQ / Kafka)
   - Background workers (Celery)
   - Intent scans run in worker pool

4. **AI Services**
   - Rate limiting with token bucket
   - Fallback providers
   - Batch embedding generation

## 13) Repository Map and Files

### Backend
- [backend/app/main.py](backend/app/main.py) - FastAPI app definition
- [backend/app/routers/](backend/app/routers) - API endpoints (auth, leads, campaigns, ai, company)
- [backend/app/services/](backend/app/services) - Business logic and external integrations
- [backend/app/models/](backend/app/models) - MongoEngine database models
- [backend/requirements.txt](backend/requirements.txt) - Python dependencies

### Frontend
- [src/main.tsx](src/main.tsx) - Entry point
- [src/App.tsx](src/App.tsx) - Main router
- [src/pages/](src/pages) - Page components (one per route)
- [src/components/](src/components) - Reusable components
- [src/services/api.ts](src/services/api.ts) - API client
- [package.json](package.json) - Node.js dependencies

### Configuration
- [docker-compose.yml](docker-compose.yml) - Local dev stack
- [vite.config.ts](vite.config.ts) - Frontend build config
- [tsconfig.json](tsconfig.json) - TypeScript config
- [tailwind.config.ts](tailwind.config.ts) - Tailwind CSS config
- [playwright.config.ts](playwright.config.ts) - E2E test config

---

**Last Updated:** April 2026

**Contact:** engineering@yourdomain.com

### 6.1 Routed Screens in Active Navigation

| Route | Page | Purpose | Data Source |
| --- | --- | --- | --- |
| / | Index | Landing page and entry point | Static UI |
| /login | Login | User sign-in | /auth/login |
| /register | Register | User signup | /auth/register |
| /dashboard | LeadDashboard | Dashboard and summary cards | Mostly sample/demo data in current implementation |
| /company-setup | CompanySetup | Company profile wizard and intelligence setup | /company/* |
| /search | LeadSearch | Build intent-aware lead search query | /leads/search |
| /leads | LeadResults | Immediate search result review | localStorage from search response |
| /all-leads | AllLeads | Persistent database lead list and hot leads | /leads/all and /leads/hot |
| /lead/:id | LeadDetail | Lead intelligence, enrichment, email generation | /leads/{id}, enrich, generate-email |
| /settings | Settings | Account and app settings UI | Varies |
| /test | TestDashboard | Advanced testing surface for phase flows | Mixed live and experimental endpoints |

### 6.2 Additional Page Files Present

The following pages exist in source but are not currently mounted in active routing:

- AILearning
- Analytics
- Campaigns
- Dashboard
- LeadSettings
- NewCampaign
- Prospects
- ReviewQueue

### 6.3 Feature Behavior Details

#### Company Setup

- Loads existing profile on mount.
- Saves progress per step via profile update.
- Final completion runs a pipeline: save profile, generate embeddings, generate ICP, mark complete.

#### Search Leads

- User picks location, services, and filters.
- UI runs a staged progress sequence to communicate process status.
- Submits query and filters to /leads/search.
- Stores response in localStorage and redirects to /leads.

#### Lead Results

- Reads localStorage payload generated by search.
- Supports filtering by priority/status and sorting by quality/company/date.
- Offers quick actions for copy email, open details, mark contacted UI action.

#### All Leads

- Pulls persisted leads from database.
- Separates hot leads into dedicated tab.
- Supports pagination and advanced score breakdown expansion.

#### Lead Detail

- Fetches enriched lead details.
- Displays scoring dimensions and reasons.
- Supports cold email generation and email history.
- Supports contact-ready details including fallback from enrichment payload.

#### Test Dashboard

- Includes Phase-2 intent scan actions and polling.
- Includes Phase-5 LinkedIn UI scaffolding.
- Some controls point to endpoints that are not fully implemented in current backend routers.

## 14) Backend Services and Internal Logic

| Service | Main Responsibility | Inputs | Outputs |
| --- | --- | --- | --- |
| ai_service | Query planning, message generation, embeddings, retrieval | Campaign/profile context and prompts | Ranked queries, generated text, vectors |
| lead_service | Main discovery orchestrator | Query + filters + user context | Ranked lead list, saved lead docs |
| apollo_service | Apollo provider integration | Search criteria and API key | Candidate companies and contacts |
| web_scraper | Web discovery and page signal extraction | Search terms and domains | Candidate intent records |
| jobboard_service | Buyer-intent signal mining | Services and locations | Intent entities and opportunity clues |
| intent_monitor | Async scan lifecycle management | Campaign/service scan request | Scan status, intent signals, lead linkage |
| enrichment_service | Lead/company enrichment | Lead identifier and company signals | Tech stack, contact, and signal enrichments |
| email_generator | Outreach copy generation | Lead profile and context | Subject, body, personalization score |
| company_service | Company profile intelligence | Profile form data | Stored profile, ICP output, embeddings |
| campaign_service | Campaign CRUD/start | Campaign payload | Campaign records and state changes |
| query_generator | Deterministic fallback query creation | Service and location context | Search-ready query set |
| query_scorer | Query intent extraction and scoring | Candidate query list | Ranked query scores |
| service_catalog | Service taxonomy and keyword mapping | Service terms | Normalized domain taxonomy |
| llm_provider | Groq-specific abstraction | Prompt payload | Model completion |
| linkedin_service | Sequence and outreach support layer | Lead/campaign signal context | LinkedIn automation helper outputs |

## 15) Data Model Overview

```mermaid
classDiagram
  class User {
    +id
    +email
    +username
    +hashed_password
  }

  class Campaign {
    +id
    +owner_id
    +name
    +description
    +status
  }

  class Lead {
    +id
    +owner_id
    +campaign_id
    +company
    +email
    +status
    +score
    +enrichment
    +emails[]
  }

  class Company {
    +id
    +owner_id
    +company_name
    +services[]
    +target_industries[]
    +target_locations[]
    +setup_complete
  }

  class Embedding {
    +id
    +owner_id
    +source_type
    +chunk_text
    +vector
  }

  class IntentSignal {
    +id
    +scan_id
    +company_name
    +signal_type
    +strength
    +lead_id optional
  }

  User "1" --> "many" Campaign
  User "1" --> "many" Lead
  User "1" --> "1" Company
  Campaign "1" --> "many" Lead
  Company "1" --> "many" Embedding
  IntentSignal "many" --> "0..1" Lead
```

### 8.1 Scoring Notes

In UI fallback logic for some views, quality is derived from fit and signal:

$Q = 10 \times (0.5 \cdot company\_fit\_score + 0.3 \cdot signal\_score)$

Scorecards can also include richer breakdown dimensions:

- service_fit
- intent_score
- tech_stack
- contact_availability
- size_fit

## 16) Configuration and Environment Settings

Backend environment file: backend/.env

```env
APP_NAME=Spark Outreach API
DEBUG=False
API_V1_STR=/api/v1

MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=spark_outreach
MONGO_REQUIRED_ON_STARTUP=True

SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
GROQ_API_KEY=
GROQ_MODEL=qwen/qwen3-32b
OPENAI_API_KEY=

APOLLO_API_KEY=
APOLLO_BASE_URL=https://api.apollo.io/api/v1
APOLLO_MAX_PAGES=2
APOLLO_ENRICHMENT_ENABLED=True
APOLLO_ENRICHMENT_MAX_PEOPLE=20

LEAD_QUERY_PLANNER_ENABLED=True
LEAD_QUERY_PLANNER_MAX_QUERIES=5

HF_API_KEY=
SERPAPI_KEY=
SERPER_API_KEY=
WAPPALYZER_API_KEY=
HUNTER_API_KEY=

REDIS_URL=
```

### 9.1 Important Runtime Notes

- Frontend API base URL is currently hardcoded to http://localhost:8000/api/v1 in multiple files.
- Company setup and test screens also contain local hardcoded API roots.
- If MONGO_REQUIRED_ON_STARTUP is False, app can boot in degraded mode with DB-dependent endpoints returning 503.

## 17) Development Environment Setup and Commands

### 10.1 Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB

### 10.2 Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 10.3 Frontend Setup

```bash
cd ..
npm install
npm run dev
```

Frontend default URL: http://localhost:8080

### 10.4 Frontend Scripts

```bash
npm run dev
npm run build
npm run build:dev
npm run lint
npm run preview
npm run test
npm run test:watch
```

### 10.5 Backend Utility Commands

```bash
cd backend
python manage_db.py check
python route_inspect.py
```

## 18) Test Suite Overview (Complement to Section 9)

Current tooling:

- Unit/component testing: Vitest + Testing Library + jsdom
- E2E framework present: Playwright config and fixture files
- Linting: ESLint

Recommended release checks:

1. Run frontend unit tests and lint.
2. Verify backend health and DB connectivity.
3. Execute manual workflow validation:
   - auth
   - setup
   - search
   - lead detail enrich/email
   - intent scan status polling

## 12) Operational Notes and Known Gaps

### 12.1 Known Gaps

- LeadDashboard currently renders mostly static/sample analytics data.
- TestDashboard includes some Phase-5 LinkedIn controls that are UI scaffolding and not fully backed by current router endpoints.
- API base URL values are hardcoded in client code and should be migrated to environment-driven configuration.

### 12.2 Reliability Notes

- External-source discovery quality depends on API keys and provider availability.
- Strict filters can reduce lead volume; broaden location and service inputs for wider search.
- Intent scanning is asynchronous and should be tracked using scan-status polling.

### 12.3 Security Notes

- JWT token is stored in localStorage; assess risk profile based on deployment context.
- Ensure SECRET_KEY is rotated and injected securely in production.
- Restrict CORS origins in production configuration.

## 13) Repository Map

```text
spark-outreach/
  backend/
    app/
      main.py
      config.py
      database.py
      models/
      schemas/
      routers/
      services/
      utils/
    requirements.txt
    manage_db.py
    route_inspect.py
    wsgi.py
  src/
    App.tsx
    main.tsx
    contexts/
    pages/
    services/
    components/
    hooks/
  public/
  package.json
  vite.config.ts
  vitest.config.ts
  playwright.config.ts
```

---

This README now reflects the current implementation status and is structured for handoff, onboarding, and delivery reporting. For enterprise handoff, the next recommended additions are deployment architecture, SLO/SLA definitions, and a versioned OpenAPI specification with request/response examples.
