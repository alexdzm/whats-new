from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    band_name: str
    date: datetime
    venue: str
    description: str