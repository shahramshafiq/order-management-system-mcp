# Build Notes

Running log of design decisions and why they were made, same purpose as Ledger's
`docs/NOTES.md`: a record for explaining choices to the supervisor later, not just a diary.

## 2026-09-28 — Project start

- Read the assignment doc in full. 6 required tools, business rules around stock
  reservations, idempotency, atomicity, Decimal money, and audit movement records.
- Decided to keep the same shape as the MCP Task Assistant project: FastAPI host process
  launches the MCP server as a stdio subprocess, one client session for the app's lifetime,
  a bounded tool-calling loop against OpenAI, plus a chat frontend.
- New this project: NeMo Guardrails wraps both the incoming user message (input rail) and
  the assistant's reply (output rail), specifically to block jailbreak/prompt-injection
  attempts, since the supervisor was actively probing the previous project's chat UI for
  exactly this kind of weakness.
- Storage is plain JSON files per entity (products, orders, suppliers, movements,
  idempotency keys), no database, matching the previous project's `tasks.json` pattern.
- Suppliers are seed/reference data (`data/suppliers.json`), not one of the 6 tools.
