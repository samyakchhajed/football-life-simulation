import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from src.engine.models.player import Player
from src.engine.models.club import Club, ClubLegend
from src.engine.models.league import League, ContinentalTournament
from src.engine.models.award import SeasonAwardsRecord
from src.engine.models.international import NationalTeam, InternationalTournament, InternationalMatch

CURRENT_RULE_VERSION = "1.0.0"
CURRENT_SCHEMA_VERSION = "1.0.0"

class CompactSeasonHistory(BaseModel):
    season_year: int
    league_champions: Dict[str, str] = Field(default_factory=dict) # league_id -> club_name
    tournament_champion: str = ""
    ballon_dor_winner: str = ""
    top_scorers: Dict[str, str] = Field(default_factory=dict) # league_id -> "Name (Goals)"
    international_champion: Optional[str] = None
    user_player_summary: Optional[Dict[str, Any]] = None

class TransferBidOffer(BaseModel):
    offer_id: str = Field(default_factory=lambda: f"off_{uuid.uuid4().hex[:6]}")
    club_id: str
    club_name: str
    league_name: str
    compensation_fee: int # 100% market value
    contract_years: int # 3-5 years
    expected_role: str = "Guaranteed Starter" # "Guaranteed Starter", "Impact Sub / Rotation", "Squad Depth"
    club_tier: str = "Mid-Table Established"
    club_stars: str = "★★★"
    contextual_reason: str # Tactical reason why the club wants the player
    recent_form_ranks: List[int] = Field(default_factory=list)
    trajectory_status: str = ""
    recent_form_display: str = ""
    annual_wage: float = 1.0 # in Millions € / year
    silverware_bonus: float = 0.5 # in Millions € / trophy
    release_clause: int = 0 # in Millions €
    is_renewal: bool = False

class WorldState(BaseModel):
    world_id: str = Field(default_factory=lambda: f"wld_{uuid.uuid4().hex[:8]}")
    user_id: str = "local_user"
    rule_version: str = CURRENT_RULE_VERSION
    schema_version: str = CURRENT_SCHEMA_VERSION
    seed: int = 42
    
    # Progress State
    current_season: int = 1
    current_stage: int = 1 # 1 to 8 stops per season
    is_career_ended: bool = False
    
    # User Reference
    user_player_id: str
    
    # World Entities
    leagues: Dict[str, League] = Field(default_factory=dict)
    clubs: Dict[str, Club] = Field(default_factory=dict)
    players: Dict[str, Player] = Field(default_factory=dict)
    free_agent_ids: List[str] = Field(default_factory=list)
    tournament: ContinentalTournament = Field(default_factory=ContinentalTournament)
    
    # International Football
    national_teams: Dict[str, NationalTeam] = Field(default_factory=dict) # country_name -> NationalTeam
    active_international_tournament: Optional[InternationalTournament] = None
    international_history: List[InternationalTournament] = Field(default_factory=list)
    
    # Active Season Ephemeral / Staging Data
    active_awards: Optional[SeasonAwardsRecord] = None
    pending_user_offers: List[TransferBidOffer] = Field(default_factory=list)
    pending_injury_choice: bool = False
    
    # Global Compact History & All-Time Legends
    history: List[CompactSeasonHistory] = Field(default_factory=list)
    world_legends: List[ClubLegend] = Field(default_factory=list)
    storylines: List[str] = Field(default_factory=list) # Active news headlines

    def get_user_player(self) -> Optional[Player]:
        return self.players.get(self.user_player_id)

    def get_user_club(self) -> Optional[Club]:
        user_p = self.get_user_player()
        if user_p and user_p.contract:
            return self.clubs.get(user_p.contract.club_id)
        return None
