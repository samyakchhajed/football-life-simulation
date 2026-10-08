import random
from typing import List, Dict, Tuple, Optional
from src.engine.models import (
    Player, Club, League, Position, Contract, TransferBidOffer, MilestoneEvent
)

CONTEXTUAL_REASONS = {
    Position.FWD: [
        "Seeking an elite finisher to spearhead next season's championship challenge.",
        "Replacing a departing striker to maintain attacking firepower.",
        "Adding attacking depth and dynamism for continental competition.",
        "Investing in a high-potential goalscorer to build the team's long-term future."
    ],
    Position.MID: [
        "Looking for a midfield maestro to dictate match tempo and control possession.",
        "Strengthening the midfield core to fix tactical weaknesses.",
        "Adding creative playmaking flair to unlock stubborn defensive blocks.",
        "Signing a dynamic box-to-box midfielder to power transitions."
    ],
    Position.DEF: [
        "Seeking a commanding defensive pillar to solidify our backline.",
        "Replacing an aging veteran defender with proven leadership.",
        "Targeting defensive reinforcements after conceding too many goals last campaign.",
        "Building a rock-solid defensive foundation for our title aspirations."
    ],
    Position.GK: [
        "Signing a reliable starting goalkeeper to secure our goal line.",
        "Fixing critical goalkeeping liabilities identified in recent seasons.",
        "Upgrading to a world-class shot-stopper to win tight knockout ties.",
        "Securing an agile, high-potential goalkeeper for the coming era."
    ]
}

class TransferMarket:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate_offers_for_user(
        self,
        user_player: Player,
        clubs: Dict[str, Club],
        leagues: Dict[str, League]
    ) -> List[TransferBidOffer]:
        """
        Generates contract renewal offer + external club offers for the user player
        when they are in the final year of their contract or expiring.
        """
        offers: List[TransferBidOffer] = []
        market_val = user_player.calculate_market_value()
        
        def _get_club_tier_info(club_obj: Club) -> Tuple[str, str]:
            return club_obj.tier_name, club_obj.tier_stars

        # Helper to compute realistic wage and clauses based on rating & club budget
        def _compute_contract_package(ovr: int, c_budget: int, is_ext: bool) -> Tuple[float, float, int]:
            if ovr < 65:
                wage = round(0.5 + (ovr - 50) * 0.05, 2)
            elif ovr < 75:
                wage = round(1.5 + (ovr - 65) * 0.25, 2)
            elif ovr < 85:
                wage = round(4.5 + (ovr - 75) * 0.65, 2)
            elif ovr < 92:
                wage = round(11.0 + (ovr - 85) * 1.5, 2)
            else:
                wage = round(22.0 + (ovr - 92) * 2.5, 2)
            
            # Rich clubs pay higher wages
            if c_budget > 120:
                wage = round(wage * 1.25, 2)
            elif c_budget < 40:
                wage = round(wage * 0.85, 2)
            
            silv_bonus = round(wage * 0.25, 2)
            rel_clause = max(0, int(market_val * 1.6))
            return wage, silv_bonus, rel_clause

        # 1. Current club renewal offer
        current_club = clubs.get(user_player.contract.club_id) if user_player.contract else None
        if current_club:
            c_tier, c_stars = _get_club_tier_info(current_club)
            c_traj = current_club.form_trajectory
            c_wage, c_bonus, c_clause = _compute_contract_package(user_player.overall_rating, current_club.budget, True)
            offers.append(TransferBidOffer(
                offer_id=f"offer_{user_player.id}_{current_club.id}_renewal",
                club_id=current_club.id,
                club_name=current_club.name,
                league_name=leagues[current_club.league_id].name if current_club.league_id in leagues else "Top League",
                compensation_fee=0,
                contract_years=self.rng.randint(3, 5),
                expected_role="Guaranteed Starter",
                club_tier=c_tier,
                club_stars=c_stars,
                contextual_reason=f"Current club {current_club.name} offers a key contract extension with upgraded terms as a core player.",
                recent_form_ranks=c_traj["recent_ranks"],
                trajectory_status=c_traj["badge"],
                recent_form_display=c_traj["form_display"],
                annual_wage=c_wage,
                silverware_bonus=c_bonus,
                release_clause=c_clause,
                is_renewal=True
            ))
            
        # 2. External interested clubs based on player rating, career phase, and performance
        # Breakout performance (goals, assists, clean sheets) unlocks top bids and international moves immediately
        has_breakout_performance = (
            user_player.season_goals >= 20 or 
            user_player.season_assists >= 10 or 
            user_player.season_clean_sheets >= 12 or 
            user_player.overall_rating >= 76
        )
        is_young_prospect = (user_player.age <= 19 and not has_breakout_performance)
        
        eligible_clubs = []
        for c in clubs.values():
            if current_club and c.id == current_club.id:
                continue
            # Gated domestic progression: young prospects without breakout numbers stay domestic
            if is_young_prospect and c.country.strip().lower() != user_player.country.strip().lower():
                continue
            if c.budget >= market_val or c.last_season_rank <= 12 or c.league_titles >= 5:
                eligible_clubs.append(c)
                
        if not eligible_clubs:
            if is_young_prospect:
                eligible_clubs = [
                    c for c in clubs.values() 
                    if (not current_club or c.id != current_club.id) and c.country.strip().lower() == user_player.country.strip().lower()
                ]
            if not eligible_clubs:
                eligible_clubs = [c for c in clubs.values() if not current_club or c.id != current_club.id]
        
        # Sort by club rank / prestige alignment: breakout performers get bids from title contenders & giants
        if has_breakout_performance:
            eligible_clubs.sort(key=lambda c: (c.last_season_rank, -c.budget))
        else:
            eligible_clubs.sort(
                key=lambda c: abs(c.last_season_rank - max(1, 21 - int(user_player.overall_rating / 5)))
            )
        
        # Pick 3-5 interested clubs with league diversity
        num_offers = min(len(eligible_clubs), self.rng.randint(3, 5))
        for club in eligible_clubs[:num_offers]:
            reasons = CONTEXTUAL_REASONS.get(user_player.position, ["Strengthening squad."])
            reason = self.rng.choice(reasons)
            league_name = leagues[club.league_id].name if club.league_id in leagues else "Top Division"
            c_tier, c_stars = _get_club_tier_info(club)
            c_traj = club.form_trajectory
            c_wage, c_bonus, c_clause = _compute_contract_package(user_player.overall_rating, club.budget, False)
            
            # Determine expected role based on club squad strength and user rating
            if club.last_season_rank <= 4 and user_player.overall_rating < 80:
                if user_player.overall_rating < 74:
                    role = "Squad Depth / Backup"
                    reason += " (Joining elite contender as developmental depth/backup)"
                else:
                    role = "Impact Sub / Rotation"
                    reason += " (Key tactical rotation option for domestic and continental campaigns)"
            elif club.last_season_rank <= 10 and user_player.overall_rating < 72:
                role = "Impact Sub / Rotation"
                reason += " (Talented bench reinforcement looking to challenge for starting XI)"
            else:
                role = "Guaranteed Starter"
                reason += " (Signed to become immediate first-choice pillar)"
            
            offers.append(TransferBidOffer(
                offer_id=f"offer_{user_player.id}_{club.id}_transfer",
                club_id=club.id,
                club_name=club.name,
                league_name=league_name,
                compensation_fee=market_val,
                contract_years=self.rng.randint(3, 5),
                expected_role=role,
                club_tier=c_tier,
                club_stars=c_stars,
                contextual_reason=reason,
                recent_form_ranks=c_traj["recent_ranks"],
                trajectory_status=c_traj["badge"],
                recent_form_display=c_traj["form_display"],
                annual_wage=c_wage,
                silverware_bonus=c_bonus,
                release_clause=c_clause,
                is_renewal=False
            ))
            
        return offers

    def process_ai_transfer_window(
        self,
        clubs: Dict[str, Club],
        players: Dict[str, Player],
        free_agent_ids: List[str],
        current_season: int
    ):
        """
        Executes annual AI transfers adhering to:
        - Max 5 signings per club per window.
        - Minimum squad composition (2 GK, 6 DEF, 6 MID, 4 FWD).
        - Squad limits (18 to 22).
        - Compensation fees (100% of market value) added to selling club's next year budget.
        """
        # Collect expiring and free agent players
        expiring_players = [
            p for p in players.values() 
            if not p.is_user and not p.is_retired and (not p.contract or p.contract.years_remaining <= 0)
        ]
        
        # Shuffle club order
        club_list = list(clubs.values())
        self.rng.shuffle(club_list)
        
        # Phase 1: Fill emergency positional needs below minimums
        for club in club_list:
            if club.signings_this_window >= 5 or len(club.player_ids) >= 22:
                continue
            self._fill_club_minimums(club, clubs, players, free_agent_ids, current_season)
            
        # Phase 2: Targeted upgrades for competitive clubs
        for club in club_list:
            if club.signings_this_window >= 5 or len(club.player_ids) >= 22 or club.budget <= 10:
                continue
            self._attempt_club_upgrade(club, clubs, players, expiring_players, free_agent_ids, current_season)

    def _fill_club_minimums(
        self, 
        club: Club, 
        clubs: Dict[str, Club],
        players: Dict[str, Player], 
        free_agent_ids: List[str],
        current_season: int
    ):
        """Ensures squad meets minimum requirements: 2 GK, 6 DEF, 6 MID, 4 FWD"""
        squad = [players[pid] for pid in club.player_ids if pid in players]
        counts = {
            Position.GK: sum(1 for p in squad if p.position == Position.GK),
            Position.DEF: sum(1 for p in squad if p.position == Position.DEF),
            Position.MID: sum(1 for p in squad if p.position == Position.MID),
            Position.FWD: sum(1 for p in squad if p.position == Position.FWD),
        }
        
        required = {
            Position.GK: 2,
            Position.DEF: 6,
            Position.MID: 6,
            Position.FWD: 4
        }
        
        for pos, min_count in required.items():
            needed = min_count - counts[pos]
            for _ in range(needed):
                if club.signings_this_window >= 5 or len(club.player_ids) >= 22:
                    break
                # Try finding from free agents
                signed = self._sign_free_agent_by_position(club, clubs, pos, players, free_agent_ids, current_season)
                if signed:
                    club.signings_this_window += 1

    def _sign_free_agent_by_position(
        self,
        club: Club,
        clubs: Dict[str, Club],
        pos: Position,
        players: Dict[str, Player],
        free_agent_ids: List[str],
        current_season: int
    ) -> bool:
        candidates = [
            pid for pid in free_agent_ids 
            if pid in players and players[pid].position == pos and not players[pid].is_retired
        ]
        if not candidates:
            return False
            
        # Pick best available candidate
        candidates.sort(key=lambda pid: players[pid].overall_rating, reverse=True)
        chosen_id = candidates[0]
        chosen_player = players[chosen_id]
        
        fee = int(chosen_player.calculate_market_value() * 0.20) # 20% free agent fee
        if club.budget >= fee:
            club.budget -= fee
            if chosen_id in free_agent_ids:
                free_agent_ids.remove(chosen_id)
            # Remove from old club if registered anywhere
            if chosen_player.contract and chosen_player.contract.club_id in clubs:
                old_club = clubs[chosen_player.contract.club_id]
                if chosen_id in old_club.player_ids:
                    old_club.player_ids.remove(chosen_id)
            if chosen_id not in club.player_ids:
                club.player_ids.append(chosen_id)
            chosen_player.contract = Contract(
                club_id=club.id,
                club_name=club.name,
                years_remaining=self.rng.randint(2, 4),
                total_years=4
            )
            return True
        return False

    def _attempt_club_upgrade(
        self,
        club: Club,
        clubs: Dict[str, Club],
        players: Dict[str, Player],
        expiring_players: List[Player],
        free_agent_ids: List[str],
        current_season: int
    ):
        # Find weakest starting position
        squad = [players[pid] for pid in club.player_ids if pid in players]
        if not squad:
            return
            
        weakest_starter = min(squad, key=lambda p: p.overall_rating)
        
        # Look for superior available expiring candidate
        candidates = [
            p for p in expiring_players 
            if p.position == weakest_starter.position 
            and p.overall_rating > weakest_starter.overall_rating + 2
            and p.calculate_market_value() <= club.budget
            and (not p.contract or p.contract.club_id != club.id)
            and (not (p.age <= 19 and p.overall_rating < 76) or p.country.strip().lower() == club.country.strip().lower())
        ]
        
        if candidates:
            candidates.sort(key=lambda p: p.overall_rating, reverse=True)
            chosen = candidates[0]
            val = chosen.calculate_market_value()
            
            # Remove from previous club and transfer compensation fee
            if chosen.contract and chosen.contract.club_id in clubs:
                old_club = clubs[chosen.contract.club_id]
                if chosen.id in old_club.player_ids:
                    old_club.player_ids.remove(chosen.id)
                old_club.budget += val
                old_club.pending_transfer_compensation += val
                
            club.budget = max(0, club.budget - val)
            if chosen.id not in club.player_ids:
                club.player_ids.append(chosen.id)
            club.signings_this_window += 1
            
            chosen.contract = Contract(
                club_id=club.id,
                club_name=club.name,
                years_remaining=self.rng.randint(3, 5),
                total_years=4
            )
            if chosen in expiring_players:
                expiring_players.remove(chosen)
            if chosen.id in free_agent_ids:
                free_agent_ids.remove(chosen.id)
