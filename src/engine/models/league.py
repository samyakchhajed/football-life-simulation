import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class MatchResult(BaseModel):
    match_id: str = Field(default_factory=lambda: f"m_{uuid.uuid4().hex[:8]}")
    home_club_id: str
    away_club_id: str
    home_club_name: str
    away_club_name: str
    home_goals: int
    away_goals: int
    match_week: int
    is_tournament: bool = False
    
    # Key player events
    scorers: List[Dict[str, str]] = Field(default_factory=list) # [{"player_id": "...", "player_name": "...", "club_id": "..."}]
    assisters: List[Dict[str, str]] = Field(default_factory=list)

class LeagueStanding(BaseModel):
    club_id: str
    club_name: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    form: List[str] = Field(default_factory=list) # Last 5 results ("W", "D", "L")

class League(BaseModel):
    id: str = Field(default_factory=lambda: f"lg_{uuid.uuid4().hex[:6]}")
    name: str
    country: str
    tier: int = 1
    founded_year: int = 1920
    most_successful_club: str = ""
    record_scorer: str = ""
    past_champions: List[Dict[str, Any]] = Field(default_factory=list) # [{"season_label": "2023/24", "club_name": "...", "points": 88, "top_scorer": "..."}]
    club_ids: List[str] = Field(default_factory=list)
    standings: List[LeagueStanding] = Field(default_factory=list)
    fixtures: List[List[Dict[str, str]]] = Field(default_factory=list) # 38 match weeks
    season_results: List[MatchResult] = Field(default_factory=list)

class TournamentMatch(BaseModel):
    match_id: str = Field(default_factory=lambda: f"tm_{uuid.uuid4().hex[:8]}")
    round_name: str # "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"
    home_club_id: str
    away_club_id: str
    home_club_name: str
    away_club_name: str
    home_goals: int
    away_goals: int
    penalty_winner_id: Optional[str] = None
    winner_club_id: str
    scorers: List[Dict[str, str]] = Field(default_factory=list)
    assisters: List[Dict[str, str]] = Field(default_factory=list)

class ContinentalTournament(BaseModel):
    id: str = "continental_cup"
    name: str = "Continental Champions Trophy"
    founded_year: int = 1955
    most_successful_club: str = ""
    past_winners: List[Dict[str, Any]] = Field(default_factory=list) # [{"season_label": "2023/24", "winner_name": "...", "runner_up_name": "...", "score": "2 - 1"}]
    qualified_club_ids: List[str] = Field(default_factory=list)
    rounds: Dict[str, List[TournamentMatch]] = Field(default_factory=dict)
    winner_club_id: Optional[str] = None
    runner_up_club_id: Optional[str] = None
