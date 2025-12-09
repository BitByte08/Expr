from fastapi import APIRouter
from utils.riot.league import get_league_entry_by_puuid
from models.league import LeagueEntryDTO
router = APIRouter()

@router.get("/{puuid}", response_model=LeagueEntryDTO)
def get_account(puuid: str):
    return get_league_entry_by_puuid(puuid)