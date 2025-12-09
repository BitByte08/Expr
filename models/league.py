from pydantic import BaseModel
from typing import Optional

class MiniSeriesDTO(BaseModel):
    losses: int
    progress: str
    target: int
    wins: int

class LeagueEntryDTO(BaseModel):
    leagueId: str
    puuid: str
    queueType: str
    tier: str
    rank: str
    leaguePoints: int
    wins: int
    losses: int
    hotStreak: bool
    veteran: bool
    freshBlood: bool
    inactive: bool
    miniSeries: Optional[MiniSeriesDTO] = None
