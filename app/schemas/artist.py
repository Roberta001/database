from pydantic import BaseModel

class BasicArtistOut(BaseModel):
    id: int
    name: str