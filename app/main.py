import time
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from .db import SessionLocal, engine, Base
from .models import User, Transaction
from .schemas import SignUpIn, LoginIn, UserOut, TransactionIn, TransactionOut

app = FastAPI(title="BudgetWise API")

# CORS (para Android y pruebas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para demo. Luego restringes.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# ---------- AUTH (demo, sin JWT todavía) ----------
@app.post("/auth/signup", response_model=UserOut)
def signup(body: SignUpIn, db: Session = Depends(get_db)):
    username = body.username.strip().lower()
    password = body.password.strip()

    if not username:
        raise HTTPException(status_code=400, detail="username obligatorio")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="password demasiado corta")

    existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        password=password,  # demo
    )
    db.add(user)
    db.commit()
    return UserOut(id=user.id, username=user.username)

@app.post("/auth/login", response_model=UserOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    username = body.username.strip().lower()
    password = body.password.strip()

    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return UserOut(id=user.id, username=user.username)

@app.post("/auth/reset-password")
def reset_password(body: SignUpIn, db: Session = Depends(get_db)):
    # reusamos SignUpIn: username + new password
    username = body.username.strip().lower()
    new_pass = body.password.strip()

    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if len(new_pass) < 4:
        raise HTTPException(status_code=400, detail="password demasiado corta")

    user.password = new_pass
    db.commit()
    return {"ok": True}

# ---------- TRANSACTIONS ----------
@app.get("/users/{user_id}/transactions", response_model=list[TransactionOut])
def list_transactions(user_id: str, db: Session = Depends(get_db)):
    # validar usuario
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    rows = db.execute(select(Transaction).where(Transaction.user_id == user_id)).scalars().all()
    # orden por fecha string dd/MM/yyyy no es ideal, pero para demo vale; tu app ordena en cliente.
    return [
        TransactionOut(
            id=t.id,
            user_id=t.user_id,
            type=t.type,
            amount=t.amount,
            category=t.category,
            note=t.note,
            date=t.date,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in rows
    ]

@app.post("/users/{user_id}/transactions", response_model=TransactionOut)
def upsert_transaction(user_id: str, body: TransactionIn, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    now = int(time.time() * 1000)

    existing = db.execute(
        select(Transaction).where(Transaction.id == body.id, Transaction.user_id == user_id)
    ).scalar_one_or_none()

    if existing:
        existing.type = body.type
        existing.amount = body.amount
        existing.category = body.category
        existing.note = body.note
        existing.date = body.date
        existing.updated_at = now
        db.commit()
        t = existing
    else:
        t = Transaction(
            id=body.id,
            user_id=user_id,
            type=body.type,
            amount=body.amount,
            category=body.category,
            note=body.note,
            date=body.date,
            created_at=now,
            updated_at=now,
        )
        db.add(t)
        db.commit()

    return TransactionOut(
        id=t.id,
        user_id=t.user_id,
        type=t.type,
        amount=t.amount,
        category=t.category,
        note=t.note,
        date=t.date,
        created_at=t.created_at,
        updated_at=t.updated_at
    )

@app.delete("/users/{user_id}/transactions/{tx_id}")
def delete_transaction(user_id: str, tx_id: str, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    res = db.execute(delete(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user_id))
    db.commit()

    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    return {"ok": True}
