from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="业务错误码")
    message: str = Field(description="错误信息")
    detail: dict = Field(default_factory=dict, description="错误上下文")
    request_id: str | None = Field(default=None, description="请求追踪ID")
