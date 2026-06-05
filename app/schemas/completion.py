from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class CompletionResponse(BaseModel):
    output: str
    input_tokens: int
    output_tokens: int
