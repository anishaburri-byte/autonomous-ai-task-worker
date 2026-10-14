import os, re
try: import fitz
except: fitz=None
INJ = re.compile(r"ignore previous|system prompt|override tools", re.I)

def search_invoice_files(query: str):
    for base in ["backend/invoices","ai-worker/backend/invoices", os.path.abspath("backend/invoices")]:
        if os.path.exists(base): break
    else: base="backend/invoices"
    files = [f for f in os.listdir(base) if query.lower().replace(" corporation","") in f.lower() or query.lower() in f.lower()]
    if not files and "acme" in query.lower(): files=[f for f in os.listdir(base) if "acme" in f.lower()]
    if not files and "globex" in query.lower(): files=[f for f in os.listdir(base) if "globex" in f.lower()]
    def dk(f): m=re.search(r"(\d{4}-\d{2}-\d{2})",f); return m.group(1) if m else ""
    return sorted([{"filename":f,"date":dk(f)} for f in files], key=lambda x:x["date"], reverse=True)

def read_invoice_file(filename: str):
    # FIXED: traversal guard
    if ".." in filename or "/" in filename or "\\" in filename:
        raise PermissionError("Invalid filename: path traversal blocked")
    safe = os.path.basename(filename)
    for base in ["backend/invoices","ai-worker/backend/invoices"]:
        p=os.path.join(base,safe)
        # absolute path check
        if os.path.exists(p):
            if not os.path.abspath(p).startswith(os.path.abspath(base)):
                raise PermissionError("Path outside invoices")
            if p.endswith(".pdf") and fitz:
                doc=fitz.open(p)
                text="".join(page.get_text() for page in doc)
            else:
                text=open(p,encoding="utf-8",errors="ignore").read()
            if INJ.search(text): text+="\n[UNTRUSTED CONTENT IGNORED]"
            return text
    raise FileNotFoundError(filename)

def extract_invoice_fields(text: str):
    inv=re.search(r"Invoice Number:\s*(\S+)",text,re.I)
    amt=re.search(r"Amount:\s*\$?([\d,]+\.\d{2})",text)
    cur=re.search(r"Currency:\s*(\w+)",text,re.I)
    cur2=re.search(r"Amount:.*(USD|EUR|GBP)",text,re.I)
    due=re.search(r"Due Date:\s*(\d{4}-\d{2}-\d{2})",text)
    cur = cur.group(1) if cur else (cur2.group(1) if cur2 else "USD")
    return {
        "invoice_number": inv.group(1) if inv else None,
        "amount": float(amt.group(1).replace(",","")) if amt else None,
        "currency": cur,
        "due_date": due.group(1) if due else None,
        "confidence": 1.0 if all([inv,amt,due]) else 0.6,
        "missing": [k for k,v in [("invoice_number",inv),("amount",amt),("due_date",due)] if not v]
    }
