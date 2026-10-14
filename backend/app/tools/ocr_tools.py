import os
try:
    import fitz, pytesseract
    from PIL import Image
except: fitz=None
CONFIDENCE_THRESHOLD=0.8

def extract_with_ocr_fallback(path: str, text: str):
    if text.strip() and len(text.split())>10:
        return text, 0.95, False
    if not fitz: return text, 0.6, False
    try:
        doc=fitz.open(path)
        pix=doc[0].get_pixmap(dpi=300)
        img=Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ocr_text=pytesseract.image_to_string(img)
        from app.tools.invoice_tools import extract_invoice_fields
        fields=extract_invoice_fields(ocr_text)
        conf=fields["confidence"]*0.9
        return ocr_text, conf, True
    except Exception as e:
        return text, 0.6, False

def needs_review(confidence: float) -> bool:
    return confidence < CONFIDENCE_THRESHOLD
