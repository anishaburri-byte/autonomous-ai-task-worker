TOOL_SCHEMAS=[
 {"name":"search_invoice_files","description":"Search local invoices by company name","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
 {"name":"read_invoice_file","description":"Read invoice file text","input_schema":{"type":"object","properties":{"filename":{"type":"string"}},"required":["filename"]}},
 {"name":"extract_invoice_fields","description":"Extract invoice_number, amount, currency, due_date with confidence","input_schema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}},
 {"name":"search_finance_records","description":"Search persisted finance DB","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
 {"name":"create_finance_record","description":"Create record idempotent via idempotency_key","input_schema":{"type":"object","properties":{"invoice_number":{"type":"string"},"company":{"type":"string"},"amount":{"type":"number"},"currency":{"type":"string"},"due_date":{"type":"string"},"idempotency_key":{"type":"string"},"source_file":{"type":"string"}},"required":["invoice_number","company","amount","currency","due_date","idempotency_key"]}},
 {"name":"verify_finance_record","description":"Verify persisted record matches expected","input_schema":{"type":"object","properties":{"invoice_number":{"type":"string"},"expected":{"type":"object"}},"required":["invoice_number","expected"]}},
 {"name":"request_user_approval","description":"Request approval for financial write","input_schema":{"type":"object","properties":{"reason":{"type":"string"},"payload":{"type":"object"}},"required":["reason","payload"]}},
 {"name":"task_complete","description":"Mark task done, will be independently verified","input_schema":{"type":"object","properties":{"summary":{"type":"string"}},"required":["summary"]}},
]
