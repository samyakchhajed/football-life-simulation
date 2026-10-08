import math
import random
from typing import List, Dict, Tuple, Optional
from src.engine.models import Player, Club, Position, MatchResult, TournamentMatch

def poisson_sample(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm for Poisson random number generation"""
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= rng.random()
    return k - 1

class MatchSimulator:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def simulate_league_match(
        self, 
        home_club: Club, 
        away_club: Club, 
        players_dict: Dict[str, Player],
        match_week: int
    ) -> MatchResult:
        """
        Simulates a league match using Poisson goal distribution based on
        first-choice starting 11 ratings plus home advantage.
        """
        home_starters = home_club.get_first_choice_squad(players_dict)
        away_starters = away_club.get_first_choice_squad(players_dict)
        
        _, home_att, home_def = home_club.calculate_squad_ratings(players_dict)
        _, away_att, away_def = away_club.calculate_squad_ratings(players_dict)
        
        # Home advantage (+4 rating bonus)
        effective_home_att = home_att + 4.0
        
        # Attack vs Defense delta with decisive match-winning sensitivity
        att_def_delta_home = (effective_home_att - away_def)
        att_def_delta_away = (away_att - home_def)
        
        home_lambda = max(0.25, (effective_home_att / max(1.0, away_def)) * 1.48 + att_def_delta_home * 0.025)
        away_lambda = max(0.20, (away_att / max(1.0, home_def)) * 1.27 + att_def_delta_away * 0.025)
        
        # Clamp lambdas to reasonable bounds (0.20 to 4.5)
        home_lambda = min(4.5, max(0.25, home_lambda))
        away_lambda = min(4.5, max(0.20, away_lambda))
        
        home_goals = poisson_sample(home_lambda, self.rng)
        away_goals = poisson_sample(away_lambda, self.rng)
        
        # Record match participation for all starters
        all_starters = [p for plist in home_starters.values() for p in plist] + \
                       [p for plist in away_starters.values() for p in plist]
        for p in all_starters:
            p.season_matches += 1
            p.career_matches += 1
            
        scorers: List[Dict[str, str]] = []
        assisters: List[Dict[str, str]] = []
        
        # Assign home goals
        for _ in range(home_goals):
            scorer, assister = self._assign_goal_and_assist(home_starters, away_starters)
            if scorer:
                scorers.append({"player_id": scorer.id, "player_name": scorer.name, "club_id": home_club.id})
                scorer.season_goals += 1
                scorer.career_goals += 1
            if assister:
                assisters.append({"player_id": assister.id, "player_name": assister.name, "club_id": home_club.id})
                assister.season_assists += 1
                assister.career_assists += 1
                
        # Assign away goals
        for _ in range(away_goals):
            scorer, assister = self._assign_goal_and_assist(away_starters, home_starters)
            if scorer:
                scorers.append({"player_id": scorer.id, "player_name": scorer.name, "club_id": away_club.id})
                scorer.season_goals += 1
                scorer.career_goals += 1
            if assister:
                assisters.append({"player_id": assister.id, "player_name": assister.name, "club_id": away_club.id})
                assister.season_assists += 1
                assister.career_assists += 1
                
        # Defensive credits (clean sheets, goals conceded, GK saves)
        self._apply_defensive_credit(home_starters, away_goals, away_att)
        self._apply_defensive_credit(away_starters, home_goals, effective_home_att)
        
        # Update club league statistics
        home_club.league_goals_for += home_goals
        home_club.league_goals_against += away_goals
        away_club.league_goals_for += away_goals
        away_club.league_goals_against += home_goals
        
        if home_goals > away_goals:
            home_club.league_points += 3
            home_club.league_wins += 1
            home_club.budget += 3 # 3M for win
            away_club.league_losses += 1
        elif away_goals > home_goals:
            away_club.league_points += 3
            away_club.league_wins += 1
            away_club.budget += 3 # 3M for win
            home_club.league_losses += 1
        else:
            home_club.league_points += 1
            home_club.league_draws += 1
            away_club.league_points += 1
            away_club.league_draws += 1
            
        return MatchResult(
            match_id=f"m_{home_club.id}_{away_club.id}_w{match_week}",
            home_club_id=home_club.id,
            away_club_id=away_club.id,
            home_club_name=home_club.name,
            away_club_name=away_club.name,
            home_goals=home_goals,
            away_goals=away_goals,
            match_week=match_week,
            scorers=scorers,
            assisters=assisters
        )

    def simulate_tournament_match(
        self,
        round_name: str,
        home_club: Club,
        away_club: Club,
        players_dict: Dict[str, Player]
    ) -> TournamentMatch:
        """
        Simulates single-leg knockout tournament match.
        Draws are decided by seeded penalty shootout.
        """
        home_starters = home_club.get_first_choice_squad(players_dict)
        away_starters = away_club.get_first_choice_squad(players_dict)
        
        _, home_att, home_def = home_club.calculate_squad_ratings(players_dict)
        _, away_att, away_def = away_club.calculate_squad_ratings(players_dict)
        
        # Neutral ground (no home advantage bonus)
        att_def_delta_home = (home_att - away_def)
        att_def_delta_away = (away_att - home_def)
        
        home_lambda = min(4.5, max(0.25, (home_att / max(1.0, away_def)) * 1.40 + att_def_delta_home * 0.025))
        away_lambda = min(4.5, max(0.20, (away_att / max(1.0, home_def)) * 1.35 + att_def_delta_away * 0.025))
        
        home_goals = poisson_sample(home_lambda, self.rng)
        away_goals = poisson_sample(away_lambda, self.rng)
        
        # Matches participation
        all_starters = [p for plist in home_starters.values() for p in plist] + \
                       [p for plist in away_starters.values() for p in plist]
        for p in all_starters:
            p.season_matches += 1
            p.career_matches += 1
            
        scorers: List[Dict[str, str]] = []
        assisters: List[Dict[str, str]] = []
        
        for _ in range(home_goals):
            s, a = self._assign_goal_and_assist(home_starters, away_starters)
            if s:
                scorers.append({"player_id": s.id, "player_name": s.name, "club_id": home_club.id})
                s.season_goals += 1
                s.career_goals += 1
            if a:
                assisters.append({"player_id": a.id, "player_name": a.name, "club_id": home_club.id})
                a.season_assists += 1
                a.career_assists += 1
                
        for _ in range(away_goals):
            s, a = self._assign_goal_and_assist(away_starters, home_starters)
            if s:
                scorers.append({"player_id": s.id, "player_name": s.name, "club_id": away_club.id})
                s.season_goals += 1
                s.career_goals += 1
            if a:
                assisters.append({"player_id": a.id, "player_name": a.name, "club_id": away_club.id})
                a.season_assists += 1
                a.career_assists += 1
                
        self._apply_defensive_credit(home_starters, away_goals, away_att)
        self._apply_defensive_credit(away_starters, home_goals, home_att)
        
        penalty_winner_id: Optional[str] = None
        winner_club_id: str
        
        if home_goals > away_goals:
            winner_club_id = home_club.id
        elif away_goals > home_goals:
            winner_club_id = away_club.id
        else:
            # Seeded penalty draw
            home_pen_prob = 0.5 + (home_att - away_att) * 0.01
            if self.rng.random() < home_pen_prob:
                winner_club_id = home_club.id
                penalty_winner_id = home_club.id
            else:
                winner_club_id = away_club.id
                penalty_winner_id = away_club.id
                
        return TournamentMatch(
            match_id=f"tm_{round_name}_{home_club.id}_{away_club.id}",
            round_name=round_name,
            home_club_id=home_club.id,
            away_club_id=away_club.id,
            home_club_name=home_club.name,
            away_club_name=away_club.name,
            home_goals=home_goals,
            away_goals=away_goals,
            penalty_winner_id=penalty_winner_id,
            winner_club_id=winner_club_id,
            scorers=scorers,
            assisters=assisters
        )

    def _assign_goal_and_assist(
        self, 
        att_starters: Dict[Position, List[Player]], 
        def_starters: Dict[Position, List[Player]]
    ) -> Tuple[Optional[Player], Optional[Player]]:
        """
        Assigns one scorer and optional assister using authentic positional weighting
        and non-linear attacking rating influence.
        Position goal shares: FWD (~72%), MID (~22%), DEF (~5.5%), GK (~0.5%).
        """
        candidates: List[Tuple[Player, float]] = []
        
        for pos, players in att_starters.items():
            if not players:
                continue
            if pos == Position.FWD:
                pos_mult = 0.72
            elif pos == Position.MID:
                pos_mult = 0.22
            elif pos == Position.DEF:
                pos_mult = 0.055
            else:
                pos_mult = 0.005
                
            per_player_base = pos_mult / len(players)
            for p in players:
                # Authentic power curve on attacking attribute (70 baseline)
                # 90 attacking -> ~1.75x weight; 70 attacking -> 1.0x weight; 50 attacking -> 0.47x weight
                att_scale = max(0.1, (p.attacking / 70.0) ** 2.2)
                trait_mult = 1.0
                if hasattr(p, "traits"):
                    if "🎯 Clinical Finisher" in p.traits:
                        trait_mult *= 1.35
                    if "🚀 Rapid Counter-Poacher" in p.traits:
                        trait_mult *= 1.25
                    if "🛡️ Target Man & Hold-Up" in p.traits:
                        trait_mult *= 1.20
                    if "👑 Big-Game Clutch DNA" in p.traits:
                        trait_mult *= 1.25
                    if "🎯 Dead-Ball Specialist" in p.traits:
                        trait_mult *= 1.20
                weight = per_player_base * att_scale * trait_mult
                candidates.append((p, weight))
                
        if not candidates:
            return None, None
            
        total_weight = sum(w for _, w in candidates)
        r = self.rng.random() * total_weight
        current = 0.0
        scorer: Optional[Player] = candidates[0][0]
        for p, w in candidates:
            current += w
            if r <= current:
                scorer = p
                break
                
        # Assist: 75% of goals have an assist
        assister: Optional[Player] = None
        if self.rng.random() < 0.75:
            assist_candidates: List[Tuple[Player, float]] = []
            for pos, players in att_starters.items():
                if not players:
                    continue
                if pos == Position.MID:
                    pos_mult = 0.58
                elif pos == Position.FWD:
                    pos_mult = 0.28
                elif pos == Position.DEF:
                    pos_mult = 0.13
                else:
                    pos_mult = 0.01
                per_player_base = pos_mult / len(players)
                for p in players:
                    if p.id != (scorer.id if scorer else ""):
                        pm_scale = max(0.1, (p.playmaking / 70.0) ** 2.0)
                        trait_mult = 1.0
                        if hasattr(p, "traits"):
                            if "🎩 Midfield Maestro" in p.traits:
                                trait_mult *= 1.45
                            if "🎯 Dead-Ball Specialist" in p.traits:
                                trait_mult *= 1.30
                            if "🛡️ Target Man & Hold-Up" in p.traits:
                                trait_mult *= 1.25
                            if "👑 Big-Game Clutch DNA" in p.traits:
                                trait_mult *= 1.20
                            if "⚡ Box-to-Box Engine" in p.traits:
                                trait_mult *= 1.15
                        weight = per_player_base * pm_scale * trait_mult
                        assist_candidates.append((p, weight))
            if assist_candidates:
                tot_a = sum(w for _, w in assist_candidates)
                r_a = self.rng.random() * tot_a
                cur_a = 0.0
                for p, w in assist_candidates:
                    cur_a += w
                    if r_a <= cur_a:
                        assister = p
                        break
                        
        return scorer, assister

    def _apply_defensive_credit(
        self, 
        starters: Dict[Position, List[Player]], 
        goals_conceded: int,
        opponent_att: float
    ):
        """Applies clean sheets, goals conceded, and saves to GK and defenders"""
        # Goalkeeper
        for gk in starters[Position.GK]:
            gk.season_goals_conceded += goals_conceded
            gk.career_goals_conceded += goals_conceded
            if goals_conceded == 0:
                gk.season_clean_sheets += 1
                gk.career_clean_sheets += 1
            # Saves calculation: shots on target ~ 3 to 7 depending on opponent attack
            extra_saves = 1 if (hasattr(gk, "traits") and "🧤 Acrobatic Wall" in gk.traits) else 0
            estimated_shots_on_target = max(goals_conceded, int((opponent_att / 20.0) + self.rng.randint(0, 3) + extra_saves))
            saves_made = max(0, estimated_shots_on_target - goals_conceded)
            gk.season_saves += saves_made
            gk.career_saves += saves_made
            
        # Defenders
        for d in starters[Position.DEF]:
            d.season_goals_conceded += goals_conceded
            d.career_goals_conceded += goals_conceded
            if goals_conceded == 0:
                d.season_clean_sheets += 1
                d.career_clean_sheets += 1
