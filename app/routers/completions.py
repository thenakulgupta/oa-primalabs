from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.completion import CompletionRequest, CompletionResponse
from app.services.completion_service import (
    ApiKeyMismatchError,
    DeploymentNotReadyError,
    InvalidApiKeyError,
    create_completion,
)
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/v1", tags=["completions"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/{deployment_id}/completions", response_model=CompletionResponse)
def post_completion(
    deployment_id: str,
    body: CompletionRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CompletionResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    api_key = credentials.credentials
    if not rate_limiter.is_allowed(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (100 requests per minute)",
        )

    try:
        return create_completion(db, deployment_id, api_key, body.prompt)
    except InvalidApiKeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    except ApiKeyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not match this deployment",
        )
    except DeploymentNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deployment is not ready",
        )
