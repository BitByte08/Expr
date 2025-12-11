from models.account import AccountDTO
from utils.riot.base import get_request

async def get_account_by_riot_id(game_name: str, tag_line: str):
    endpoint = f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    return AccountDTO(**await get_request(endpoint, "asia"))

async def get_account_by_puuid(puuid: str):
    endpoint = f"/riot/account/v1/accounts/by-puuid/{puuid}"
    return AccountDTO(**await get_request(endpoint, "asia"))