"""
Pydantic schemas for query planning and lead discovery
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class IntentSignal(str, Enum):
    """Premium buying intent signals"""
    HIRING = "hiring"
    FUNDING = "funding"
    EXPANSION = "expansion"
    MODERNIZATION = "modernization"
    BUYING_INTENT = "buying_intent"


class QueryScore(BaseModel):
    """Scored, characterized query with intent signals"""
    query: str = Field(..., description="The search query")
    score: float = Field(..., description="Intent score 0-1")
    signals: List[str] = Field(default_factory=list, description="Intent signals detected")
    why: Optional[str] = Field(default=None, description="Why this query scores high")


class QualitySummary(BaseModel):
    """Quality metrics for planner output"""
    selected_count: int = Field(..., description="Number of queries selected")
    avg_score: float = Field(..., description="Average quality score")


class PlannerResult(BaseModel):
    """Complete lead query planner output"""
    planner: str = Field(default="groq", description="Planner source (groq, heuristic, etc)")
    queries: List[str] = Field(..., description="Generated discovery queries")
    strategy: str = Field(..., description="High-level discovery strategy")
    model: str = Field(default="qwen/qwen3-32b", description="LLM model used")
    quality_summary: QualitySummary = Field(..., description="Quality metrics")
    scored_queries: Optional[List[QueryScore]] = Field(
        default=None, description="Detailed scores (for diagnostics)"
    )
