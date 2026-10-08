import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from src.engine.models.contract import Position, PlayerTier, Contract, InjuryState, InjurySeverity

class SeasonStatRecord(BaseModel):
    season_year: int
    club_id: str
    club_name: str
    league_id: str
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    saves: int = 0
    goals_conceded: int = 0
    average_rating: float = 0.0
    trophies_won: List[str] = Field(default_factory=list)
    awards_won: List[str] = Field(default_factory=list)
    ending_rating: int = 0
    market_value: int = 0

class MilestoneEvent(BaseModel):
    season_year: int
    age: int
    category: str # "transfer", "trophy", "award", "record", "injury", "milestone"
    title: str
    description: str
    club_name: str

class Player(BaseModel):
    id: str = Field(default_factory=lambda: f"ply_{uuid.uuid4().hex[:8]}")
    name: str
    country: str # Real country name
    age: int = 17
    position: Position
    is_user: bool = False
    is_retired: bool = False
    
    # Core Attributes (0-100)
    overall_rating: int = Field(default=60, ge=1, le=100)
    potential: int = Field(default=75, ge=1, le=100)
    attacking: int = Field(default=50, ge=1, le=100)
    playmaking: int = Field(default=50, ge=1, le=100)
    defending: int = Field(default=50, ge=1, le=100)
    physical: int = Field(default=50, ge=1, le=100)
    
    # State, Contracts & Playstyles
    contract: Optional[Contract] = None
    injury: InjuryState = Field(default_factory=InjuryState)
    traits: List[str] = Field(default_factory=list) # Playstyle traits (e.g. "Clinical Finisher", "Big-Game Clutch DNA")
    
    # Personal Life, Wealth & Lifestyle
    net_worth: float = 0.0 # in Millions €
    annual_wage: float = 0.5 # in Millions €
    sponsorship_deals: List[Dict[str, Any]] = Field(default_factory=list)
    properties: List[str] = Field(default_factory=list)
    has_private_lab: bool = False
    relationship_status: str = "Single" # "Single", "In a Relationship", "Married"
    partner_name: Optional[str] = None
    partner_backstory: Optional[str] = None # e.g. "🏡 Childhood Sweetheart"
    partner_origin_story: Optional[str] = None # Detailed narrative of how they met
    partner_meeting_year: Optional[int] = None
    children: List[str] = Field(default_factory=list)
    charities: List[str] = Field(default_factory=list)
    
    # Career Cumulative Stats
    career_matches: int = 0
    career_goals: int = 0
    career_assists: int = 0
    career_clean_sheets: int = 0
    career_saves: int = 0
    career_goals_conceded: int = 0
    career_trophies: int = 0
    career_ballon_dors: int = 0
    max_season_goals: int = 0
    max_season_assists: int = 0
    career_score: float = 0.0 # Running sum for all-time ranking
    
    # International & National Team Stats
    international_caps: int = 0
    international_goals: int = 0
    international_assists: int = 0
    international_trophies: List[str] = Field(default_factory=list)
    national_team_status: str = "Uncapped" # "Uncapped", "U21 International", "Senior Squad Regular", "Starting Pillar", "National Team Captain"
    is_national_team_captain: bool = False
    
    # Current Season Stats
    season_matches: int = 0
    season_goals: int = 0
    season_assists: int = 0
    season_clean_sheets: int = 0
    season_saves: int = 0
    season_goals_conceded: int = 0
    season_awards: List[str] = Field(default_factory=list)
    
    # Historical Timeline & Milestones
    history: List[SeasonStatRecord] = Field(default_factory=list)
    milestones: List[MilestoneEvent] = Field(default_factory=list)

    @property
    def tier(self) -> PlayerTier:
        if self.overall_rating >= 93:
            return PlayerTier.GOD_LEVEL
        elif self.overall_rating >= 85:
            return PlayerTier.BEST
        elif self.overall_rating >= 75:
            return PlayerTier.ELITE
        elif self.overall_rating >= 60:
            return PlayerTier.NORMAL
        return PlayerTier.NORMAL_FILLER

    @property
    def card_style(self) -> str:
        """Card styling theme for eFootball / FIFA inspired UI cards"""
        if self.overall_rating >= 93:
            return "card-god-level"
        elif self.overall_rating >= 85:
            return "card-best"
        elif self.overall_rating >= 75:
            return "card-elite"
        elif self.overall_rating >= 65:
            return "card-gold"
        elif self.overall_rating >= 55:
            return "card-silver"
        return "card-bronze"

    @property
    def position_score(self) -> float:
        """Score used for determining first-choice lineup and match influence"""
        if self.position == Position.GK:
            return (self.defending * 0.6) + (self.physical * 0.4)
        elif self.position == Position.DEF:
            return (self.defending * 0.65) + (self.physical * 0.35)
        elif self.position == Position.MID:
            return (self.playmaking * 0.55) + (self.attacking * 0.3) + (self.defending * 0.15)
        else:  # FWD
            return (self.attacking * 0.7) + (self.physical * 0.3)

    def calculate_market_value(self) -> int:
        """
        Price Table (Section 3.8 of Spec):
        under 60: 1-3M
        60-69:    3-10M
        70-74:    10-20M
        75-79:    40-80M
        80-84:    80-150M
        85-92:    150-300M
        93+:      400-800M
        Modifiers: young + high potential costs more; age 33+ costs less; 1 year left on contract costs less.
        """
        rating = self.overall_rating
        if rating < 60:
            base = 1 + int((rating - 40) / 20 * 2)
        elif rating <= 69:
            base = 3 + int((rating - 60) / 9 * 7)
        elif rating <= 74:
            base = 10 + int((rating - 70) / 4 * 10)
        elif rating <= 79:
            base = 40 + int((rating - 75) / 4 * 40)
        elif rating <= 84:
            base = 80 + int((rating - 80) / 4 * 70)
        elif rating <= 92:
            base = 150 + int((rating - 85) / 7 * 150)
        else:
            base = 400 + int((min(rating, 100) - 93) / 7 * 400)
            
        base = max(1, base)
        
        # Modifiers
        multiplier = 1.0
        # Youth & High Potential premium
        if self.age <= 22 and self.potential > self.overall_rating:
            multiplier += 0.25 * ((self.potential - self.overall_rating) / 15)
        # Age discount
        if self.age >= 33:
            multiplier *= max(0.25, 1.0 - (self.age - 32) * 0.12)
        # Final contract year discount
        if self.contract and self.contract.years_remaining <= 1:
            multiplier *= 0.85
            
        return max(1, int(base * multiplier))

    def reset_season_stats(self):
        self.season_matches = 0
        self.season_goals = 0
        self.season_assists = 0
        self.season_clean_sheets = 0
        self.season_saves = 0
        self.season_goals_conceded = 0
        self.season_awards = []
