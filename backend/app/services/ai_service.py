"""
Service for AI-related operations including embeddings and message generation
"""
from typing import Optional, List, Dict, Any
import warnings
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.embedding import Embedding
from app.utils.embeddings import embedding_service
from app.config import settings

try:
    from google import genai
    _GEMINI_MODE = "new"
except ImportError:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai  # type: ignore
    _GEMINI_MODE = "legacy"

class AIService:
    """Service for AI operations including embeddings, RAG, and content generation"""
    
    def __init__(self):
        """Initialize AI service with configured provider"""
        self.model = None
        self.client = None
        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            if _GEMINI_MODE == "new":
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            else:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.provider = settings.LLM_PROVIDER
    
    async def generate_lead_message(
        self,
        lead: Lead,
        campaign: Campaign,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a personalized message for a lead using AI
        Supports both Gemini and OpenAI APIs
        """
        prompt = f"""
You are a professional outreach specialist. Generate a personalized email message for the following lead:

Lead Information:
- Name: {lead.name}
- Company: {lead.company}
- Job Title: {lead.job_title}
- Industry: {lead.industry}

Campaign Information:
- Title: {campaign.title}
- Content: {campaign.content}
- Target Audience: {campaign.target_audience}

Custom Instructions:
{campaign.custom_instructions or 'None'}

Additional Context:
{context or 'None'}

Generate a personalized, professional email message that:
1. Addresses the lead by name
2. References their company/industry when relevant
3. Is concise and compelling
4. Has a clear call-to-action
5. Respects the character limit of {campaign.max_tokens} tokens

Message:
"""
        
        try:
            if self.provider == "gemini":
                if _GEMINI_MODE == "new" and self.client:
                    response = self.client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=prompt,
                    )
                    return response.text or ""
                if self.model:
                    response = self.model.generate_content(prompt)
                    return response.text
                return "Gemini is not configured. Please set GEMINI_API_KEY in .env"
            else:
                # Placeholder for OpenAI implementation
                return "Generated message placeholder (configure OpenAI API key)"
        except Exception as e:
            print(f"Error generating message: {e}")
            return "Error generating personalized message. Please try again."
    
    async def analyze_lead_relevance(
        self,
        lead: Lead,
        campaign: Campaign
    ) -> float:
        """
        Analyze how relevant a lead is to the campaign using embeddings
        Returns a relevance score from 0 to 1
        """
        # Get or create embeddings for lead profile
        lead_text = f"{lead.name} {lead.company} {lead.job_title} {lead.industry}".strip()
        
        # Get or create embeddings for campaign target
        campaign_text = f"{campaign.title} {campaign.content} {campaign.target_audience}"
        
        lead_embedding = await embedding_service.create_embedding(lead_text)
        campaign_embedding = await embedding_service.create_embedding(campaign_text)
        
        # Calculate similarity
        similarities = await embedding_service.similarity_search(
            campaign_embedding, 
            [lead_embedding], 
            top_k=1
        )
        
        if similarities:
            relevance_score = min(1.0, max(0.0, similarities[0][1]))
        else:
            relevance_score = 0.0
        
        return relevance_score
    
    async def retrieve_relevant_context(
        self,
        query: str,
        campaign_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from campaign embeddings using RAG
        """
        # Create embedding for query
        query_embedding = await embedding_service.create_embedding(query)
        
        # Get all embeddings for this campaign from MongoDB
        embeddings = Embedding.objects(campaign_id=campaign_id)
        
        if not embeddings:
            return []
        
        # Find similar embeddings
        similar = await embedding_service.similarity_search(
            query_embedding,
            [emb.embedding_vector for emb in embeddings],
            top_k=top_k
        )
        
        results = []
        embeddings_list = list(embeddings)
        for idx, score in similar:
            if idx < len(embeddings_list):
                results.append({
                    "content": embeddings_list[idx].content,
                    "metadata": embeddings_list[idx].embedding_metadata,
                    "score": score
                })
        
        return results
    
    async def create_campaign_embeddings(
        self,
        campaign: Campaign
    ) -> int:
        """
        Create embeddings for campaign content for RAG
        Returns number of embeddings created
        """
        # Chunk the campaign content
        chunks = embedding_service.chunk_text(campaign.content)
        
        embeddings_created = 0
        
        for chunk_idx, chunk in enumerate(chunks):
            # Create embedding
            embedding_vector = await embedding_service.create_embedding(chunk)
            
            # Store in database
            embedding = Embedding(
                campaign_id=str(campaign.id),
                content=chunk,
                embedding_vector=embedding_vector,  # Native list in MongoDB
                embedding_model=embedding_service.embedding_model,
                chunk_index=chunk_idx,
                embedding_metadata={
                    "chunk_count": len(chunks),
                    "chunk_size": len(chunk)
                }
            )
            embedding.save()  # MongoDB save
            embeddings_created += 1
        
        return embeddings_created

# Initialize AI service singleton
ai_service = AIService()
