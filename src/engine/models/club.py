import uuid
from typing import List, Dict, Optional, Tuple, Union, Any
from pydantic import BaseModel, Field
from src.engine.models.player import Player
from src.engine.models.contract import Position

class ClubLegend(BaseModel):
    player_id: str
    name: str
    country: str
    position: str
    years_active: str
    matches: int
    goals: int
    assists: int
    trophies: int
    legacy_score: float

class Club(BaseModel):
    id: str = Field(default_factory=lambda: f"clb_{uuid.uuid4().hex[:8]}")
    name: str
    short_name: str
    league_id: str
    country: str
    
    # Financial & Infrastructure
    budget: int = Field(default=50, ge=0)  # In M
    pending_transfer_compensation: int = Field(default=0, ge=0)  # Transfer revenue to credit on top of operating budget baseline
    infrastructure_level: int = Field(default=1, ge=1, le=5)
    seasons_since_infra_upgrade: int = Field(default=0, ge=0)
    last_season_rank: int = 10
    
    recent_ranks: List[int] = Field(default_factory=list)
    
    # Visual & Card Aesthetics (FIFA / eFootball inspired)
    primary_color: str = "#1e3a8a"
    secondary_color: str = "#fbbf24"
    badge_style: str = "shield-classic"
    
    # Squad Lists
    player_ids: List[str] = Field(default_factory=list)
    youth_academy_ids: List[str] = Field(default_factory=list)
    
    # History, Heritage & Trophy Room
    founded_year: int = 1900
    stadium_name: str = "City Arena"
    stadium_capacity: int = 50000
    historical_rival: str = "Local Rivals"
    league_titles: int = 0
    tournament_titles: int = 0
    title_years: List[Union[str, int]] = Field(default_factory=list)
    legends: List[ClubLegend] = Field(default_factory=list)
    
    current_season: int = 1
    
    # Seasonal tracking
    signings_this_window: int = 0
    league_points: int = 0
    league_goals_for: int = 0
    league_goals_against: int = 0
    league_wins: int = 0
    league_draws: int = 0
    league_losses: int = 0

    @property
    def goal_difference(self) -> int:
        return self.league_goals_for - self.league_goals_against

    @property
    def era_silverware(self) -> int:
        """
        Calculates total major trophies won within the last 15 seasons (Season >= current_season - 14).
        """
        if not self.title_years:
            return 0
        import re
        season_nums = []
        for entry in self.title_years:
            m = re.search(r"Season\s+(\d+)", str(entry))
            if m:
                season_nums.append(int(m.group(1)))
            elif isinstance(entry, int):
                season_nums.append(entry)
        if not season_nums:
            return 0
        ref_season = getattr(self, "current_season", 1) or 1
        # Count only trophies won within the last 15 seasons window
        return sum(1 for s in season_nums if s >= (ref_season - 14))

    @property
    def total_trophies(self) -> int:
        return self.league_titles + self.tournament_titles

    @property
    def tier_number(self) -> int:
        """
        Determines canonical prestige tier (1 to 4) blending:
        1. Current Sporting Form: Rolling 3-season average rank (R_3)
        2. Recent Era Dominance: Era Silverware (last 15 seasons)
        3. Historic Institutional Heritage: Lifetime trophies prestige floor
        """
        ranks = self.recent_ranks if self.recent_ranks else [self.last_season_rank]
        recent_3 = ranks[-3:]
        avg_rank = sum(recent_3) / len(recent_3)
        silverware = self.era_silverware
        trophies = self.total_trophies
        
        # Tier 1 (★★★★★): 
        # - Sustained top 4 contenders (avg_rank <= 4.0)
        # - Multi-trophy winners in current era (Era Silverware >= 2)
        # - All-time historic giants staying highly competitive (Total Trophies >= 25 and avg_rank <= 6.0)
        if avg_rank <= 4.0 or silverware >= 2 or (trophies >= 25 and avg_rank <= 6.0):
            return 1
        # Tier 2 (★★★★):
        # - Top 8 contenders (avg_rank <= 8.0)
        # - Major trophy winner in current era (Era Silverware >= 1)
        # - Historic Titan Floor (Total Trophies >= 15): Multi-decade giants never fall below Tier 2
        elif avg_rank <= 8.0 or silverware >= 1 or trophies >= 15:
            return 2
        # Tier 3 (★★★):
        # - Established mid-table (avg_rank <= 14.0)
        # - Historic Heritage Floor (Total Trophies >= 5): Decorated clubs never drop to Tier 4
        elif avg_rank <= 14.0 or trophies >= 5:
            return 3
        # Tier 4 (★★): Top-flight underdogs
        else:
            return 4

    @property
    def tier_stars(self) -> str:
        stars_map = {1: "★★★★★", 2: "★★★★", 3: "★★★", 4: "★★"}
        return stars_map.get(self.tier_number, "★★")

    @property
    def tier_name(self) -> str:
        names_map = {
            1: "👑 Tier 1 • Elite Contender (★★★★★)",
            2: "💎 Tier 2 • Upper Division (★★★★)",
            3: "⚡ Tier 3 • Mid-Table (★★★)",
            4: "🛡️ Tier 4 • Lower Table (★★)"
        }
        return names_map.get(self.tier_number, "🛡️ Tier 4 • Lower Table (★★)")

    @property
    def form_trajectory(self) -> Dict[str, Any]:
        """
        Calculates recent form trajectory badge and description based on last 3-5 season ranks.
        """
        ranks = self.recent_ranks if self.recent_ranks else [self.last_season_rank]
        recent_3 = ranks[-3:]
        avg_rank = sum(recent_3) / len(recent_3)
        
        is_historic_giant = (self.total_trophies >= 10 or self.era_silverware >= 2)
        is_rising = len(recent_3) >= 3 and recent_3[0] > recent_3[1] > recent_3[2]
        is_dropping = len(recent_3) >= 3 and recent_3[0] < recent_3[1] < recent_3[2]
        
        if avg_rank <= 2.5:
            badge = "🔥 Title Contender"
            color = "#22c55e"
            desc = "Dominant league leader consistently challenging for domestic and continental trophies."
        elif is_historic_giant and avg_rank > 8.0:
            badge = "🔄 Squad Transition"
            color = "#f59e0b"
            desc = f"Historic club ({self.league_titles} league titles) undergoing tactical and squad restructuring."
        elif is_rising:
            badge = "⚡ Upward Momentum"
            color = "#38bdf8"
            desc = "Rapidly improving side with successive multi-season gains in the table."
        elif avg_rank <= 5.0:
            badge = "💎 Continental Contender"
            color = "#818cf8"
            desc = "Regular European contender consistently securing upper-table qualification."
        elif avg_rank >= 15.0:
            badge = "⚠️ Relegation Battle"
            color = "#ef4444"
            desc = "Struggling in the lower table fighting for crucial survival points."
        elif is_dropping:
            badge = "📉 Downturn in Form"
            color = "#fb923c"
            desc = "Experiencing a multi-season competitive slump in league standing."
        else:
            badge = "⚖️ Mid-Table Stability"
            color = "#94a3b8"
            desc = "Consistent top-flight mainstay reliably securing comfortable mid-table finishes."
            
        def _ord(n: int) -> str:
            if 11 <= (n % 100) <= 13: return f"{n}th"
            rem = n % 10
            if rem == 1: return f"{n}st"
            if rem == 2: return f"{n}nd"
            if rem == 3: return f"{n}rd"
            return f"{n}th"
            
        form_str = " ➔ ".join(_ord(r) for r in recent_3)
        
        return {
            "badge": badge,
            "color": color,
            "description": desc,
            "recent_ranks": recent_3,
            "form_display": form_str,
            "avg_rank": round(avg_rank, 1)
        }

    def get_first_choice_squad(self, players_dict: Dict[str, Player]) -> Dict[Position, List[Player]]:
        """
        Determines the starting 11 for standard 1-4-4-2 formation:
        1 GK, 4 DEF, 4 MID, 2 FWD.
        Injured players are skipped. If user is in the squad, user is always first-choice in position.
        """
        healthy_players = [
            players_dict[pid] for pid in self.player_ids 
            if pid in players_dict and players_dict[pid].injury.weeks_remaining <= 0
        ]
        
        by_pos: Dict[Position, List[Player]] = {
            Position.GK: [],
            Position.DEF: [],
            Position.MID: [],
            Position.FWD: []
        }
        for p in healthy_players:
            by_pos[p.position].append(p)
            
        # Sort each position by position_score descending
        # User player has priority boost to guarantee starting spot
        for pos in by_pos:
            by_pos[pos].sort(
                key=lambda p: (1 if p.is_user else 0, p.position_score, p.overall_rating), 
                reverse=True
            )
            
        # Required counts: 1 GK, 4 DEF, 4 MID, 2 FWD
        starting_11 = {
            Position.GK: by_pos[Position.GK][:1],
            Position.DEF: by_pos[Position.DEF][:4],
            Position.MID: by_pos[Position.MID][:4],
            Position.FWD: by_pos[Position.FWD][:2]
        }
        return starting_11

    def calculate_squad_ratings(self, players_dict: Dict[str, Player]) -> Tuple[float, float, float]:
        """
        Returns (average_starting_rating, team_attack_strength, team_defense_strength)
        Uses top-heavy superstar weighting so elite players (80+, 85+, 92+)
        exert authentic, match-winning offensive and defensive leverage.
        """
        starters = self.get_first_choice_squad(players_dict)
        all_starters = [p for p_list in starters.values() for p in p_list]
        
        if not all_starters:
            return 60.0, 50.0, 50.0
            
        avg_rating = sum(p.overall_rating for p in all_starters) / len(all_starters)
        
        # 1. Attack strength from FWD and MID (6 players)
        att_players = starters[Position.FWD] + starters[Position.MID]
        if att_players:
            att_scores = sorted(
                [(p.attacking * 0.70 + p.playmaking * 0.30) for p in att_players], 
                reverse=True
            )
            weights = [1.8, 1.4, 1.1, 0.9, 0.8, 0.8][:len(att_scores)]
            weighted_att = sum(s * w for s, w in zip(att_scores, weights)) / sum(weights)
            
            # Superstar offensive surge (80+, 85+, 92+)
            superstar_boost = 0.0
            for p in att_players:
                if p.overall_rating >= 92:
                    superstar_boost += 4.5
                elif p.overall_rating >= 85:
                    superstar_boost += 2.5
                elif p.overall_rating >= 80:
                    superstar_boost += 1.0
            att_strength = weighted_att + min(12.0, superstar_boost)
        else:
            att_strength = 50.0
        
        # 2. Defense strength from GK and DEF (5 players)
        def_players = starters[Position.GK] + starters[Position.DEF]
        if def_players:
            def_scores = sorted(
                [(p.defending * 0.70 + p.physical * 0.30) for p in def_players], 
                reverse=True
            )
            def_weights = [1.6, 1.3, 1.0, 0.9, 0.8][:len(def_scores)]
            weighted_def = sum(s * w for s, w in zip(def_scores, def_weights)) / sum(def_weights)
            
            # Defensive pillar superstar surge (80+, 85+, 92+)
            def_superstar_boost = 0.0
            for p in def_players:
                if p.overall_rating >= 92:
                    def_superstar_boost += 4.5
                elif p.overall_rating >= 85:
                    def_superstar_boost += 2.5
                elif p.overall_rating >= 80:
                    def_superstar_boost += 1.0
            def_strength = weighted_def + min(12.0, def_superstar_boost)
        else:
            def_strength = 50.0
        
        return avg_rating, att_strength, def_strength

    def reset_season_stats(self):
        self.league_points = 0
        self.league_goals_for = 0
        self.league_goals_against = 0
        self.league_wins = 0
        self.league_draws = 0
        self.league_losses = 0
        self.signings_this_window = 0
