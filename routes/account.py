from fastapi import APIRouter
from utils.riot.account import get_account_by_riot_id, get_account_by_puuid
from models.account import AccountDTO
router = APIRouter()

@router.get("/{game_name}/{tag_line}", response_model=AccountDTO)
async def get_account_riot_id(game_name: str, tag_line: str):
    return await get_account_by_riot_id(game_name, tag_line)
@router.get("/{puuid}", response_model=AccountDTO)
async def get_account_puuid(puuid: str):
    return await get_account_by_puuid(puuid)