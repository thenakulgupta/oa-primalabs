from typing import Literal

from pydantic import BaseModel, Field


class UsageGroupRow(BaseModel):
    group_key: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float


class UsageResponse(BaseModel):
    api_key: str
    from_: str = Field(serialization_alias="from")
    to: str
    group_by: Literal["day", "model"]
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    groups: list[UsageGroupRow]

    model_config = {"populate_by_name": True}
