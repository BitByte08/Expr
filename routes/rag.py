import os
import logging
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from collections import Counter

from utils.docs.store import store_champion_data, search_champion
from utils.docs.ddragon import fetch_champion_ddragon
from utils.docs.fow import crawl_fow

logger = logging.getLogger(__name__)
router = APIRouter()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)

class RagRequest(BaseModel):
    champion: str
    question: str
    n_results: Optional[int] = 3
    force_refresh: Optional[bool] = False

# ------------------------
# Gemini 요약
# ------------------------
def _summarize_with_gemini(texts: List[str], question: str) -> str:
    if not GEMINI_KEY:
        return "\n\n---\n\n".join(texts)

    max_docs = 5
    docs = texts[:max_docs]

    prompt = f"""아래 문서들을 참고해서 질문에 한국어로 정확하게 답해주세요.

[질문]
{question}

[문서들]
"""
    for i, t in enumerate(docs):
        if isinstance(t, dict):
            t = json.dumps(t, ensure_ascii=False)
        prompt += f"\n\n[문서 {i+1}]\n{t}\n"

    prompt += "\n\n위 문서들의 정보를 기반으로 간결하고 정확하게 답변하세요."

    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"))
        response = model.generate_content(prompt)
        if hasattr(response, "text"):
            return response.text.strip()
        if hasattr(response, "candidates") and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            return "".join([p.text for p in parts]).strip()
        return str(response).strip()
    except Exception as e:
        logger.error(f"Gemini summarization error: {e}")
        return "\n\n---\n\n".join([json.dumps(d, ensure_ascii=False) if isinstance(d, dict) else d for d in docs])

# ------------------------
# skill_order 빈도 기반 정리
# ------------------------
def reorder_skill_order(skills: List[str]) -> List[str]:
    filtered = [s for s in skills if s != 'R']
    count = Counter(filtered)
    sorted_skills = [skill for skill, _ in count.most_common()]
    # 누락된 스킬(Q/W/E) 추가
    for s in ['Q','W','E']:
        if s not in sorted_skills:
            sorted_skills.append(s)
    return sorted_skills

# ------------------------
# Main RAG Route
# ------------------------
@router.post("")
def rag(req: RagRequest):
    champion = req.champion
    question = req.question
    n = req.n_results

    # ----------------------------
    # 1) 기존 Vector Search
    # ----------------------------
    search_res = search_champion(champion, question, n_results=n)
    try:
        docs = search_res.get("documents", [[]])[0]
    except:
        docs = []

    # ----------------------------
    # 2) 자동 동기화: DDragon + FOW
    # ----------------------------
    new_data = {}

    # DDragon
    try:
        dd = fetch_champion_ddragon(champion.capitalize())
        if dd:
            new_data["ddragon"] = dd
    except Exception as e:
        logger.warning(f"ddragon fetch error: {e}")

    # FOW
    try:
        fow = crawl_fow(champion.lower())
        # skill_order 후처리
        if fow.get("skill_order"):
            fow["skill_order"] = reorder_skill_order(fow["skill_order"])
        print("=== fow 크롤링 결과 ===")
        print(fow)
        if fow:
            new_data["FOW"] = fow
    except Exception as e:
        logger.warning(f"fow fetch error: {e}")

    # ----------------------------
    # 3) DB 업데이트 (JSON 문자열로 저장)
    # ----------------------------
    if new_data:
        store_champion_data(
            champion,
            {"auto_sync": json.dumps(new_data, ensure_ascii=False, indent=2)},  # 문자열 저장
            "auto_sync"
        )
        # docs에도 포함
        docs.append(new_data)

    # ----------------------------
    # 4) Gemini 요약
    # ----------------------------
    summary = _summarize_with_gemini(docs, question)

    return {
        "source": "vector+auto_sync",
        "documents": docs,
        "answer": summary
    }
