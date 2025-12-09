import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
BASE_URL_TEMPLATE = "https://{region}.api.riotgames.com"

HEADERS = {"X-Riot-Token": RIOT_API_KEY}

def get_request(endpoint: str, region: str = "kr"):
    """
    Riot API 호출 유틸
    :param endpoint: 호출할 엔드포인트, 예: "summoner/v4/summoners/by-name/username"
    :param region: Riot API 서버 지역, 기본값 "kr"
    :return: JSON 응답
    """
    url = f"{BASE_URL_TEMPLATE.format(region=region)}/{endpoint}"
    print(f"[DEBUG] Request URL: {url}")
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
