"""
Company profile router
Endpoints for company setup and context management
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.schemas.company import (
    CompanyProfileCreateRequest,
    CompanyProfileUpdateRequest,
    CompanyProfileResponse,
    CompanySetupStepRequest,
    CompanyQueryRequest,
    CompanyQueryResponse
)
from app.services.company_service import CompanyService
from app.utils.auth import decode_token

router = APIRouter(prefix="/company", tags=["company"])

def get_user_from_token(authorization: Optional[str]) -> str:
    """Extract user email from authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return token_data["email"]

@router.post("/profile", response_model=CompanyProfileResponse)
async def create_company_profile(
    request: CompanyProfileCreateRequest,
    authorization: Optional[str] = Header(None)
):
    """Create new company profile"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        data = request.dict(exclude_none=True)
        profile = CompanyService.create_or_update_company_profile(str(user.id), data)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company profile: {str(e)}"
        )

@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(authorization: Optional[str] = Header(None)):
    """Get current user's company profile"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = CompanyService.get_company_profile(str(user.id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found. Please create one first."
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch company profile: {str(e)}"
        )

@router.put("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    request: CompanyProfileUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """Update company profile"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        data = request.dict(exclude_none=True)
        profile = CompanyService.create_or_update_company_profile(str(user.id), data)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update company profile: {str(e)}"
        )

@router.post("/profile/generate-embeddings", response_model=CompanyProfileResponse)
async def generate_embeddings(authorization: Optional[str] = Header(None)):
    """Generate embeddings for company context"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = await CompanyService.generate_company_embeddings(str(user.id))
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )

@router.post("/profile/query", response_model=CompanyQueryResponse)
async def query_company_profile(
    request: CompanyQueryRequest,
    authorization: Optional[str] = Header(None)
):
    """Query company details using embeddings and retrieve the most relevant company context."""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        response = await CompanyService.query_company_profile(
            str(user.id),
            request.query,
            top_k=request.top_k
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query company profile: {str(e)}"
        )

@router.post("/profile/generate-icp", response_model=CompanyProfileResponse)
async def generate_icp_and_signals(authorization: Optional[str] = Header(None)):
    """Generate ICP and signals from company context"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = await CompanyService.generate_icp_and_signals(str(user.id))
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ICP: {str(e)}"
        )

@router.post("/profile/complete-setup", response_model=CompanyProfileResponse)
async def complete_setup(authorization: Optional[str] = Header(None)):
    """Mark company setup as complete"""
    try:
        from app.models.user import User
        email = get_user_from_token(authorization)
        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = CompanyService.complete_setup(str(user.id))
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete setup: {str(e)}"
        )
