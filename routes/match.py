# routes/match.py
from typing import List
import asyncio
from fastapi import APIRouter

from pydantic import BaseModel
from models.match import MatchDto
from utils.riot.account import get_account_by_riot_id
from utils.riot.match import (
    get_match_ids_by_puuid,
    limited_match_detail,
)

router = APIRouter()


class SlimParticipantDto(BaseModel):
    summonerName: str | None = None
    teamPosition: str | None = None
    championName: str | None = None
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    cs: int | None = None
    win: bool | None = None


class SlimInfoDto(BaseModel):
    queueId: int | None = None
    gameMode: str | None = None
    participants: List[SlimParticipantDto]


class SlimMatchDto(BaseModel):
    metadata: dict | None = None
    info: SlimInfoDto


# LLM 토큰 과다를 막기 위해 필요한 필드만 남기는 슬라이싱
def _slim_participant(p: dict) -> SlimParticipantDto:
    name = p.get("summonerName") or p.get("riotIdGameName") or None
    return SlimParticipantDto(
        summonerName=name,
        teamPosition=p.get("teamPosition"),
        championName=p.get("championName"),
        kills=p.get("kills"),
        deaths=p.get("deaths"),
        assists=p.get("assists"),
        cs=p.get("totalMinionsKilled"),
        win=p.get("win"),
    )


def _slim_team(t: dict) -> dict:
    if not t:
        return {}
    return {
        "teamId": t.get("teamId"),
        "win": t.get("win"),
    }


def _pick_me(info: dict, puuid: str | None = None, game_name: str | None = None, tag_line: str | None = None) -> dict | None:
    if not info:
        return None

    participants = info.get("participants", []) or []
    game_norm = game_name.strip().lower() if game_name else None
    tag_norm = tag_line.strip().lower() if tag_line else None
    for p in participants:
        if puuid and p.get("puuid") == puuid:
            return p
    for p in participants:
        if game_norm and tag_norm:
            pname = (p.get("riotIdGameName") or p.get("summonerName") or "").strip().lower()
            ptag = (p.get("riotIdTagline") or "").strip().lower()
            if pname == game_norm and ptag == tag_norm:
                return p
    return None


def _slim_match(match: MatchDto, puuid: str | None = None, game_name: str | None = None, tag_line: str | None = None) -> SlimMatchDto:
    data = match.dict(exclude_none=True)
    info = data.get("info", {})

    me_raw = _pick_me(info, puuid, game_name, tag_line)
    me = _slim_participant(me_raw) if me_raw else None

    slim_info = SlimInfoDto(
        queueId=info.get("queueId"),
        gameMode=info.get("gameMode"),
        participants=[me] if me else [_slim_participant(p) for p in info.get("participants", [])[:1] if p],
    )

    return SlimMatchDto(
        metadata=None,
        info=slim_info,
    )


@router.get(
    "/detail/all/{game_name}/{tag_line}",
    response_model=List[SlimMatchDto],
    response_model_exclude_none=True,
)
async def get_match_detail_all(game_name: str, tag_line: str, limit: int = 10):
    """
    - 비동기 병렬 처리
    - rate limit 방지 (Semaphore)
    - 최근 limit개만
    """
    account = await get_account_by_riot_id(game_name, tag_line)
    match_ids = await get_match_ids_by_puuid(account.puuid)

    # 최근 N개만 사용 (상한 3개로 제한하여 응답 속도 확보)
    safe_limit = max(1, min(limit, 3))
    match_ids = match_ids[:safe_limit]

    tasks = [limited_match_detail(mid) for mid in match_ids]
    match_details = await asyncio.gather(*tasks)

    # 필요 필드만 남긴 슬림 버전 반환
    return [_slim_match(m, puuid=account.puuid, game_name=game_name, tag_line=tag_line) for m in match_details]
