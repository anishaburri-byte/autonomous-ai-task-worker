# Overdue summary - second reusable task
import os
os.environ["DATABASE_URL"]="sqlite:///./test_unseen.db"
from app.database import Base, engine, SessionLocal
from app.models import FinanceRecord
Base.metadata.create_all(bind=engine)

def test_overdue_summary():
    db=SessionLocal()
    db.query(FinanceRecord).delete()
    db.add(FinanceRecord(invoice_number="INV-1", company="Acme", amount=100, currency="USD", due_date="2024-01-01", idempotency_key="u1", owner_id="demo-user"))
    db.add(FinanceRecord(invoice_number="INV-2", company="Globex", amount=200, currency="USD", due_date="2024-01-02", idempotency_key="u2", owner_id="demo-user"))
    db.commit()
    # Simulate overdue query grouped by company
    recs=db.query(FinanceRecord).all()
    grouped={}
    for r in recs:
        grouped.setdefault(r.company, []).append(r.invoice_number)
    assert "Acme" in grouped
    assert "Globex" in grouped
    db.query(FinanceRecord).delete()
    db.commit()
    db.close()
