# utils/riot/match.py
import asyncio
from utils.riot.base import get_request
from models.match import MatchDto

# 한 번에 5개만 병렬 호출 (Riot rate limit safe)
SEMAPHORE = asyncio.Semaphore(5)


async def get_match_ids_by_puuid(puuid: str):
    endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return await get_request(endpoint, "asia")


async def get_match_detail_by_match_id(match_id: str):
    endpoint = f"/lol/match/v5/matches/{match_id}"
    data = await get_request(endpoint, "asia")
    return MatchDto(**data)


async def limited_match_detail(match_id: str):
    """Semaphore로 동시 호출량 제한"""
    async with SEMAPHORE:
        return await get_match_detail_by_match_id(match_id)
