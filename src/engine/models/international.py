import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class InternationalMatch(BaseModel):
    id: str = Field(default_factory=lambda: f"intl_m_{uuid.uuid4().hex[:8]}")
    round_name: str # "Group Stage", "Quarter-Finals", "Semi-Finals", "Final", "Friendly"
    competition_name: str # "World Championship", "Continental Nations Cup", "International Qualifiers"
    home_country: str
    away_country: str
    home_goals: int
    away_goals: int
    penalty_winner_country: Optional[str] = None
    winner_country: str
    scorers: List[Dict[str, str]] = Field(default_factory=list) # [{"player_id", "player_name", "country"}]
    assisters: List[Dict[str, str]] = Field(default_factory=list)

class NationalTeam(BaseModel):
    id: str = Field(default_factory=lambda: f"nat_{uuid.uuid4().hex[:8]}")
    country: str
    fifa_ranking: int = 10
    flag_emoji: str = "🏳️"
    primary_color: str = "#1e3a8a"
    secondary_color: str = "#ffffff"
    
    # Squad Selection (Top 23 for current international window)
    squad_player_ids: List[str] = Field(default_factory=list)
    starting_xi_ids: List[str] = Field(default_factory=list)
    captain_player_id: Optional[str] = None
    
    # Honors & History
    world_cup_titles: int = 0
    continental_titles: int = 0
    past_honors: List[str] = Field(default_factory=list)

class InternationalTournament(BaseModel):
    id: str = Field(default_factory=lambda: f"tourn_intl_{uuid.uuid4().hex[:8]}")
    season_year: int
    name: str # "Global World Championship" or "Continental Nations Cup"
    cycle_year: int # 1, 2, 3, or 4
    qualified_countries: List[str] = Field(default_factory=list)
    winner_country: Optional[str] = None
    runner_up_country: Optional[str] = None
    top_scorer_name: Optional[str] = None
    top_scorer_goals: int = 0
    best_player_name: Optional[str] = None
    matches: List[InternationalMatch] = Field(default_factory=list)
