from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, UniqueConstraint
from datetime import datetime
from app.database import Base

class Task(Base):
    __tablename__="tasks"
    id=Column(Integer, primary_key=True)
    goal=Column(Text, nullable=False)
    status=Column(String, default="pending") # pending,executing,awaiting_approval,awaiting_clarification,verifying,completed,failed,cancelled
    memory=Column(JSON, default=dict)
    owner_id=Column(String, index=True, default="demo-user")
    idempotency_key=Column(String)
    approval_granted=Column(Boolean, default=False)
    approval_required=Column(Boolean, default=True)
    pending_hash=Column(String)
    token_budget=Column(Integer, default=15000)
    tokens_used=Column(Integer, default=0)
    cost_usd=Column(Float, default=0.0)
    max_steps=Column(Integer, default=15)
    created_at=Column(DateTime, default=datetime.utcnow)

class FinanceRecord(Base):
    __tablename__="finance_records"
    id=Column(Integer, primary_key=True)
    invoice_number=Column(String, index=True)
    company=Column(String, index=True)
    amount=Column(Float)
    currency=Column(String)
    due_date=Column(String)
    source_file=Column(String)
    owner_id=Column(String, index=True, default="demo-user")
    idempotency_key=Column(String, unique=True, index=True)
    created_at=Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('invoice_number', 'owner_id', name='uq_invoice_owner'),)

class Event(Base):
    __tablename__="events"
    id=Column(Integer, primary_key=True)
    task_id=Column(Integer, index=True)
    tool=Column(String)
    args=Column(JSON)
    result=Column(Text)
    status=Column(String) # success,failure
    duration_ms=Column(Integer)
    retry=Column(Integer, default=0)
    evidence_ref=Column(String)
    created_at=Column(DateTime, default=datetime.utcnow)
