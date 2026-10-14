from app.tools.ocr_tools import needs_review

def test_confidence_gate():
    assert needs_review(0.6)==True
    assert needs_review(0.95)==False
    assert needs_review(0.79)==True
    assert needs_review(0.81)==False
