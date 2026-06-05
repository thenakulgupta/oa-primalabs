from sqlalchemy.orm import Session

from app.models.deployment import Deployment, DeploymentStatus
from app.schemas.deployment import DeploymentResponse


class DeploymentNotFoundError(Exception):
    pass


def create_deployment(db: Session, model: str) -> Deployment:
    deployment = Deployment(model=model, status=DeploymentStatus.PROVISIONING.value)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


def get_deployment(db: Session, deployment_id: str) -> Deployment:
    deployment = db.get(Deployment, deployment_id)
    if deployment is None:
        raise DeploymentNotFoundError(deployment_id)
    return deployment


def terminate_deployment(db: Session, deployment_id: str) -> Deployment:
    deployment = get_deployment(db, deployment_id)
    deployment.status = DeploymentStatus.TERMINATED.value
    db.commit()
    db.refresh(deployment)
    return deployment


def to_response(deployment: Deployment) -> DeploymentResponse:
    response = DeploymentResponse(
        deployment_id=deployment.id,
        status=deployment.status,
        model=deployment.model,
    )
    if deployment.status == DeploymentStatus.READY.value:
        return response.model_copy(
            update={
                "endpoint_url": deployment.endpoint_url,
                "api_key": deployment.api_key,
            }
        )
    return response
