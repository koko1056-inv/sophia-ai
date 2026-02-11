"""Main FastAPI application."""

import json
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


@app.on_event("startup")
def startup() -> None:
    vector_store.load()


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
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI APIキーが設定されていません")
    response_text = generate_response(req.message)
    return ChatResponse(response=response_text)


# --- FAQ API ---


class FAQItem(BaseModel):
    question: str
    answer: str


@app.get("/api/faq")
def get_faq() -> list[dict]:
    if os.path.exists(settings.faq_path):
        with open(settings.faq_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.post("/api/faq")
def add_faq(item: FAQItem) -> dict:
    faq_list = []
    if os.path.exists(settings.faq_path):
        with open(settings.faq_path, "r", encoding="utf-8") as f:
            faq_list = json.load(f)
    faq_list.append({"question": item.question, "answer": item.answer})
    with open(settings.faq_path, "w", encoding="utf-8") as f:
        json.dump(faq_list, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "count": len(faq_list)}


@app.delete("/api/faq/{index}")
def delete_faq(index: int) -> dict:
    if not os.path.exists(settings.faq_path):
        raise HTTPException(status_code=404, detail="FAQが見つかりません")
    with open(settings.faq_path, "r", encoding="utf-8") as f:
        faq_list = json.load(f)
    if index < 0 or index >= len(faq_list):
        raise HTTPException(status_code=404, detail="FAQが見つかりません")
    faq_list.pop(index)
    with open(settings.faq_path, "w", encoding="utf-8") as f:
        json.dump(faq_list, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "count": len(faq_list)}


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
