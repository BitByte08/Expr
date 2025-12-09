from utils.riot.base import get_request
from models.league import LeagueEntryDTO

def get_league_entry_by_puuid(puuid: str):
    endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
    return LeagueEntryDTO(**get_request(endpoint))