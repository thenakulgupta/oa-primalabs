from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.deployment import (
    CreateDeploymentRequest,
    CreateDeploymentResponse,
    DeploymentResponse,
)
from app.services.deployment_service import (
    DeploymentNotFoundError,
    create_deployment,
    get_deployment,
    terminate_deployment,
    to_response,
)
from app.services.provisioning import provision_deployment_sync

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=CreateDeploymentResponse, status_code=status.HTTP_201_CREATED)
def post_deployment(
    body: CreateDeploymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CreateDeploymentResponse:
    deployment = create_deployment(db, body.model)
    background_tasks.add_task(provision_deployment_sync, deployment.id)
    return CreateDeploymentResponse(
        deployment_id=deployment.id,
        status="provisioning",
    )


@router.get(
    "/{deployment_id}",
    response_model=DeploymentResponse,
    response_model_exclude_none=True,
)
def get_deployment_by_id(
    deployment_id: str,
    db: Session = Depends(get_db),
) -> DeploymentResponse:
    try:
        deployment = get_deployment(db, deployment_id)
    except DeploymentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return to_response(deployment)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deployment(
    deployment_id: str,
    db: Session = Depends(get_db),
) -> None:
    try:
        terminate_deployment(db, deployment_id)
    except DeploymentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
