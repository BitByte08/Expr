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
from utils.docs.champion_kor_to_en import champion_kor_to_en

logger = logging.getLogger(__name__)
router = APIRouter()


class RagRequest(BaseModel):
    champion: str
    question: str
    n_results: Optional[int] = 3
    force_refresh: Optional[bool] = False


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
# Main RAG Route (Gemini 제거)
# ------------------------
@router.post("")
def rag(req: RagRequest):
    champion = req.champion

    # 한글 챔프이면 영어로 변환
    if champion in champion_kor_to_en:
        champion = champion_kor_to_en[champion]

    question = req.question
    n = req.n_results

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
        dd = fetch_champion_ddragon(champion)
        if dd:
            new_data["ddragon"] = dd
    except Exception as e:
        logger.warning(f"ddragon fetch error: {e}")

    # FOW
    try:
        fow = crawl_fow(champion.lower())
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
            {"auto_sync": json.dumps(new_data, ensure_ascii=False, indent=2)},
            "auto_sync"
        )
        docs.append(new_data)

    # ----------------------------
    # 4) 요약 제거 → 원본 docs만 반환
    # ----------------------------
    return {
        "source": "vector+auto_sync",
        "documents": docs
    }
