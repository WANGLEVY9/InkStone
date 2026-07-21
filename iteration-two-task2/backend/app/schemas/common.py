from datetime import datetime

from pydantic import BaseModel


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 10


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int


class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime
