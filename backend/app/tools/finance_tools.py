from app.models import FinanceRecord

def search_finance_records(db, query: str, owner_id: str="demo-user"):
    q=db.query(FinanceRecord).filter(FinanceRecord.owner_id==owner_id)
    if query:
        q=q.filter((FinanceRecord.company.ilike(f"%{query}%")) | (FinanceRecord.invoice_number.ilike(f"%{query}%")))
    return q.all()

def create_finance_record(db, payload: dict, owner_id: str="demo-user"):
    hit=db.query(FinanceRecord).filter_by(idempotency_key=payload.get("idempotency_key")).first()
    if hit: return {"status":"idempotent_hit","id":hit.id}
    dup=db.query(FinanceRecord).filter_by(invoice_number=payload["invoice_number"], owner_id=owner_id).first()
    if dup: return {"status":"duplicate","id":dup.id}
    if payload.get("inject_timeout"):
        rec=FinanceRecord(invoice_number=payload["invoice_number"],company=payload["company"],amount=payload["amount"],currency=payload["currency"],due_date=payload["due_date"],source_file=payload.get("source_file",""),idempotency_key=payload["idempotency_key"], owner_id=owner_id)
        db.add(rec); db.commit(); db.refresh(rec)
        raise TimeoutError("503 Simulated — response lost but persisted")
    rec=FinanceRecord(invoice_number=payload["invoice_number"],company=payload["company"],amount=payload["amount"],currency=payload["currency"],due_date=payload["due_date"],source_file=payload.get("source_file",""),idempotency_key=payload["idempotency_key"], owner_id=owner_id)
    db.add(rec); db.commit(); db.refresh(rec)
    return {"status":"created","id":rec.id}
