from pydantic import BaseModel

class SignUpIn(BaseModel):
    username: str
    password: str

class LoginIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str

class TransactionIn(BaseModel):
    id: str
    type: str
    amount: float
    category: str
    note: str
    date: str

class TransactionOut(TransactionIn):
    user_id: str
    created_at: int
    updated_at: int
