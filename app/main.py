"""Main FastAPI application."""

import os

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.chat import generate_response
from app.config import settings
from app.vectorstore import vector_store

app = FastAPI(title=settings.app_title)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# --- Page Routes ---


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("admin.html", {"request": request})


# --- Chat API ---


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="メッセージを入力してください")
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini APIキーが設定されていません")
    response_text = generate_response(req.message)
    return ChatResponse(response=response_text)


# --- FAQ API (Supabase) ---


class FAQItem(BaseModel):
    question: str
    answer: str


def _get_supabase():
    return vector_store.supabase


@app.get("/api/faq")
def get_faq() -> list[dict]:
    result = _get_supabase().table("faq").select("*").order("id").execute()
    return [{"id": r["id"], "question": r["question"], "answer": r["answer"]} for r in (result.data or [])]


@app.post("/api/faq")
def add_faq(item: FAQItem) -> dict:
    _get_supabase().table("faq").insert(
        {"question": item.question, "answer": item.answer}
    ).execute()
    count_result = _get_supabase().table("faq").select("id", count="exact").execute()
    return {"status": "ok", "count": count_result.count or 0}


@app.delete("/api/faq/{faq_id}")
def delete_faq(faq_id: int) -> dict:
    _get_supabase().table("faq").delete().eq("id", faq_id).execute()
    count_result = _get_supabase().table("faq").select("id", count="exact").execute()
    return {"status": "ok", "count": count_result.count or 0}


# --- Knowledge API ---


class KnowledgeText(BaseModel):
    title: str
    content: str


@app.post("/api/knowledge/text")
def add_knowledge_text(item: KnowledgeText) -> dict:
    vector_store.add_document(item.content, source=item.title)
    return {"status": "ok", "chunks": vector_store.document_count}


@app.post("/api/knowledge/file")
async def add_knowledge_file(file: UploadFile) -> dict:
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="テキストファイル(.txt)のみ対応しています")
    content = await file.read()
    text = content.decode("utf-8")
    vector_store.add_document(text, source=file.filename)
    return {"status": "ok", "chunks": vector_store.document_count}


@app.get("/api/knowledge/status")
def knowledge_status() -> dict:
    return {"document_count": vector_store.document_count}


@app.delete("/api/knowledge")
def clear_knowledge() -> dict:
    vector_store.clear()
    return {"status": "ok"}
