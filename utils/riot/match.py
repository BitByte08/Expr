from models.match import MatchDto
from utils.riot.base import get_request

def get_match_ids_by_puuid(puuid: str):
    endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return get_request(endpoint, "asia")

def get_match_detail_by_match_id(match_id: str):
    endpoint = f"/lol/match/v5/matches/{match_id}"
    return MatchDto(**get_request(endpoint, "asia"))