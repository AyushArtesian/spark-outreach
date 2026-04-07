# Spark Outreach

A full-stack outreach platform for building company profiles, generating rich company embeddings, and testing semantic retrieval through a UI.

## Overview

This project combines a modern React frontend with a FastAPI backend and MongoDB persistence to support:
- company profile setup and contextual enrichment
- website and portfolio scraping
- local embedding generation using SentenceTransformers
- company embedding testing through a settings UI
- JWT authentication and protected API routes

## What we have built so far

### Backend
- FastAPI backend with clean routing and authentication
- MongoDB via MongoEngine for persistent company profiles and user data
- JWT auth using `python-jose` and Argon2 password hashing
- Company profile data model including:
  - company details, services, technologies, target industries, team expertise
  - manual projects, portfolio URLs, GitHub, LinkedIn, Upwork
  - cached scraped website and portfolio content
- Web scraping service to fetch:
  - company website content and internal pages
  - GitHub user/org/repo metadata
  - LinkedIn profile fallback signals
  - Upwork agency fallback signals
  - additional portfolio URLs
- Local embedding generation using `sentence-transformers`:
  - model: `paraphrase-mpnet-base-v2`
  - rich 768-dimensional semantic embeddings
- Embedding text builder that includes both:
  - manual profile fields and project data
  - fetched website/portfolio content
- Company profile query endpoint: `POST /api/v1/company/profile/query`
  - supports natural language questions against company context
  - returns top matching content chunks with relevance scores
- Graceful fallback behavior for blocked external sources

### Frontend
- React + TypeScript application using Vite
- Tailwind CSS with shadcn/ui style components
- Protected routes and auth state management
- Company setup wizard for entering profile and portfolio details
- Settings page with a built-in embedding test UI for direct company query testing
- API client utility with automatic JWT authorization
- `companyAPI.queryProfile()` support for embedding QA requests

## Tech Stack

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- React Router DOM
- React Query
- Framer Motion
- Lucide Icons
- Zod

### Backend
- Python 3.x
- FastAPI
- Uvicorn
- MongoDB + MongoEngine
- Python-JOSE
- passlib[argon2]
- Pydantic / pydantic-settings
- aiohttp
- BeautifulSoup4
- sentence-transformers
- google-genai (optional Gemini support)

### AI / Embeddings
- `sentence-transformers` local model
- `paraphrase-mpnet-base-v2` for high-quality semantic vectors
- Local embedding generation after first model download
- No OpenAI API key required for embeddings

## Setup Instructions

### Backend

1. Create and activate Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables in `backend/.env`:
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
4. Run backend:
   ```bash
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Frontend

1. From the project root:
   ```bash
   npm install
   ```
2. Start the frontend:
   ```bash
   npm run dev
   ```
3. Open the app in the browser at `http://localhost:5173`

## How to Test Embeddings

1. Create or update your company profile through the company setup flow.
2. Generate company embeddings using the backend endpoint or UI flow.
3. Open `Settings` and select the new `Embedding Test` tab.
4. Enter a question about your company and run the test.
5. Review the top matching chunks and score results.

### API Test Option

Alternatively, you can call the backend directly:
- `POST /api/v1/company/profile/query`
- body: `{ "query": "What web development services do we offer?", "top_k": 3 }`
- requires Bearer JWT authorization

## Current Features

- Company profile creation and update
- Company website, GitHub, LinkedIn, Upwork, and portfolio scraping
- Local sentence-transformer embeddings with richer semantic dimension
- Embedding test UI in Settings
- API route for company profile semantic querying
- Graceful handling of blocked or unavailable external sources

## Future Work

- Add chat-style conversational QA over company embeddings
- Build a “single answer” response layer from top retrieval results
- Add campaign-level RAG and lead matching using company embeddings
- Add direct lead scoring using company and campaign semantic similarity
- Add OpenAI/Gemini prompt-based summaries and content generation
- Improve scraper reliability for multiple business sites and content sources
- Add more advanced analytics and lead signal extraction

## Notes

- Upwork and LinkedIn scraping may be blocked by bot protection; the system preserves source signals even when direct scraping fails.
- GitHub data may be rate-limited without authentication, but fallback scraping is available.
- The current embedding model is local and does not require external paid APIs for inference.

## Project Structure

- `backend/` - FastAPI backend, models, routers, services, and embedding logic
- `src/` - React frontend pages, components, and API client
- `public/` - static assets
- `package.json` - frontend dependencies and scripts
- `backend/requirements.txt` - backend Python dependencies
- `README.md` - project documentation

---

This README reflects the current state of the project and the major work completed so far, including company context enrichment, local semantic embeddings, embedding testing UI, and the foundational outreach platform architecture.
