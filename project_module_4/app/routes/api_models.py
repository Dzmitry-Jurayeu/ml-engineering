from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema
from datetime import datetime


class Balance(BaseModel):
    balance_id: int
    user_id: int
    last_update: datetime
    balance_value: int


class ModelEventIn(BaseModel):
    text: str = Field(default=None, min_length=1, max_length=300)
    title: str = Field(default="Model request", min_length=1, max_length=30)


class ModelEventOut(BaseModel):
    event_id: int
    creator_id: int
    text: str
    title: str
    score: float | None
    response: str | None
    amount: int
    timestamp: datetime


class BalanceReplenishmentEventIn(BaseModel):
    title: str = Field(default="Balance operation", min_length=1, max_length=30)
    amount: int = Field(default=0)


class BalanceReplenishmentEventOut(BaseModel):
    event_id: int
    creator_id: int
    title: str
    amount: int
    timestamp: datetime


class UserSignIn(BaseModel):
    username: str
    password: str


class UserSignUp(BaseModel):
    email: str
    password: str
    is_admin: SkipJsonSchema[bool] = False


class UserEmail(BaseModel):
    email: str


class UserOut(BaseModel):
    user_id: int
    email: str
    password: str
    is_admin: bool


class ModelIn(BaseModel):
    task: str
    model_name: str


class ModelOut(BaseModel):
    model_id: int
    task: str
    model_name: str


class Token(BaseModel):
    access_token: str
    token_type: str
