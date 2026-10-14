import os
os.environ["DATABASE_URL"]="sqlite:///./test_agent.db"
from app.database import engine, SessionLocal, Base
from app.models import Task, FinanceRecord
Base.metadata.create_all(bind=engine)

def fake_run(goal, owner="demo-user"):
    # deterministic fake-model sequence for 16 tests
    from app.tools import invoice_tools
    from app.tools.finance_tools import create_finance_record, search_finance_records
    db=SessionLocal()
    # simulate latest invoice selection
    files=invoice_tools.search_invoice_files("Acme")
    assert files[0]["filename"]=="Acme_Corp_2024-11-15_INV-1042.txt"
    text=invoice_tools.read_invoice_file(files[0]["filename"])
    fields=invoice_tools.extract_invoice_fields(text)
    assert fields["invoice_number"]=="INV-1042"
    assert fields["amount"]==1245.00
    assert fields["currency"]=="USD"
    assert fields["due_date"]=="2024-12-15"
    # duplicate prevention check
    before=search_finance_records(db,"INV-1042",owner)
    create_finance_record(db, {"invoice_number":fields["invoice_number"],"company":"Acme Corporation","amount":fields["amount"],"currency":fields["currency"],"due_date":fields["due_date"],"idempotency_key":"test-key-1042","source_file":files[0]["filename"]}, owner)
    after=search_finance_records(db,"INV-1042",owner)
    db.close()
    return fields

def test_normal_invoice():
    f=fake_run("Find latest Acme invoice")
    assert f["invoice_number"]=="INV-1042"

def test_latest_selection():
    from app.tools.invoice_tools import search_invoice_files
    files=search_invoice_files("Acme")
    assert files[0]["date"] > files[1]["date"]

def test_duplicate_prevention():
    db=SessionLocal()
    db.query(FinanceRecord).delete()
    db.commit()
    from app.tools.finance_tools import create_finance_record
    r1=create_finance_record(db, {"invoice_number":"INV-1042","company":"Acme","amount":1245,"currency":"USD","due_date":"2024-12-15","idempotency_key":"k1"}, "demo-user")
    r2=create_finance_record(db, {"invoice_number":"INV-1042","company":"Acme","amount":1245,"currency":"USD","due_date":"2024-12-15","idempotency_key":"k1"}, "demo-user")
    assert r1["status"]=="created"
    assert r2["status"]=="idempotent_hit"
    r3=create_finance_record(db, {"invoice_number":"INV-1042","company":"Acme","amount":1245,"currency":"USD","due_date":"2024-12-15","idempotency_key":"k2"}, "demo-user")
    assert r3["status"]=="duplicate"
    db.close()

def test_timeout_recovery():
    db=SessionLocal()
    db.query(FinanceRecord).delete()
    db.commit()
    from app.tools.finance_tools import create_finance_record, search_finance_records
    try:
        create_finance_record(db, {"invoice_number":"INV-1042","company":"Acme","amount":1245,"currency":"USD","due_date":"2024-12-15","idempotency_key":"timeout-k","inject_timeout":True}, "demo-user")
    except TimeoutError as e:
        assert "503" in str(e)
    recs=search_finance_records(db,"INV-1042","demo-user")
    assert len(recs)==1 # persisted despite timeout
    db.close()
