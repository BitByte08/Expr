from typing import List, Optional
from pydantic import BaseModel


class ObjectiveDto(BaseModel):
    first: Optional[bool] = None
    kills: Optional[int] = None

    class Config:
        extra = "allow"


class ObjectivesDto(BaseModel):
    baron: Optional[ObjectiveDto] = None
    champion: Optional[ObjectiveDto] = None
    dragon: Optional[ObjectiveDto] = None
    horde: Optional[ObjectiveDto] = None
    inhibitor: Optional[ObjectiveDto] = None
    riftHerald: Optional[ObjectiveDto] = None
    tower: Optional[ObjectiveDto] = None

    class Config:
        extra = "allow"


class BanDto(BaseModel):
    championId: Optional[int] = None
    pickTurn: Optional[int] = None

    class Config:
        extra = "allow"


class TeamDto(BaseModel):
    bans: Optional[List[BanDto]] = None
    objectives: Optional[ObjectivesDto] = None
    teamId: Optional[int] = None
    win: Optional[bool] = None

    class Config:
        extra = "allow"


class PerkStyleSelectionDto(BaseModel):
    perk: Optional[int] = None
    var1: Optional[int] = None
    var2: Optional[int] = None
    var3: Optional[int] = None

    class Config:
        extra = "allow"


class PerkStyleDto(BaseModel):
    description: Optional[str] = None
    selections: Optional[List[PerkStyleSelectionDto]] = None
    style: Optional[int] = None

    class Config:
        extra = "allow"


class PerkStatsDto(BaseModel):
    defense: Optional[int] = None
    flex: Optional[int] = None
    offense: Optional[int] = None

    class Config:
        extra = "allow"


class PerksDto(BaseModel):
    statPerks: Optional[PerkStatsDto] = None
    styles: Optional[List[PerkStyleDto]] = None

    class Config:
        extra = "allow"


class ChallengesDto(BaseModel):
    class Config:
        extra = "allow"


class MissionsDto(BaseModel):
    class Config:
        extra = "allow"


class ParticipantDto(BaseModel):
    allInPings: Optional[int] = None
    assistMePings: Optional[int] = None
    assists: Optional[int] = None
    baronKills: Optional[int] = None
    bountyLevel: Optional[int] = None
    champExperience: Optional[int] = None
    champLevel: Optional[int] = None
    championId: Optional[int] = None
    championName: Optional[str] = None
    commandPings: Optional[int] = None
    consumablesPurchased: Optional[int] = None
    challenges: Optional[ChallengesDto] = None
    damageDealtToBuildings: Optional[int] = None
    damageDealtToObjectives: Optional[int] = None
    damageDealtToTurrets: Optional[int] = None
    damageSelfMitigated: Optional[int] = None
    deaths: Optional[int] = None
    detectorWardsPlaced: Optional[int] = None
    doubleKills: Optional[int] = None
    dragonKills: Optional[int] = None
    eligibleForProgression: Optional[bool] = None
    enemyMissingPings: Optional[int] = None
    enemyVisionPings: Optional[int] = None
    firstBloodAssist: Optional[bool] = None
    firstBloodKill: Optional[bool] = None
    firstTowerAssist: Optional[bool] = None
    firstTowerKill: Optional[bool] = None
    gameEndedInEarlySurrender: Optional[bool] = None
    gameEndedInSurrender: Optional[bool] = None
    goldEarned: Optional[int] = None
    goldSpent: Optional[int] = None
    individualPosition: Optional[str] = None
    kills: Optional[int] = None
    largestCriticalStrike: Optional[int] = None
    largestKillingSpree: Optional[int] = None
    largestMultiKill: Optional[int] = None
    longestTimeSpentLiving: Optional[int] = None
    magicDamageDealt: Optional[int] = None
    magicDamageDealtToChampions: Optional[int] = None
    magicDamageTaken: Optional[int] = None
    neutralMinionsKilled: Optional[int] = None
    nexusKills: Optional[int] = None
    nexusTakedowns: Optional[int] = None
    nexusLost: Optional[int] = None
    objectivesStolen: Optional[int] = None
    objectivesStolenAssists: Optional[int] = None
    participantId: Optional[int] = None
    perks: Optional[PerksDto] = None
    physicalDamageDealt: Optional[int] = None
    physicalDamageDealtToChampions: Optional[int] = None
    physicalDamageTaken: Optional[int] = None
    profileIcon: Optional[int] = None
    puuid: Optional[str] = None
    quadraKills: Optional[int] = None
    riotIdGameName: Optional[str] = None
    riotIdTagline: Optional[str] = None
    role: Optional[str] = None
    sightWardsBoughtInGame: Optional[int] = None
    spell1Casts: Optional[int] = None
    spell2Casts: Optional[int] = None
    spell3Casts: Optional[int] = None
    spell4Casts: Optional[int] = None
    summoner1Casts: Optional[int] = None
    summoner1Id: Optional[int] = None
    summoner2Casts: Optional[int] = None
    summoner2Id: Optional[int] = None
    summonerId: Optional[str] = None
    summonerLevel: Optional[int] = None
    summonerName: Optional[str] = None
    teamId: Optional[int] = None
    teamPosition: Optional[str] = None
    timeCCingOthers: Optional[int] = None
    timePlayed: Optional[int] = None
    totalDamageDealt: Optional[int] = None
    totalDamageDealtToChampions: Optional[int] = None
    totalDamageShieldedOnTeammates: Optional[int] = None
    totalDamageTaken: Optional[int] = None
    totalHeal: Optional[int] = None
    totalHealsOnTeammates: Optional[int] = None
    totalMinionsKilled: Optional[int] = None
    totalTimeCCDealt: Optional[int] = None
    totalUnitsHealed: Optional[int] = None
    tripleKills: Optional[int] = None
    trueDamageDealt: Optional[int] = None
    trueDamageDealtToChampions: Optional[int] = None
    trueDamageTaken: Optional[int] = None
    turretKills: Optional[int] = None
    turretTakedowns: Optional[int] = None
    turretsLost: Optional[int] = None
    unrealKills: Optional[int] = None
    visionScore: Optional[int] = None
    wardsKilled: Optional[int] = None
    wardsPlaced: Optional[int] = None
    win: Optional[bool] = None

    class Config:
        extra = "allow"


class InfoDto(BaseModel):
    gameCreation: Optional[int] = None
    gameDuration: Optional[int] = None
    gameEndTimestamp: Optional[int] = None
    gameId: Optional[int] = None
    gameMode: Optional[str] = None
    gameName: Optional[str] = None
    gameStartTimestamp: Optional[int] = None
    gameType: Optional[str] = None
    gameVersion: Optional[str] = None
    mapId: Optional[int] = None
    participants: Optional[List[ParticipantDto]] = None
    platformId: Optional[str] = None
    queueId: Optional[int] = None
    teams: Optional[List[TeamDto]] = None
    tournamentCode: Optional[str] = None

    class Config:
        extra = "allow"


class MetadataDto(BaseModel):
    dataVersion: Optional[str] = None
    matchId: Optional[str] = None
    participants: Optional[List[str]] = None

    class Config:
        extra = "allow"


class MatchDto(BaseModel):
    metadata: Optional[MetadataDto] = None
    info: Optional[InfoDto] = None

    class Config:
        extra = "allow"
