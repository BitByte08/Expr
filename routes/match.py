from typing import List

from fastapi import APIRouter

from models.match import MatchDto
from utils.riot.match import get_match_ids_by_puuid, get_match_detail_by_match_id

router = APIRouter()

@router.get("/{puuid}", response_model=List[str])
def get_match(puuid: str):
    return get_match_ids_by_puuid(puuid)
@router.get("/detail/{match_id}", response_model=MatchDto)
def get_match_detail(match_id: str):
    return get_match_detail_by_match_id(match_id)