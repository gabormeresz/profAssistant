Run Frontend:
cd frontend && npm run dev

Run backend:
cd backend && uv run uvicorn main:app --reload --port 8000

Run wiki mcp server
cd backend && uv run wikipedia-mcp --transport sse --port 8765 --enable-cache
