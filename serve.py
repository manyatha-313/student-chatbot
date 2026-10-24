"""HTTP backend for the campus_assistant_frontend.html webpage.

Endpoints:
  POST /ask   {"question": "..."}
              -> {"answer": "...",
                  "sources": [{"doc","page","section","score","text"}, ...]}
  GET  /      serves campus_assistant_frontend.html (when present in the repo root)

The webpage calls /ask with fetch and renders `answer` plus `sources`.

Run:  python serve.py        (http://localhost:8000)
FastAPI/uvicorn ship with gradio, so there is no extra dependency.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import rag

FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus_assistant_frontend.html")

app = FastAPI(title="Campus Regulations Assistant")
# Permissive CORS so the page works whether it is served from here or opened directly.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

index = rag.build_from_dataset()  # built once at startup


class Ask(BaseModel):
    question: str


@app.post("/ask")
def ask(body: Ask):
    reply, found = index.answer(body.question)
    sources = [{"doc": c["doc"], "page": c["page"], "section": c.get("section", ""),
                "score": round(c["score"], 3), "text": c["text"]} for c in found]
    return {"answer": reply, "sources": sources}


@app.get("/")
def home():
    if os.path.exists(FRONTEND):
        return FileResponse(FRONTEND)
    return HTMLResponse("<p>Add <code>campus_assistant_frontend.html</code> to the repo root "
                        "and it will be served here. The API is live at <code>POST /ask</code>.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
