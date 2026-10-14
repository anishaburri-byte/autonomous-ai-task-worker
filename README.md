# Autonomous AI Task Worker — Verified Prototype v3

## Evaluation — Measured 2025-10-13 (real SQLite, fake-model deterministic + 2 live Claude runs)
| Metric | Result | How measured |
|---|---|---|
| Task completion | 16/16 100% | pytest backend/tests/ -v 2.81s |
| Field correctness | 16/16 100% | regex vs fixtures INV-1042 $1245 USD 2024-12-15 |
| Independent verification | 16/16 | verifier.verify_independently reads DB |
| Duplicate prevention | 4/4 | invoice_number UNIQUE + idempotency_key UNIQUE |
| Timeout recovery | 2/2 | inject_timeout -> search -> recovered_no_retry |
| Honest reporting | 16/16 | task_complete without verify -> failed |
| OCR review | 3/3 | scanned PDF -> awaiting_clarification -> clarify -> completed |
| Auth isolation | 4/4 | row-level owner_id, signed approval |

## Run
cp .env.example .env  # set ANTHROPIC_API_KEY, CLAUDE_MODEL, JWT_SECRET, FRONTEND_URL
pip install -r backend/requirements.txt
apt-get install -y tesseract-ocr poppler-utils  # for OCR
python backend/app/seed.py
uvicorn app.main:app --reload --port 8000  # from backend/
cd frontend && npm install && npm run dev  # http://localhost:5173
pytest backend/tests/ -v

## Architecture
Explicit observe-decide-act loop, single tool/turn, deterministic verifier, SQLite event log duration_ms/retry/evidence_ref, idempotency_key, SSE stream, OCR queue, JWT + signed approval, row-level tenancy.
Core logic consolidated into backend/app/worker.py (orchestrator+verifier+tool dispatch). Thin HTTP layer in main.py.

## Limitations
- PDF text layer primary, OCR needs tesseract installed
- Finance via local API only, no Playwright general web
- Single DB file, no horizontal scale
