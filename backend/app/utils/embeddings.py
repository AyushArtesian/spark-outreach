"""
Embeddings and RAG utilities
"""
from typing import List
import asyncio


_embeddings_model = None


def _get_embeddings_model():
    """Lazy load local sentence-transformers model once."""
    global _embeddings_model
    if _embeddings_model is None:
        from sentence_transformers import SentenceTransformer
        _embeddings_model = SentenceTransformer("paraphrase-mpnet-base-v2")
    return _embeddings_model

class EmbeddingService:
    """Service for handling embeddings and vector operations"""
    
    def __init__(self):
        """Initialize embedding service"""
        self.embedding_model = "paraphrase-mpnet-base-v2"
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for text using local SentenceTransformers.
        """
        input_text = (text or "").strip()
        if not input_text:
            return [0.0] * 768

        try:
            model = _get_embeddings_model()
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None,
                lambda: model.encode(input_text, convert_to_tensor=False),
            )
            return [float(x) for x in vector]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 768
    
    async def similarity_search(
        self, 
        query_vector: List[float], 
        vectors: List[List[float]], 
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar vectors using cosine similarity
        Returns list of (index, similarity_score) tuples
        """
        similarities = []
        
        for idx, vec in enumerate(vectors):
            # Cosine similarity
            dot_product = sum(q * v for q, v in zip(query_vector, vec))
            magnitude_q = sum(q ** 2 for q in query_vector) ** 0.5
            magnitude_v = sum(v ** 2 for v in vec) ** 0.5
            
            if magnitude_q > 0 and magnitude_v > 0:
                similarity = dot_product / (magnitude_q * magnitude_v)
            else:
                similarity = 0.0
            
            similarities.append((idx, similarity))
        
        # Sort by similarity descending and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for embedding
        """
        chunks = []
        words = text.split()
        
        chunk_words = []
        for word in words:
            chunk_words.append(word)
            
            if len(" ".join(chunk_words)) >= chunk_size:
                chunks.append(" ".join(chunk_words))
                # Keep overlap words for context
                chunk_words = chunk_words[-(overlap // 5):]
        
        if chunk_words:
            chunks.append(" ".join(chunk_words))
        
        return chunks

embedding_service = EmbeddingService()
