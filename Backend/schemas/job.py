from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from db.database import Base


class StoryJobBase(BaseModel):
    theme: str


class StoryJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    story_id: Optional[int] = None
    complete_at: Optional[datetime] = None
    error: Optional[str] = None

    class config:
        from_attributes = True


class StoryJobCreate(StoryJobBase):
    pass
