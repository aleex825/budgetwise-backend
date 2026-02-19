from sqlalchemy import String, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)         # UUID
    username: Mapped[str] = mapped_column(String, nullable=False)     # email
    password: Mapped[str] = mapped_column(String, nullable=False)     # demo (plain)

    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)         # UUID
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    type: Mapped[str] = mapped_column(String, nullable=False)         # "GASTO" / "INGRESO"
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False, default="")
    date: Mapped[str] = mapped_column(String, nullable=False)         # "dd/MM/yyyy"

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="transactions")
