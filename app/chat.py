"""Chat module with RAG integration using Gemini API."""

from google import genai
from google.genai import types

from app.config import settings
from app.vectorstore import vector_store

SYSTEM_PROMPT = """\
あなたは株式会社ソフィアのAIアシスタントです。
お客様からのお問い合わせに丁寧かつ正確にお答えします。

以下のルールに従ってください：
- 提供されたナレッジ情報に基づいて回答してください
- ナレッジに該当する情報がない場合は、「申し訳ございませんが、その件についての情報は現在持ち合わせておりません。お手数ですが、直接お問い合わせください。」と回答してください
- 回答は簡潔かつ分かりやすく、丁寧な日本語で行ってください
- 推測や不確かな情報は提供しないでください
"""


def generate_response(user_message: str) -> str:
    """Generate a response using RAG."""
    relevant_docs = vector_store.search(user_message)

    context = ""
    if relevant_docs:
        context_parts = []
        for doc in relevant_docs:
            source_info = f"（出典: {doc['source']}）" if doc["source"] else ""
            context_parts.append(f"{doc['text']}{source_info}")
        context = "\n\n".join(context_parts)

    system_instruction = SYSTEM_PROMPT
    if context:
        system_instruction += f"\n\n以下はお客様の質問に関連するナレッジ情報です：\n\n{context}"

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.chat_model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    return response.text
