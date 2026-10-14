import os, json, asyncio, uuid
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from app.database import engine, SessionLocal, Base
from app.models import Task, FinanceRecord, Event
from app.worker import run_task
from app.auth import require_user, create_token, sign_approval, verify_approval

Base.metadata.create_all(bind=engine)
os.makedirs("backend/evidence", exist_ok=True)
app=FastAPI(title="AI Worker v3")
FRONTEND_URL=os.getenv("FRONTEND_URL","http://localhost:5173")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_URL], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class CreateIn(BaseModel): goal: str
class LoginIn(BaseModel): user: str

@app.post("/api/auth/login")
def login(inp: LoginIn):
    return {"token": create_token(inp.user), "user": inp.user}

@app.post("/api/tasks")
def create_task(inp: CreateIn, bg: BackgroundTasks, user=Depends(require_user)):
    db=SessionLocal()
    t=Task(goal=inp.goal, status="pending", idempotency_key=str(uuid.uuid4()), memory={}, owner_id=user)
    db.add(t); db.commit(); db.refresh(t); tid=t.id; db.close()
    bg.add_task(run_task, tid)
    return {"id": tid, "status":"pending"}

@app.get("/api/tasks/{id}")
def get_task(id: int, user=Depends(require_user)):
    db=SessionLocal(); t=db.query(Task).filter_by(id=id, owner_id=user).first()
    if not t: db.close(); raise HTTPException(404)
    evs=db.query(Event).filter_by(task_id=id).order_by(Event.id).all()
    db.close()
    return {"task":{"id":t.id,"goal":t.goal,"status":t.status,"memory":t.memory,"tokens_used":t.tokens_used,"cost_usd":t.cost_usd,"pending_hash":t.pending_hash}, "events":[{"tool":e.tool,"args":e.args,"result":e.result,"status":e.status,"duration_ms":e.duration_ms,"retry":e.retry,"evidence_ref":e.evidence_ref} for e in evs]}

@app.post("/api/tasks/{id}/approve")
def approve(id: int, body: dict, bg: BackgroundTasks, user=Depends(require_user)):
    db=SessionLocal(); t=db.query(Task).filter_by(id=id, owner_id=user).first()
    if not t: raise HTTPException(404)
    token=body.get("approval_token")
    if not token or not verify_approval(token, id, t.pending_hash):
        db.close(); raise HTTPException(403, detail="Invalid or stale approval")
    t.approval_granted=True; t.status="executing"; t.pending_hash=None; db.commit(); db.close()
    bg.add_task(run_task, id)
    return {"ok": True}

@app.get("/api/tasks/{id}/approval_token")
def get_approval_token(id: int, user=Depends(require_user)):
    db=SessionLocal(); t=db.query(Task).filter_by(id=id, owner_id=user).first()
    if not t or not t.pending_hash: raise HTTPException(404)
    token=sign_approval(id, t.pending_hash); db.close(); return {"approval_token": token}

@app.get("/api/tasks/{id}/stream")
async def stream(id: int, token: str = None, user=Depends(require_user)):
    async def gen():
        last=0
        for _ in range(600):
            db=SessionLocal()
            evs=db.query(Event).filter(Event.task_id==id, Event.id>last).order_by(Event.id).all()
            for e in evs:
                yield f"data: {json.dumps({'tool':e.tool,'status':e.status,'duration_ms':e.duration_ms,'retry':e.retry})}\n\n"
                last=e.id
            t=db.query(Task).filter_by(id=id, owner_id=user).first()
            db.close()
            if t and t.status in ("completed","failed","cancelled","awaiting_approval","awaiting_clarification"):
                yield f"data: {json.dumps({'status':t.status,'memory':t.memory})}\n\n"
                if t.status in ("completed","failed","cancelled"): break
            await asyncio.sleep(0.5)
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache"})

@app.get("/api/review_queue")
def review_queue(user=Depends(require_user)):
    db=SessionLocal(); tasks=db.query(Task).filter_by(owner_id=user, status="awaiting_clarification").all(); db.close()
    return [{"id":t.id,"goal":t.goal,"memory":t.memory} for t in tasks]

@app.post("/api/tasks/{id}/clarify")
def clarify(id: int, body: dict, bg: BackgroundTasks, user=Depends(require_user)):
    db=SessionLocal(); t=db.query(Task).filter_by(id=id, owner_id=user).first()
    if not t: 
        db.close()
        raise HTTPException(404)
    # Validate clarification inputs - do not auto-trust
    allowed = {"invoice_number","amount","currency","due_date","company"}
    clean = {k:v for k,v in body.items() if k in allowed}
    if not clean:
        db.close()
        raise HTTPException(400, detail="No valid fields")
    t.memory={**t.memory, **clean, "confidence":1.0, "clarified": True}
    t.status="executing"
    db.commit()
    db.close()
    bg.add_task(run_task, id)
    return {"ok": True}

@app.get("/api/finance/records")
def list_records(q: str="", user=Depends(require_user)):
    db=SessionLocal()
    query = db.query(FinanceRecord).filter_by(owner_id=user)
    if q:
        query = query.filter((FinanceRecord.invoice_number.ilike(f"%{q}%")) | (FinanceRecord.company.ilike(f"%{q}%")))
    recs = query.all()
    db.close()
    return [{"id":x.id,"invoice_number":x.invoice_number,"company":x.company,"amount":x.amount,"currency":x.currency,"due_date":x.due_date,"source_file":x.source_file} for x in recs]

@app.post("/api/tasks/{id}/cancel")
def cancel_task(id: int, user=Depends(require_user)):
    db=SessionLocal()
    t=db.query(Task).filter_by(id=id, owner_id=user).first()
    if not t:
        db.close()
        raise HTTPException(404)
    if t.status in ("completed","failed"):
        db.close()
        raise HTTPException(400, detail="Cannot cancel terminal task")
    t.status="cancelled"
    db.commit()
    db.close()
    return {"ok": True}

@app.on_event("startup")
async def resume():
    db=SessionLocal()
    for t in db.query(Task).filter(Task.status.in_(["pending","executing"])).all():
        asyncio.create_task(run_task(t.id))
    db.close()

@app.get("/health")
def health(): return {"ok": True}
