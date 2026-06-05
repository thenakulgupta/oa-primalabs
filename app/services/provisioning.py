import random
import secrets
import time

from sqlalchemy.orm import Session

from app import database
from app.config import settings
from app.models.deployment import Deployment, DeploymentStatus


def _provisioning_delay_seconds() -> float:
    if settings.provisioning_delay_seconds is not None:
        return settings.provisioning_delay_seconds
    return random.uniform(
        settings.provisioning_delay_min,
        settings.provisioning_delay_max,
    )


def provision_deployment_sync(deployment_id: str) -> None:
    time.sleep(_provisioning_delay_seconds())

    db: Session = database.SessionLocal()
    try:
        deployment = db.get(Deployment, deployment_id)
        if deployment is None or deployment.status != DeploymentStatus.PROVISIONING.value:
            return

        api_key = secrets.token_urlsafe(32)
        deployment.status = DeploymentStatus.READY.value
        deployment.api_key = api_key
        deployment.endpoint_url = (
            f"https://backend.primalabs.ai/v1/{deployment_id}/completions"
        )
        db.commit()
    finally:
        db.close()
