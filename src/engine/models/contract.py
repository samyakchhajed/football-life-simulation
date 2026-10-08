from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Position(str, Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

class PlayerTier(str, Enum):
    NORMAL_FILLER = "normal_filler"  # under 60
    NORMAL = "normal"                # 60-74
    ELITE = "elite"                  # 75-84
    BEST = "best"                    # 85-92
    GOD_LEVEL = "god_level"          # 93+

class InjurySeverity(str, Enum):
    NONE = "none"
    SMALL = "small"          # 1-3 weeks
    MEDIUM = "medium"        # 4-8 weeks
    HEAVY = "heavy"          # 9-12 weeks
    CAREER_THREAT = "threat" # rare life-threatening

class InjuryState(BaseModel):
    severity: InjurySeverity = InjurySeverity.NONE
    description: str = ""
    weeks_remaining: int = 0
    protection_weeks_remaining: int = 0
    is_career_threatening: bool = False

class Contract(BaseModel):
    club_id: str
    club_name: str
    years_remaining: int = Field(default=3, ge=0)
    total_years: int = Field(default=3, ge=1)
    wage_tier: str = "standard"
