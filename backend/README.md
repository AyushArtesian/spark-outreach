# Spark Outreach Backend

Python-based backend API for the Spark Outreach platform with AI-powered lead outreach capabilities.

## Features

- **FastAPI Backend**: High-performance REST API with async support
- **Database Models**: SQLAlchemy ORM with support for PostgreSQL, MySQL, SQLite
- **Authentication**: JWT-based user authentication with password hashing
- **Campaign Management**: Create and manage outreach campaigns
- **Lead Management**: Store, track, and manage leads with rich metadata
- **AI/ML Integration**:
  - OpenAI integration for personalized message generation
  - Embeddings for semantic similarity search
  - RAG (Retrieval-Augmented Generation) for context-aware responses
  - Lead relevance scoring
- **Asynchronous Processing**: Async/await support for long-running operations

## Technology Stack

- **Framework**: FastAPI with Uvicorn
- **Database**: SQLAlchemy ORM
- **Authentication**: Python-Jose, Passlib, Bcrypt
- **AI/ML**: LangChain, OpenAI API
- **Data Validation**: Pydantic
- **Environment**: Python-dotenv

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Database setup and session management
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py           # User model
│   │   ├── campaign.py        # Campaign model
│   │   ├── lead.py           # Lead model
│   │   └── embedding.py      # Embedding model for RAG
│   ├── schemas/               # Pydantic schemas for request/response validation
│   │   ├── user.py
│   │   ├── campaign.py
│   │   └── lead.py
│   ├── routers/               # API route handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── campaigns.py      # Campaign endpoints
│   │   ├── leads.py          # Lead endpoints
│   │   └── ai.py             # AI operation endpoints
│   ├── services/              # Business logic
│   │   ├── ai_service.py     # AI operations: embeddings, RAG, message generation
│   │   ├── campaign_service.py
│   │   └── lead_service.py
│   └── utils/                 # Utility functions
│       ├── auth.py           # Authentication utilities
│       └── embeddings.py     # Embedding and vector utilities
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Setup and Installation

### Prerequisites
- Python 3.10 or higher
- pip or poetry for package management

### 1. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
# Don't forget to update:
# - SECRET_KEY (generate a new one)
# - DATABASE_URL (if not using SQLite)
# - OPENAI_API_KEY (for AI features)
```

### 4. Initialize Database

```bash
# Create tables
python -c "from app.database import Base, engine; Base.metadata.create_all(engine)"
```

### 5. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user

### Campaigns
- `POST /api/v1/campaigns` - Create a campaign
- `GET /api/v1/campaigns` - List user's campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign details
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `POST /api/v1/campaigns/{id}/start` - Start campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign

### Leads
- `POST /api/v1/leads` - Create a lead
- `POST /api/v1/leads/bulk` - Create multiple leads
- `GET /api/v1/leads/{id}` - Get lead details
- `GET /api/v1/leads/campaign/{id}` - List campaign leads
- `PUT /api/v1/leads/{id}` - Update lead
- `POST /api/v1/leads/{id}/contact` - Generate and send message
- `DELETE /api/v1/leads/{id}` - Delete lead

### AI Operations
- `POST /api/v1/ai/rag-search` - Perform RAG search
- `POST /api/v1/ai/generate-message` - Generate personalized message
- `POST /api/v1/ai/create-embeddings` - Create embeddings for campaign

## Environment Variables

Key environment variables to configure:

```
DATABASE_URL              # Database connection string
SECRET_KEY               # JWT secret key
OPENAI_API_KEY          # OpenAI API key for embeddings and LLM
LLM_PROVIDER            # gemini | groq | openai
GROQ_API_KEY            # Groq API key for Qwen-based workflows
GROQ_MODEL              # Groq model id (default: qwen/qwen3-32b)
LEAD_QUERY_PLANNER_ENABLED      # Enable LLM-based search query planning
LEAD_QUERY_PLANNER_MAX_QUERIES  # Max generated search queries
DEBUG                   # Enable debug mode (False for production)
CORS_ORIGINS            # Comma-separated list of allowed origins
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
pylint app/
flake8 app/
```

## Database

### Supported Databases
- **SQLite**: Default, good for development
- **PostgreSQL**: Recommended for production
- **MySQL**: Also supported

### Using PostgreSQL
```
pip install psycopg2-binary
DATABASE_URL=postgresql://user:password@localhost/spark_outreach
```

### Using MySQL
```
pip install pymysql
DATABASE_URL=mysql+pymysql://user:password@localhost/spark_outreach
```

## AI Features

### Embeddings and RAG
- Text content is automatically chunked and embedded
- Embeddings are stored in the database for efficient retrieval
- RAG system allows context-aware responses based on campaign content

### Message Generation
- Uses OpenAI API to generate personalized outreach messages
- Considers lead information, campaign content, and custom instructions
- Can be integrated with email or messaging platforms

### Lead Relevance Scoring
- Automatically scores leads based on relevance to campaign
- Uses semantic similarity between lead profile and campaign target audience

## Deployment

### Docker Deployment (TODO)
```bash
docker build -t spark-outreach-backend .
docker run -p 8000:8000 --env-file .env spark-outreach-backend
```

### Cloud Deployment
- Can be deployed to AWS, Google Cloud, Azure, or any cloud provider supporting Python
- Consider using managed databases (RDS, Cloud SQL, etc.)
- Use environment variables for configuration

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation as needed
4. Use type hints in code

## Security Notes

⚠️ **Important Security Considerations:**

1. Change the `SECRET_KEY` in production
2. Use HTTPS in production
3. Rotate API keys regularly
4. Store sensitive data (API keys) in secure secret management systems
5. Use strong database passwords
6. Implement rate limiting for production
7. Enable CORS only for trusted origins
8. Keep dependencies updated

## Troubleshooting

### Common Issues

**Port already in use**
```bash
# Use a different port
uvicorn app.main:app --port 8001
```

**Database connection errors**
- Check DATABASE_URL is correct
- Verify database server is running
- Check database credentials

**OpenAI API errors**
- Verify OPENAI_API_KEY is set correctly
- Check API key has sufficient credits
- Verify API key permissions

## Future Enhancements

- [ ] Email integration for automated outreach
- [ ] Webhook support for external integrations
- [ ] Advanced analytics and reporting
- [ ] Lead import from various sources
- [ ] Scheduled campaign execution
- [ ] Multi-language support
- [ ] Advanced RAG with vector databases (Pinecone, Weaviate)
- [ ] Real-time notifications with WebSockets
- [ ] Rate limiting and usage analytics

## License

TODO: Add license information

## Support

For issues, feature requests, or questions, please create an issue in the repository.
