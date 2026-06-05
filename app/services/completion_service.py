import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.deployment import Deployment, DeploymentStatus
from app.models.usage_event import UsageEvent
from app.schemas.completion import CompletionResponse
from app.services.deployment_service import DeploymentNotFoundError, get_deployment


class InvalidApiKeyError(Exception):
    pass


class DeploymentNotReadyError(Exception):
    pass


class ApiKeyMismatchError(Exception):
    pass


def compute_input_tokens(prompt: str) -> int:
    return round(len(prompt) / 4)


def create_completion(
    db: Session,
    deployment_id: str,
    api_key: str,
    prompt: str,
) -> CompletionResponse:
    key_owner = db.query(Deployment).filter(Deployment.api_key == api_key).first()
    if key_owner is None:
        raise InvalidApiKeyError()

    try:
        deployment = get_deployment(db, deployment_id)
    except DeploymentNotFoundError:
        raise ApiKeyMismatchError() from None

    if deployment.api_key != api_key:
        raise ApiKeyMismatchError()

    if deployment.status != DeploymentStatus.READY.value:
        raise DeploymentNotReadyError(deployment.status)

    input_tokens = compute_input_tokens(prompt)
    output_tokens = random.randint(50, 200)

    event = UsageEvent(
        api_key=api_key,
        deployment_id=deployment_id,
        model=deployment.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()

    return CompletionResponse(
        output="mocked response",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
