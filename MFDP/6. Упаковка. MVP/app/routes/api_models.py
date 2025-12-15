from pydantic import BaseModel
from datetime import datetime


class ModelEventOut(BaseModel):
    prediction_id: int
    creator_id: int
    timestamp: datetime
    candidates: list

class UserOut(BaseModel):
    user_id: int
    is_admin: bool


class ModelIn(BaseModel):
    version: int
    path: str


class ModelOut(BaseModel):
    model_id: int
    version: int
    path: str

class Tank(BaseModel):
    tank_id: int
    name: str
    tier: int
    nation: str
    type: str
    is_premium: bool
    image: str


class Token(BaseModel):
    access_token: str
    token_type: str
