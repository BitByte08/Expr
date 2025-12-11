import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
BASE_URL_TEMPLATE = "https://{region}.api.riotgames.com"

HEADERS = {"X-Riot-Token": RIOT_API_KEY}

async def get_request(endpoint: str, region: str = "kr"):
    """
    Riot API 호출 유틸 (비동기화)
    :param endpoint: 호출할 엔드포인트
    :param region: Riot API 지역
    :return: JSON 응답
    """
    url = f"{BASE_URL_TEMPLATE.format(region=region)}{endpoint}"
    print(f"[DEBUG] Async Request URL: {url}")

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()
