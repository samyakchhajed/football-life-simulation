import uuid
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class AwardWinner(BaseModel):
    award_id: str
    award_name: str
    category: str # "league", "tournament", "cross_league", "team_of_season"
    league_id: Optional[str] = None
    player_id: str
    player_name: str
    club_id: str
    club_name: str
    position: Optional[str] = None
    stat_summary: str
    score: float

class SeasonAwardsRecord(BaseModel):
    season_year: int
    league_awards: Dict[str, List[AwardWinner]] = Field(default_factory=dict) # league_id -> awards
    league_tots: Dict[str, List[AwardWinner]] = Field(default_factory=dict) # league_id -> Team of the Season 11
    tournament_awards: List[AwardWinner] = Field(default_factory=list) # continental tournament awards
    cross_league_awards: List[AwardWinner] = Field(default_factory=list) # world positional + young player + manager
    world_xi: List[AwardWinner] = Field(default_factory=list) # World Dream 11
    ballon_dor_winner: Optional[AwardWinner] = None # World Golden Ball Winner
    trophy_winners: Dict[str, str] = Field(default_factory=dict)
