from pydantic import BaseModel
from app.schemas.artist import BasicArtistOut

class ConfirmRequest(BaseModel):
    task_id: str