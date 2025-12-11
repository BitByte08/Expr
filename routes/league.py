from fastapi import APIRouter
from typing import List
from utils.riot.league import get_league_entry_by_puuid
from utils.riot.account import get_account_by_riot_id
from models.league import LeagueEntryDTO
router = APIRouter()

@router.get("/{game_name}/{tag_line}", response_model=List[LeagueEntryDTO])
async def get_league_by_riot_id(game_name: str, tag_line: str):
    account = await get_account_by_riot_id(game_name, tag_line)
    return await get_league_entry_by_puuid(account.puuid)