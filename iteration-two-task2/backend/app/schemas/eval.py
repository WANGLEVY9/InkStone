from pydantic import BaseModel


class ExecuteResponse(BaseModel):
    task_id: int
    message: str
    worker_task_id: str | None = None
