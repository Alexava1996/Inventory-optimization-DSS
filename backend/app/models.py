import time
import uuid
from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def uid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "inventory_users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))


class LoginAttempt(Base):
    __tablename__ = "inventory_login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    reset_at: Mapped[float] = mapped_column(Float)


class Session(Base):
    __tablename__ = "inventory_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("inventory_users.id"), index=True)
    expires_at: Mapped[float] = mapped_column(Float)


class Product(Base):
    __tablename__ = "inventory_products"
    __table_args__ = (
        UniqueConstraint("user_id", "sku"),
        CheckConstraint("stock >= 0"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("inventory_users.id"), index=True)
    sku: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(160))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    stock_known: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class Observation(Base):
    __tablename__ = "inventory_observations"
    __table_args__ = (
        UniqueConstraint("product_id", "year"),
        CheckConstraint("annual_demand >= 0 AND order_cost > 0 AND holding_cost > 0"),
        CheckConstraint("lead_time_days >= 0 AND (safety_stock IS NULL OR safety_stock >= 0)"),
        CheckConstraint("year >= 1900 AND year <= 2200"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    product_id: Mapped[str] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    annual_demand: Mapped[float] = mapped_column(Float)
    order_cost: Mapped[float] = mapped_column(Float)
    holding_cost: Mapped[float] = mapped_column(Float)
    lead_time_days: Mapped[int] = mapped_column(Integer)
    safety_stock: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Movement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    product_id: Mapped[str] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("inventory_users.id"))
    delta: Mapped[int] = mapped_column(Integer)
    resulting_stock: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    idempotency_key: Mapped[str] = mapped_column(String(36))
