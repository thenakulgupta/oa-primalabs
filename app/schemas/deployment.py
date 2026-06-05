from typing import Literal

from pydantic import BaseModel, Field


class CreateDeploymentRequest(BaseModel):
    model: Literal["model-a", "model-b"]


class CreateDeploymentResponse(BaseModel):
    deployment_id: str
    status: Literal["provisioning"]


class DeploymentResponse(BaseModel):
    deployment_id: str
    status: str
    model: str
    endpoint_url: str | None = None
    api_key: str | None = None
