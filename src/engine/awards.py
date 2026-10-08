import random
from typing import List, Dict, Tuple, Optional
from src.engine.models import (
    Player, Club, League, ContinentalTournament, Position, 
    AwardWinner, SeasonAwardsRecord, MilestoneEvent
)

class AwardSystem:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def calculate_season_awards(
        self,
        current_season: int,
        leagues: Dict[str, League],
        clubs: Dict[str, Club],
        players: Dict[str, Player],
        tournament: ContinentalTournament
    ) -> SeasonAwardsRecord:
        record = SeasonAwardsRecord(season_year=current_season)
        
        # 1. League-Specific Awards & Teams of the Season (Per League)
        for league_id, league in leagues.items():
            league_players = [
                players[pid] for cid in league.club_ids 
                for pid in clubs[cid].player_ids if pid in players
            ]
            record.league_awards[league_id] = self._calculate_league_awards(
                league, league_players, clubs, current_season
            )
            record.league_tots[league_id] = self._calculate_league_tots(
                league, league_players, clubs
            )
            
        # 2. Continental Tournament Awards
        tourn_players = [
            players[pid] for cid in tournament.qualified_club_ids 
            for pid in clubs[cid].player_ids if pid in players
        ]
        record.tournament_awards = self._calculate_tournament_awards(
            tournament, tourn_players, clubs, current_season
        )
        
        # 3. Cross-League Positional Awards, World XI & Ballon d'Or
        all_active_players = list(players.values())
        cross_awards, ballon_dor, world_xi = self._calculate_cross_league_awards(
            all_active_players, clubs, current_season
        )
        record.cross_league_awards = cross_awards
        record.ballon_dor_winner = ballon_dor
        record.world_xi = world_xi
        
        # Record milestones for all award winners
        self._record_milestones(record, players, current_season)
        
        return record

    def _calculate_league_awards(
        self, 
        league: League, 
        league_players: List[Player], 
        clubs: Dict[str, Club],
        season_year: int
    ) -> List[AwardWinner]:
        awards: List[AwardWinner] = []
        if not league_players:
            return awards
            
        by_pos = {
            Position.GK: [p for p in league_players if p.position == Position.GK],
            Position.DEF: [p for p in league_players if p.position == Position.DEF],
            Position.MID: [p for p in league_players if p.position == Position.MID],
            Position.FWD: [p for p in league_players if p.position == Position.FWD],
        }

        # 1. Player of the Season (MVP)
        poty = max(league_players, key=lambda p: self._calculate_player_season_score(p, clubs))
        awards.append(AwardWinner(
            award_id=f"poty_{league.id}",
            award_name=f"{league.name} Player of the Season",
            category="league",
            league_id=league.id,
            player_id=poty.id,
            player_name=poty.name,
            club_id=poty.contract.club_id if poty.contract else "",
            club_name=poty.contract.club_name if poty.contract else "",
            position=poty.position.value,
            stat_summary=f"{poty.season_goals}G / {poty.season_assists}A • Rating {poty.overall_rating}",
            score=self._calculate_player_season_score(poty, clubs)
        ))

        # 2. Golden Boot (Top Goal Scorer)
        if league_players:
            top_scorer = max(
                league_players, 
                key=lambda p: (p.season_goals, p.season_assists, -p.season_matches, p.overall_rating)
            )
            awards.append(AwardWinner(
                award_id=f"golden_boot_{league.id}",
                award_name=f"{league.name} Golden Boot (Top Scorer)",
                category="league",
                league_id=league.id,
                player_id=top_scorer.id,
                player_name=top_scorer.name,
                club_id=top_scorer.contract.club_id if top_scorer.contract else "",
                club_name=top_scorer.contract.club_name if top_scorer.contract else "",
                position=top_scorer.position.value,
                stat_summary=f"{top_scorer.season_goals} Goals ({top_scorer.season_matches} Apps)",
                score=float(top_scorer.season_goals)
            ))

        # 3. Midfielder of the Season & Playmaker of the Year
        if by_pos[Position.MID]:
            best_mid = max(
                by_pos[Position.MID], 
                key=lambda p: (p.season_assists, p.season_goals, p.overall_rating)
            )
            awards.append(AwardWinner(
                award_id=f"best_mid_{league.id}",
                award_name=f"{league.name} Midfielder of the Season",
                category="league",
                league_id=league.id,
                player_id=best_mid.id,
                player_name=best_mid.name,
                club_id=best_mid.contract.club_id if best_mid.contract else "",
                club_name=best_mid.contract.club_name if best_mid.contract else "",
                position="MID",
                stat_summary=f"{best_mid.season_assists} Assists • {best_mid.season_goals} Goals",
                score=float(best_mid.season_assists * 2.5 + best_mid.season_goals)
            ))

        # 4. Defender of the Season
        if by_pos[Position.DEF]:
            best_def = max(
                by_pos[Position.DEF], 
                key=lambda p: (p.season_clean_sheets, p.overall_rating, p.season_goals)
            )
            awards.append(AwardWinner(
                award_id=f"best_def_{league.id}",
                award_name=f"{league.name} Defender of the Season",
                category="league",
                league_id=league.id,
                player_id=best_def.id,
                player_name=best_def.name,
                club_id=best_def.contract.club_id if best_def.contract else "",
                club_name=best_def.contract.club_name if best_def.contract else "",
                position="DEF",
                stat_summary=f"{best_def.season_clean_sheets} Clean Sheets",
                score=float(best_def.season_clean_sheets * 3 + best_def.season_goals * 2)
            ))

        # 5. Goalkeeper of the Season (Golden Glove)
        if by_pos[Position.GK]:
            best_gk = max(
                by_pos[Position.GK], 
                key=lambda p: (p.season_clean_sheets, p.season_saves, -p.season_goals_conceded)
            )
            awards.append(AwardWinner(
                award_id=f"golden_glove_{league.id}",
                award_name=f"{league.name} Golden Glove",
                category="league",
                league_id=league.id,
                player_id=best_gk.id,
                player_name=best_gk.name,
                club_id=best_gk.contract.club_id if best_gk.contract else "",
                club_name=best_gk.contract.club_name if best_gk.contract else "",
                position="GK",
                stat_summary=f"{best_gk.season_clean_sheets} Clean Sheets • {best_gk.season_saves} Saves",
                score=float(best_gk.season_clean_sheets * 3 + best_gk.season_saves * 0.1)
            ))

        # 6. Young Player of the Season (U21)
        u21_players = [p for p in league_players if p.age <= 21]
        if u21_players:
            young_poty = max(u21_players, key=lambda p: self._calculate_player_season_score(p, clubs))
            awards.append(AwardWinner(
                award_id=f"young_poty_{league.id}",
                award_name=f"{league.name} Young Player of the Season",
                category="league",
                league_id=league.id,
                player_id=young_poty.id,
                player_name=young_poty.name,
                club_id=young_poty.contract.club_id if young_poty.contract else "",
                club_name=young_poty.contract.club_name if young_poty.contract else "",
                position=young_poty.position.value,
                stat_summary=f"Age {young_poty.age} • {young_poty.season_goals}G / {young_poty.season_assists}A • Rating {young_poty.overall_rating}",
                score=self._calculate_player_season_score(young_poty, clubs)
            ))
            
        return awards

    def _calculate_league_tots(
        self, 
        league: League, 
        league_players: List[Player], 
        clubs: Dict[str, Club]
    ) -> List[AwardWinner]:
        """Assembles the official 11-player Team of the Season (1 GK, 4 DEF, 3 MID, 3 FWD)"""
        tots: List[AwardWinner] = []
        if not league_players:
            return tots
            
        by_pos = {
            Position.GK: [p for p in league_players if p.position == Position.GK],
            Position.DEF: [p for p in league_players if p.position == Position.DEF],
            Position.MID: [p for p in league_players if p.position == Position.MID],
            Position.FWD: [p for p in league_players if p.position == Position.FWD],
        }

        # 1 GK
        if by_pos[Position.GK]:
            top_gk = max(by_pos[Position.GK], key=lambda p: (p.season_clean_sheets, p.season_saves, p.overall_rating))
            tots.append(AwardWinner(
                award_id=f"tots_gk_{league.id}",
                award_name=f"{league.name} Team of the Season",
                category="team_of_season",
                league_id=league.id,
                player_id=top_gk.id,
                player_name=top_gk.name,
                club_id=top_gk.contract.club_id if top_gk.contract else "",
                club_name=top_gk.contract.club_name if top_gk.contract else "",
                position="GK",
                stat_summary=f"{top_gk.season_clean_sheets} Clean Sheets • {top_gk.season_saves} Saves",
                score=float(top_gk.season_clean_sheets)
            ))

        # 4 DEF
        top_defs = sorted(by_pos[Position.DEF], key=lambda p: (p.season_clean_sheets, p.overall_rating, p.season_goals), reverse=True)[:4]
        for idx, d in enumerate(top_defs):
            tots.append(AwardWinner(
                award_id=f"tots_def_{league.id}_{idx+1}",
                award_name=f"{league.name} Team of the Season",
                category="team_of_season",
                league_id=league.id,
                player_id=d.id,
                player_name=d.name,
                club_id=d.contract.club_id if d.contract else "",
                club_name=d.contract.club_name if d.contract else "",
                position="DEF",
                stat_summary=f"{d.season_clean_sheets} Clean Sheets • Rating {d.overall_rating}",
                score=float(d.season_clean_sheets)
            ))

        # 3 MID
        top_mids = sorted(by_pos[Position.MID], key=lambda p: (p.season_assists, p.season_goals, p.overall_rating), reverse=True)[:3]
        for idx, m in enumerate(top_mids):
            tots.append(AwardWinner(
                award_id=f"tots_mid_{league.id}_{idx+1}",
                award_name=f"{league.name} Team of the Season",
                category="team_of_season",
                league_id=league.id,
                player_id=m.id,
                player_name=m.name,
                club_id=m.contract.club_id if m.contract else "",
                club_name=m.contract.club_name if m.contract else "",
                position="MID",
                stat_summary=f"{m.season_assists}A • {m.season_goals}G",
                score=float(m.season_assists)
            ))

        # 3 FWD
        top_fwds = sorted(by_pos[Position.FWD], key=lambda p: (p.season_goals, p.season_assists, p.overall_rating), reverse=True)[:3]
        for idx, f in enumerate(top_fwds):
            tots.append(AwardWinner(
                award_id=f"tots_fwd_{league.id}_{idx+1}",
                award_name=f"{league.name} Team of the Season",
                category="team_of_season",
                league_id=league.id,
                player_id=f.id,
                player_name=f.name,
                club_id=f.contract.club_id if f.contract else "",
                club_name=f.contract.club_name if f.contract else "",
                position="FWD",
                stat_summary=f"{f.season_goals} Goals • Rating {f.overall_rating}",
                score=float(f.season_goals)
            ))

        return tots

    def _calculate_tournament_awards(
        self,
        tournament: ContinentalTournament,
        tourn_players: List[Player],
        clubs: Dict[str, Club],
        season_year: int
    ) -> List[AwardWinner]:
        awards: List[AwardWinner] = []
        if not tourn_players:
            return awards
            
        by_pos = {
            Position.GK: [p for p in tourn_players if p.position == Position.GK],
            Position.DEF: [p for p in tourn_players if p.position == Position.DEF],
            Position.MID: [p for p in tourn_players if p.position == Position.MID],
            Position.FWD: [p for p in tourn_players if p.position == Position.FWD],
        }

        # 1. Player of the Tournament
        pott = max(tourn_players, key=lambda p: self._calculate_player_season_score(p, clubs))
        awards.append(AwardWinner(
            award_id="tournament_pott",
            award_name="Continental Player of the Tournament",
            category="tournament",
            player_id=pott.id,
            player_name=pott.name,
            club_id=pott.contract.club_id if pott.contract else "",
            club_name=pott.contract.club_name if pott.contract else "",
            position=pott.position.value,
            stat_summary=f"{pott.season_goals}G / {pott.season_assists}A • Rating {pott.overall_rating}",
            score=self._calculate_player_season_score(pott, clubs)
        ))

        # 2. Golden Boot
        top_scorer = max(tourn_players, key=lambda p: (p.season_goals, p.season_assists, p.overall_rating))
        awards.append(AwardWinner(
            award_id="tournament_top_scorer",
            award_name="Continental Golden Boot",
            category="tournament",
            player_id=top_scorer.id,
            player_name=top_scorer.name,
            club_id=top_scorer.contract.club_id if top_scorer.contract else "",
            club_name=top_scorer.contract.club_name if top_scorer.contract else "",
            position="FWD",
            stat_summary=f"{top_scorer.season_goals} Goals",
            score=float(top_scorer.season_goals)
        ))

        # 3. Best Goalkeeper
        if by_pos[Position.GK]:
            best_gk = max(by_pos[Position.GK], key=lambda p: (p.season_clean_sheets, p.season_saves))
            awards.append(AwardWinner(
                award_id="tournament_best_gk",
                award_name="Continental Best Goalkeeper",
                category="tournament",
                player_id=best_gk.id,
                player_name=best_gk.name,
                club_id=best_gk.contract.club_id if best_gk.contract else "",
                club_name=best_gk.contract.club_name if best_gk.contract else "",
                position="GK",
                stat_summary=f"{best_gk.season_clean_sheets} Clean Sheets",
                score=float(best_gk.season_clean_sheets)
            ))

        # 4. Best Defender
        if by_pos[Position.DEF]:
            best_def = max(by_pos[Position.DEF], key=lambda p: (p.season_clean_sheets, p.overall_rating))
            awards.append(AwardWinner(
                award_id="tournament_best_def",
                award_name="Continental Best Defender",
                category="tournament",
                player_id=best_def.id,
                player_name=best_def.name,
                club_id=best_def.contract.club_id if best_def.contract else "",
                club_name=best_def.contract.club_name if best_def.contract else "",
                position="DEF",
                stat_summary=f"{best_def.season_clean_sheets} Clean Sheets",
                score=float(best_def.season_clean_sheets)
            ))

        # 5. Best Midfielder
        if by_pos[Position.MID]:
            best_mid = max(by_pos[Position.MID], key=lambda p: (p.season_assists, p.season_goals, p.overall_rating))
            awards.append(AwardWinner(
                award_id="tournament_best_mid",
                award_name="Continental Best Midfielder",
                category="tournament",
                player_id=best_mid.id,
                player_name=best_mid.name,
                club_id=best_mid.contract.club_id if best_mid.contract else "",
                club_name=best_mid.contract.club_name if best_mid.contract else "",
                position="MID",
                stat_summary=f"{best_mid.season_assists} Assists • {best_mid.season_goals} Goals",
                score=float(best_mid.season_assists)
            ))

        return awards

    def _calculate_cross_league_awards(
        self,
        all_players: List[Player],
        clubs: Dict[str, Club],
        season_year: int
    ) -> Tuple[List[AwardWinner], Optional[AwardWinner], List[AwardWinner]]:
        """
        Calculates prestigious global football awards:
        1. World Golden Ball (World Player of the Year)
        2. World Golden Glove (World Goalkeeper of the Year)
        3. World Defender of the Year
        4. World Midfielder of the Year
        5. World Golden Boot (World Striker/Forward of the Year)
        6. World Golden Boy (World Best Young Player U21)
        7. World Dream XI (1 GK, 4 DEF, 3 MID, 3 FWD)
        """
        by_pos = {
            Position.GK: [p for p in all_players if p.position == Position.GK],
            Position.DEF: [p for p in all_players if p.position == Position.DEF],
            Position.MID: [p for p in all_players if p.position == Position.MID],
            Position.FWD: [p for p in all_players if p.position == Position.FWD],
        }
        
        position_winners: List[AwardWinner] = []
        
        # 1. World Goalkeeper (World Golden Glove)
        if by_pos[Position.GK]:
            best_gk = max(by_pos[Position.GK], key=lambda p: (p.season_clean_sheets, p.season_saves, p.overall_rating))
            gk_score = self._calculate_player_season_score(best_gk, clubs)
            position_winners.append(AwardWinner(
                award_id="world_golden_glove",
                award_name="World Golden Glove (World Goalkeeper of the Year)",
                category="cross_league",
                player_id=best_gk.id,
                player_name=best_gk.name,
                club_id=best_gk.contract.club_id if best_gk.contract else "",
                club_name=best_gk.contract.club_name if best_gk.contract else "",
                position="GK",
                stat_summary=f"{best_gk.season_clean_sheets} Clean Sheets • {best_gk.season_saves} Saves • Rating {best_gk.overall_rating}",
                score=gk_score
            ))

        # 2. World Defender of the Year
        if by_pos[Position.DEF]:
            best_def = max(by_pos[Position.DEF], key=lambda p: (p.season_clean_sheets, p.overall_rating, p.season_goals))
            def_score = self._calculate_player_season_score(best_def, clubs)
            position_winners.append(AwardWinner(
                award_id="world_best_def",
                award_name="World Defender of the Year",
                category="cross_league",
                player_id=best_def.id,
                player_name=best_def.name,
                club_id=best_def.contract.club_id if best_def.contract else "",
                club_name=best_def.contract.club_name if best_def.contract else "",
                position="DEF",
                stat_summary=f"{best_def.season_clean_sheets} Clean Sheets • Rating {best_def.overall_rating}",
                score=def_score
            ))

        # 3. World Midfielder of the Year
        if by_pos[Position.MID]:
            best_mid = max(by_pos[Position.MID], key=lambda p: (p.season_assists, p.season_goals, p.overall_rating))
            mid_score = self._calculate_player_season_score(best_mid, clubs)
            position_winners.append(AwardWinner(
                award_id="world_best_mid",
                award_name="World Midfielder of the Year",
                category="cross_league",
                player_id=best_mid.id,
                player_name=best_mid.name,
                club_id=best_mid.contract.club_id if best_mid.contract else "",
                club_name=best_mid.contract.club_name if best_mid.contract else "",
                position="MID",
                stat_summary=f"{best_mid.season_assists} Assists • {best_mid.season_goals} Goals • Rating {best_mid.overall_rating}",
                score=mid_score
            ))

        # 4. World Golden Boot (World Top Scorer)
        if all_players:
            best_fwd = max(all_players, key=lambda p: (p.season_goals, p.season_assists, -p.season_matches, p.overall_rating))
            fwd_score = self._calculate_player_season_score(best_fwd, clubs)
            position_winners.append(AwardWinner(
                award_id="world_golden_boot",
                award_name="World Golden Boot (World Top Scorer)",
                category="cross_league",
                player_id=best_fwd.id,
                player_name=best_fwd.name,
                club_id=best_fwd.contract.club_id if best_fwd.contract else "",
                club_name=best_fwd.contract.club_name if best_fwd.contract else "",
                position=best_fwd.position.value,
                stat_summary=f"{best_fwd.season_goals} Goals • {best_fwd.season_assists} Assists • Rating {best_fwd.overall_rating}",
                score=fwd_score
            ))

        # 5. World Golden Boy (World Best Young Player U21)
        u21_world = [p for p in all_players if p.age <= 21]
        if u21_world:
            golden_boy = max(u21_world, key=lambda p: self._calculate_player_season_score(p, clubs))
            position_winners.append(AwardWinner(
                award_id="world_golden_boy",
                award_name="World Golden Boy (World Best Under-21 Player)",
                category="cross_league",
                player_id=golden_boy.id,
                player_name=golden_boy.name,
                club_id=golden_boy.contract.club_id if golden_boy.contract else "",
                club_name=golden_boy.contract.club_name if golden_boy.contract else "",
                position=golden_boy.position.value,
                stat_summary=f"Age {golden_boy.age} • {golden_boy.season_goals}G / {golden_boy.season_assists}A • Rating {golden_boy.overall_rating}",
                score=self._calculate_player_season_score(golden_boy, clubs)
            ))

        # 6. World Golden Ball (World Player of the Year)
        ballon_dor: Optional[AwardWinner] = None
        overall_best = max(all_players, key=lambda p: self._calculate_player_season_score(p, clubs))
        bdr_score = self._calculate_player_season_score(overall_best, clubs)
        ballon_dor = AwardWinner(
            award_id="world_golden_ball",
            award_name="World Golden Ball (World Player of the Year)",
            category="cross_league",
            player_id=overall_best.id,
            player_name=overall_best.name,
            club_id=overall_best.contract.club_id if overall_best.contract else "",
            club_name=overall_best.contract.club_name if overall_best.contract else "",
            position=overall_best.position.value,
            stat_summary=f"{overall_best.season_goals}G / {overall_best.season_assists}A • Rating {overall_best.overall_rating}",
            score=bdr_score
        )
        overall_best.career_ballon_dors += 1

        # 7. World Dream XI (World Team of the Year)
        world_xi: List[AwardWinner] = []
        if by_pos[Position.GK]:
            w_gk = max(by_pos[Position.GK], key=lambda p: (p.season_clean_sheets, p.season_saves, p.overall_rating))
            world_xi.append(AwardWinner(
                award_id="world_dream_xi_gk",
                award_name="World Dream XI",
                category="team_of_season",
                player_id=w_gk.id,
                player_name=w_gk.name,
                club_id=w_gk.contract.club_id if w_gk.contract else "",
                club_name=w_gk.contract.club_name if w_gk.contract else "",
                position="GK",
                stat_summary=f"{w_gk.season_clean_sheets} CS • Rating {w_gk.overall_rating}",
                score=float(w_gk.overall_rating)
            ))
            
        w_defs = sorted(by_pos[Position.DEF], key=lambda p: (p.season_clean_sheets, p.overall_rating, p.season_goals), reverse=True)[:4]
        for idx, d in enumerate(w_defs):
            world_xi.append(AwardWinner(
                award_id=f"world_dream_xi_def_{idx+1}",
                award_name="World Dream XI",
                category="team_of_season",
                player_id=d.id,
                player_name=d.name,
                club_id=d.contract.club_id if d.contract else "",
                club_name=d.contract.club_name if d.contract else "",
                position="DEF",
                stat_summary=f"{d.season_clean_sheets} CS • Rating {d.overall_rating}",
                score=float(d.overall_rating)
            ))

        w_mids = sorted(by_pos[Position.MID], key=lambda p: (p.season_assists, p.season_goals, p.overall_rating), reverse=True)[:3]
        for idx, m in enumerate(w_mids):
            world_xi.append(AwardWinner(
                award_id=f"world_dream_xi_mid_{idx+1}",
                award_name="World Dream XI",
                category="team_of_season",
                player_id=m.id,
                player_name=m.name,
                club_id=m.contract.club_id if m.contract else "",
                club_name=m.contract.club_name if m.contract else "",
                position="MID",
                stat_summary=f"{m.season_assists}A • {m.season_goals}G • Rating {m.overall_rating}",
                score=float(m.overall_rating)
            ))

        w_fwds = sorted(by_pos[Position.FWD], key=lambda p: (p.season_goals, p.season_assists, p.overall_rating), reverse=True)[:3]
        for idx, f in enumerate(w_fwds):
            world_xi.append(AwardWinner(
                award_id=f"world_dream_xi_fwd_{idx+1}",
                award_name="World Dream XI",
                category="team_of_season",
                player_id=f.id,
                player_name=f.name,
                club_id=f.contract.club_id if f.contract else "",
                club_name=f.contract.club_name if f.contract else "",
                position="FWD",
                stat_summary=f"{f.season_goals}G • Rating {f.overall_rating}",
                score=float(f.overall_rating)
            ))

        return position_winners, ballon_dor, world_xi

    def _calculate_player_season_score(self, player: Player, clubs: Dict[str, Club]) -> float:
        # Primary component: on-pitch stats (dominates - 70%)
        stat_points = 0.0
        if player.position == Position.FWD:
            stat_points = (player.season_goals * 6.0) + (player.season_assists * 2.5)
        elif player.position == Position.MID:
            stat_points = (player.season_assists * 6.0) + (player.season_goals * 4.0)
        elif player.position == Position.DEF:
            stat_points = (player.season_clean_sheets * 6.5) + (player.season_goals * 3.0)
        else: # GK
            stat_points = (player.season_clean_sheets * 6.5) + (player.season_saves * 0.15)

        # OVR tiebreaker only (10%) — cannot override superior stats
        rating_boost = (player.overall_rating - 50) * 0.20

        # Team success (20%)
        team_points = 0.0
        if player.contract and player.contract.club_id in clubs:
            club = clubs[player.contract.club_id]
            team_points = max(0, 21 - club.last_season_rank) * 1.5

        total_season_score = (stat_points * 0.70) + rating_boost + (team_points * 0.20)
        player.career_score += total_season_score
        return total_season_score


    def _record_milestones(
        self, 
        record: SeasonAwardsRecord, 
        players: Dict[str, Player],
        season_year: int
    ):
        # 1. League awards
        for awards_list in record.league_awards.values():
            for aw in awards_list:
                if aw.player_id in players:
                    p = players[aw.player_id]
                    p.season_awards.append(aw.award_name)
                    p.milestones.append(MilestoneEvent(
                        season_year=season_year,
                        age=p.age,
                        category="award",
                        title=f"Won {aw.award_name}",
                        description=f"Honored with {aw.award_name} ({aw.stat_summary}).",
                        club_name=aw.club_name
                    ))

        # 2. League Team of the Season
        for tots_list in record.league_tots.values():
            for aw in tots_list:
                if aw.player_id in players:
                    p = players[aw.player_id]
                    p.season_awards.append(aw.award_name)
                    p.milestones.append(MilestoneEvent(
                        season_year=season_year,
                        age=p.age,
                        category="award",
                        title=f"Selected in {aw.award_name}",
                        description=f"Inducted into official Best XI as {aw.position} ({aw.stat_summary}).",
                        club_name=aw.club_name
                    ))

        # 3. Tournament awards
        for aw in record.tournament_awards:
            if aw.player_id in players:
                p = players[aw.player_id]
                p.season_awards.append(aw.award_name)
                p.milestones.append(MilestoneEvent(
                    season_year=season_year,
                    age=p.age,
                    category="award",
                    title=f"Won {aw.award_name}",
                    description=f"Continental tournament accolade ({aw.stat_summary}).",
                    club_name=aw.club_name
                ))

        # 4. Cross-League Positional awards
        for aw in record.cross_league_awards:
            if aw.player_id in players:
                p = players[aw.player_id]
                p.season_awards.append(aw.award_name)
                p.milestones.append(MilestoneEvent(
                    season_year=season_year,
                    age=p.age,
                    category="award",
                    title=f"Won {aw.award_name}",
                    description=f"World positional honor ({aw.stat_summary}).",
                    club_name=aw.club_name
                ))

        # 5. World Golden Ball (World Player of the Year)
        if record.ballon_dor_winner and record.ballon_dor_winner.player_id in players:
            bp = players[record.ballon_dor_winner.player_id]
            bp.season_awards.append("World Golden Ball")
            bp.milestones.append(MilestoneEvent(
                season_year=season_year,
                age=bp.age,
                category="award",
                title="Crowned World Golden Ball Winner 🌟",
                description="Recognized as the premier footballer on the planet (World Player of the Year).",
                club_name=record.ballon_dor_winner.club_name
            ))

        # 6. World Dream XI
        for aw in record.world_xi:
            if aw.player_id in players:
                p = players[aw.player_id]
                p.season_awards.append("World Dream XI")
                p.milestones.append(MilestoneEvent(
                    season_year=season_year,
                    age=p.age,
                    category="award",
                    title="Named in World Dream XI 🏆",
                    description=f"Selected into the premier 11 players in world football as {aw.position}.",
                    club_name=aw.club_name
                ))
