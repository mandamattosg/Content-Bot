from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Signal(BaseModel):
    source: str
    title: str
    content: str
    url: HttpUrl
    published_at: datetime
    metadata: dict = Field(default_factory=dict)
