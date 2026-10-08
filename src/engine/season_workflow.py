import random
from typing import Dict, List, Any, Optional
from src.engine.models import (
    WorldState, Player, Club, League, LeagueStanding, MatchResult, 
    ContinentalTournament, TournamentMatch, Position, CompactSeasonHistory,
    MilestoneEvent, TransferBidOffer
)
from src.engine.match_sim import MatchSimulator
from src.engine.development import DevelopmentEngine
from src.engine.injury_system import InjurySystem
from src.engine.youth_system import YouthAcademySystem
from src.engine.transfer_market import TransferMarket
from src.engine.awards import AwardSystem
from src.engine.storylines import StorylineGenerator
from src.engine.integrity import IntegrityValidator, WorldIntegrityError
from src.engine.international_engine import InternationalEngine
from src.engine.names_database import get_random_female_name_for_country, get_relationship_backstories

class SeasonWorkflowEngine:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.match_sim = MatchSimulator(seed)
        self.dev_engine = DevelopmentEngine(seed)
        self.injury_sys = InjurySystem(seed)
        self.youth_sys = YouthAcademySystem(seed)
        self.transfer_market = TransferMarket(seed)
        self.award_sys = AwardSystem(seed)
        self.story_gen = StorylineGenerator(seed)
        self.intl_engine = InternationalEngine(seed)

    def execute_current_stage(self, world: WorldState, user_choice: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the current stage (1-8) of the season workflow
        and returns the precomputed screen payload.
        """
        stage = world.current_stage
        
        if stage == 1:
            return self._run_stage_1_league_season(world)
        elif stage == 2:
            return self._run_stage_2_tournament_qualification(world)
        elif stage == 3:
            return self._run_stage_3_tournament_results(world)
        elif stage == 4:
            return self._run_stage_4_awards_ceremony(world)
        elif stage == 5:
            return self._run_stage_5_season_summary(world)
        elif stage == 6:
            return self._run_stage_6_offseason_choices(world, user_choice)
        elif stage == 7:
            return self._run_stage_7_transfer_window(world)
        elif stage == 8:
            return self._run_stage_8_new_season_preview(world)
        else:
            raise ValueError(f"Invalid season stage: {stage}")

    def run_stage_1_league(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_1_league_season(world)

    def run_stage_2_tournament_qualification(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_2_tournament_qualification(world)

    def run_stage_3_tournament_results(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_3_tournament_results(world)

    def run_stage_4_awards(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_4_awards_ceremony(world)

    def run_stage_5_season_summary(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_5_season_summary(world)

    def run_stage_6_offseason_choices(self, world: WorldState, user_choice: Optional[str] = None) -> Dict[str, Any]:
        return self._run_stage_6_offseason_choices(world, user_choice)

    def run_stage_7_transfer_window(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_7_transfer_window(world)

    def run_stage_8_launchpad(self, world: WorldState) -> Dict[str, Any]:
        return self._run_stage_8_new_season_preview(world)

    def simulate_full_season(self, world: WorldState, user_choice: Optional[str] = None) -> Dict[int, Dict[str, Any]]:
        """Simulates all 8 season stages sequentially."""
        return {
            1: self.run_stage_1_league(world),
            2: self.run_stage_2_tournament_qualification(world),
            3: self.run_stage_3_tournament_results(world),
            4: self.run_stage_4_awards(world),
            5: self.run_stage_5_season_summary(world),
            6: self.run_stage_6_offseason_choices(world, user_choice),
            7: self.run_stage_7_transfer_window(world),
            8: self.run_stage_8_launchpad(world),
        }

    # -------------------------------------------------------------
    # STAGE 1: LEAGUE SEASON (38 Match Weeks)
    # -------------------------------------------------------------
    def _run_stage_1_league_season(self, world: WorldState) -> Dict[str, Any]:
        # Reset season stats on clubs and synchronize current season
        for club in world.clubs.values():
            club.reset_season_stats()
            club.current_season = world.current_season

        # Simulate all 38 weeks for all 5 leagues
        for league_id, league in world.leagues.items():
            league.season_results = []
            
            # Double round-robin (38 weeks)
            for week_idx, week_fixtures in enumerate(league.fixtures):
                for fixture in week_fixtures:
                    home_club = world.clubs[fixture["home_id"]]
                    away_club = world.clubs[fixture["away_id"]]
                    
                    # Match injury processing
                    match_starters = [
                        world.players[pid] for pid in home_club.player_ids + away_club.player_ids 
                        if pid in world.players
                    ]
                    self.injury_sys.process_match_injuries(match_starters)
                    
                    result = self.match_sim.simulate_league_match(
                        home_club, away_club, world.players, week_idx + 1
                    )
                    league.season_results.append(result)
                    
            # Compute league standings
            self._update_league_standings(league, world.clubs)
            
            # Record season champion into league past champions roll
            if league.standings:
                champ_st = league.standings[0]
                champ_clb = world.clubs[champ_st.club_id]
                l_players = [world.players[pid] for cid in league.club_ids for pid in world.clubs[cid].player_ids if pid in world.players]
                top_p = max(l_players, key=lambda p: (p.season_goals, p.season_assists)) if l_players else None
                top_scorer_str = f"{top_p.name} ({top_p.season_goals}G)" if top_p else ""
                
                league.past_champions.insert(0, {
                    "season_label": f"Season {world.current_season}",
                    "club_name": champ_clb.name,
                    "points": champ_st.points,
                    "top_scorer": top_scorer_str
                })
            
        user = world.get_user_player()
        user_club = world.get_user_club()
        
        # Advance to Stage 2
        world.current_stage = 2
        
        return {
            "stage": 1,
            "title": "League Season Concluded",
            "season_year": world.current_season,
            "user_player": user.model_dump() if user else None,
            "user_club": user_club.model_dump() if user_club else None,
            "leagues": {lid: l.model_dump() for lid, l in world.leagues.items()},
            "top_scorers": self._get_world_top_scorers(world)
        }

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # STAGE 2: TOURNAMENT QUALIFICATION (32 Teams)
    # -------------------------------------------------------------
    def _run_stage_2_tournament_qualification(self, world: WorldState) -> Dict[str, Any]:
        qualified_ids: List[str] = []
        fourth_place_candidates: List[Club] = []
        
        # Top 3 from each of the 10 leagues = 30 clubs
        for league in world.leagues.values():
            top_3 = [standing.club_id for standing in league.standings[:3]]
            qualified_ids.extend(top_3)
            if len(league.standings) >= 4:
                fourth_club = world.clubs[league.standings[3].club_id]
                fourth_place_candidates.append(fourth_club)
                
        # 2 Wildcards (Best 2 4th-placed clubs across all 10 leagues)
        if fourth_place_candidates:
            fourth_place_candidates.sort(
                key=lambda c: (c.league_points, c.goal_difference, c.league_goals_for), 
                reverse=True
            )
            for c in fourth_place_candidates[:2]:
                if c.id not in qualified_ids:
                    qualified_ids.append(c.id)
            
        world.tournament.qualified_club_ids = qualified_ids
        world.tournament.rounds = {}
        
        user_club = world.get_user_club()
        user_qualified = user_club.id in qualified_ids if user_club else False
        
        world.current_stage = 3
        
        return {
            "stage": 2,
            "title": "Continental Champions Trophy — 32 Qualified Clubs",
            "season_year": world.current_season,
            "qualified_clubs": [world.clubs[cid].model_dump() for cid in qualified_ids if cid in world.clubs],
            "user_club_qualified": user_qualified,
            "user_club_name": user_club.name if user_club else "",
            "tournament_history": world.tournament.past_winners
        }

    # -------------------------------------------------------------
    # STAGE 3: TOURNAMENT KNOCKOUT RESULTS (32-Team Bracket)
    # -------------------------------------------------------------
    def _run_stage_3_tournament_results(self, world: WorldState) -> Dict[str, Any]:
        participants = list(world.tournament.qualified_club_ids)
        self.rng.shuffle(participants)
        
        rounds_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Round of 32 (16 matches) - if 32 teams qualified
        r32_winners = []
        if len(participants) >= 32:
            r32_matches = []
            for i in range(0, 32, 2):
                if i + 1 < len(participants):
                    h = world.clubs[participants[i]]
                    a = world.clubs[participants[i+1]]
                    m = self.match_sim.simulate_tournament_match("Round of 32", h, a, world.players)
                    r32_matches.append(m)
                    r32_winners.append(m.winner_club_id)
            world.tournament.rounds["Round of 32"] = r32_matches
            rounds_data["Round of 32"] = [m.model_dump() for m in r32_matches]
        else:
            r32_winners = participants[:16]

        # Round of 16 (8 matches)
        r16_matches = []
        r16_winners = []
        for i in range(0, len(r32_winners), 2):
            if i + 1 < len(r32_winners):
                h = world.clubs[r32_winners[i]]
                a = world.clubs[r32_winners[i+1]]
                m = self.match_sim.simulate_tournament_match("Round of 16", h, a, world.players)
                r16_matches.append(m)
                r16_winners.append(m.winner_club_id)
        world.tournament.rounds["Round of 16"] = r16_matches
        rounds_data["Round of 16"] = [m.model_dump() for m in r16_matches]
        
        # Quarter-Finals (4 matches)
        qf_matches = []
        qf_winners = []
        for i in range(0, len(r16_winners), 2):
            h = world.clubs[r16_winners[i]]
            a = world.clubs[r16_winners[i+1]]
            m = self.match_sim.simulate_tournament_match("Quarter-Finals", h, a, world.players)
            qf_matches.append(m)
            qf_winners.append(m.winner_club_id)
        world.tournament.rounds["Quarter-Finals"] = qf_matches
        rounds_data["Quarter-Finals"] = [m.model_dump() for m in qf_matches]
        
        # Semi-Finals (2 matches)
        sf_matches = []
        sf_winners = []
        sf_losers = []
        for i in range(0, len(qf_winners), 2):
            h = world.clubs[qf_winners[i]]
            a = world.clubs[qf_winners[i+1]]
            m = self.match_sim.simulate_tournament_match("Semi-Finals", h, a, world.players)
            sf_matches.append(m)
            sf_winners.append(m.winner_club_id)
            sf_losers.append(h.id if m.winner_club_id == a.id else a.id)
        world.tournament.rounds["Semi-Finals"] = sf_matches
        rounds_data["Semi-Finals"] = [m.model_dump() for m in sf_matches]
        
        # Final
        h = world.clubs[sf_winners[0]]
        a = world.clubs[sf_winners[1]]
        final_match = self.match_sim.simulate_tournament_match("Final", h, a, world.players)
        world.tournament.rounds["Final"] = [final_match]
        rounds_data["Final"] = [final_match.model_dump()]
        
        winner_id = final_match.winner_club_id
        runner_up_id = h.id if winner_id == a.id else a.id
        world.tournament.winner_club_id = winner_id
        world.tournament.runner_up_club_id = runner_up_id
        
        # Award continental trophy to winner
        winner_club = world.clubs[winner_id]
        winner_club.tournament_titles += 1
        winner_club.title_years.append(f"Season {world.current_season} (Continental Cup)")
        from src.engine.models import MilestoneEvent
        for pid in winner_club.player_ids:
            if pid in world.players:
                p = world.players[pid]
                p.career_trophies += 1
                p.milestones.append(MilestoneEvent(
                    season_year=world.current_season,
                    age=p.age,
                    category="trophy",
                    title="Won Continental Champions Trophy 🏆",
                    description=f"Lifted continental silverware with {winner_club.name} ({final_match.home_goals}-{final_match.away_goals} final).",
                    club_name=winner_club.name
                ))
                
        # Record into past winners
        world.tournament.past_winners.insert(0, {
            "season_label": f"Season {world.current_season}",
            "winner_name": winner_club.name,
            "winner_club_id": winner_club.id,
            "runner_up_name": world.clubs[runner_up_id].name,
            "runner_up_club_id": runner_up_id,
            "score": f"{final_match.home_goals} - {final_match.away_goals}"
        })
                
        # Simulate Summer International Football Tournament (World Cup, Continental Cup, Qualifiers)
        intl_tourn = self.intl_engine.simulate_summer_tournament(world)
        
        world.current_stage = 4
        
        user_p = world.get_user_player()
        user_nat_team = world.national_teams.get(user_p.country) if user_p and user_p.country in world.national_teams else None
        
        return {
            "stage": 3,
            "title": "Continental Champions Trophy & Summer International Championship",
            "season_year": world.current_season,
            "tournament_rounds": rounds_data,
            "winner_club": winner_club.model_dump(),
            "runner_up_club": world.clubs[runner_up_id].model_dump(),
            "tournament_history": world.tournament.past_winners[:10],
            "most_successful_club": world.tournament.most_successful_club,
            "international_tournament": intl_tourn.model_dump() if intl_tourn else None,
            "user_national_team": user_nat_team.model_dump() if user_nat_team else None,
            "user_player": user_p.model_dump() if user_p else None
        }

    # -------------------------------------------------------------
    # STAGE 4: AWARDS CEREMONY
    # -------------------------------------------------------------
    def _run_stage_4_awards_ceremony(self, world: WorldState) -> Dict[str, Any]:
        # Compute all 25 League awards, 5 Tournament awards, 5 Cross-League awards
        awards_record = self.award_sys.calculate_season_awards(
            world.current_season, world.leagues, world.clubs, world.players, world.tournament
        )
        world.active_awards = awards_record
        
        # Award League Champions Trophies
        from src.engine.models import MilestoneEvent
        for league in world.leagues.values():
            if league.standings:
                champion_club_id = league.standings[0].club_id
                champion_club = world.clubs[champion_club_id]
                champion_club.league_titles += 1
                champion_club.title_years.append(f"Season {world.current_season} ({league.name})")
                for pid in champion_club.player_ids:
                    if pid in world.players:
                        p = world.players[pid]
                        p.career_trophies += 1
                        p.milestones.append(MilestoneEvent(
                            season_year=world.current_season,
                            age=p.age,
                            category="trophy",
                            title=f"Won {league.name} Championship 🏆",
                            description=f"Crowned domestic league champion with {champion_club.name} ({league.standings[0].points} pts).",
                            club_name=champion_club.name
                        ))
                        
        world.current_stage = 5
        
        return {
            "stage": 4,
            "title": "Annual Awards Ceremony & Trophies",
            "season_year": world.current_season,
            "awards": awards_record.model_dump(),
            "user_awards": [
                aw.model_dump() for aw_list in awards_record.league_awards.values() for aw in aw_list 
                if aw.player_id == world.user_player_id
            ] + [
                aw.model_dump() for aw in awards_record.cross_league_awards 
                if aw.player_id == world.user_player_id
            ]
        }

    # -------------------------------------------------------------
    # STAGE 5: SEASON SUMMARY & CAREER REPORT
    # -------------------------------------------------------------
    def _run_stage_5_season_summary(self, world: WorldState) -> Dict[str, Any]:
        user = world.get_user_player()
        user_club = world.get_user_club()
        
        # Calculate market value and positional rank
        market_val = user.calculate_market_value() if user else 0
        peers = [p for p in world.players.values() if user and p.position == user.position]
        peers.sort(key=lambda p: p.overall_rating, reverse=True)
        pos_rank = (peers.index(user) + 1) if user and user in peers else 0
        
        # Living world headlines
        storylines = self.story_gen.generate_season_storylines(world)
        world.storylines = storylines
        
        world.current_stage = 6
        
        return {
            "stage": 5,
            "title": "Season Summary & Career Report",
            "season_year": world.current_season,
            "user_player": user.model_dump() if user else None,
            "user_club": user_club.model_dump() if user_club else None,
            "position_rank": pos_rank,
            "market_value_m": market_val,
            "storylines": storylines,
            "recent_milestones": [m.model_dump() for m in (user.milestones[-4:] if user else [])]
        }

    # -------------------------------------------------------------
    # STAGE 6: OFFSEASON OVERVIEW & CHOICES
    # -------------------------------------------------------------
    def _run_stage_6_offseason_choices(self, world: WorldState, user_choice: Optional[str] = None) -> Dict[str, Any]:
        # 1. Payouts (League + Tournament)
        self._distribute_season_payouts(world)
        
        # 2. Retirements (AI players)
        from src.engine.models.club import ClubLegend
        retired_count = 0
        for p in list(world.players.values()):
            if not p.is_user and not p.is_retired:
                if self.dev_engine.check_retirement(p):
                    p.is_retired = True
                    retired_count += 1
                    c = world.clubs.get(p.contract.club_id) if p.contract else None
                    if c and p.id in c.player_ids:
                        c.player_ids.remove(p.id)
                    # Archive notable veterans into Club Hall of Fame
                    if (p.career_goals >= 50 or p.career_matches >= 180 or p.overall_rating >= 82) and c:
                        start_yr = max(1, world.current_season - max(1, p.career_matches // 35))
                        c.legends.append(ClubLegend(
                            player_id=p.id,
                            name=p.name,
                            country=p.country,
                            position=p.position.value if hasattr(p.position, "value") else str(p.position),
                            years_active=f"Season {start_yr}–{world.current_season}",
                            matches=p.career_matches,
                            goals=p.career_goals,
                            assists=p.career_assists,
                            trophies=len([h for h in p.history if h.trophies_won]),
                            legacy_score=round(p.overall_rating * 0.5 + p.career_goals * 0.3 + p.career_matches * 0.1, 1)
                        ))
                    if p.id in world.free_agent_ids:
                        world.free_agent_ids.remove(p.id)
                    # Delete retired AI player from active registry to maintain fast throughput
                    del world.players[p.id]
                            
        # 3. Youth Intake (1 per club)
        for club in world.clubs.values():
            if len(club.player_ids) < 22:
                youth_p = self.youth_sys.generate_annual_intake(club)
                world.players[youth_p.id] = youth_p
                club.player_ids.append(youth_p.id)

        # 4. Generate transfer bids from interested suitors and renewal offers every offseason window
        user = world.get_user_player()
        user_offers: List[TransferBidOffer] = []
        
        if user and not user.is_retired:
            user_offers = self.transfer_market.generate_offers_for_user(
                user, world.clubs, world.leagues
            )
            world.pending_user_offers = user_offers

        user = world.get_user_player()
        user_club = world.get_user_club()
        league = world.leagues.get(user_club.league_id) if user_club else None

        # Build available sponsorships (all fictional brands)
        all_possible_sponsorships = [
            {
                "id": "spons_boot",
                "name": "⚡ AeroStrike Pro Footwear Partnership",
                "brand": "AeroStrike Athletic",
                "min_ovr": 70,
                "annual_payout": 1.5,
                "description": "Custom signature boot edition with worldwide marketing campaign."
            },
            {
                "id": "spons_watch",
                "name": "⌚ Chronos Geneva Horology Ambassador",
                "brand": "Chronos Haute Horlogerie",
                "min_ovr": 80,
                "annual_payout": 4.0,
                "description": "Featured in high-end global fashion and luxury timepieces campaigns."
            },
            {
                "id": "spons_global",
                "name": "🌐 OmniTech Global Brand Icon",
                "brand": "OmniTech Global Conglomerate",
                "min_ovr": 88,
                "annual_payout": 10.0,
                "description": "Prime digital and billboard campaign face across global metropolitan hubs."
            }
        ]

        active_deal_ids = [d.get("id") for d in (user.sponsorship_deals if user else [])]
        available_sponsorships = [
            s for s in all_possible_sponsorships 
            if s["id"] not in active_deal_ids and user and user.overall_rating >= s["min_ovr"]
        ]

        # Available properties, investments and facilities
        all_properties = [
            {
                "id": "prop_penthouse",
                "name": "🏢 Metropolitan Skyline Penthouse",
                "cost": 2.5,
                "description": "Panoramic skyline view, private infinity pool, and underground private garage."
            },
            {
                "id": "prop_villa",
                "name": "🏡 Azure Coastline Seaside Villa",
                "cost": 8.0,
                "description": "Expansive private retreat with direct coast access and supreme serenity."
            },
            {
                "id": "prop_lab",
                "name": "🧬 Biomechanic Cryo-Recovery Lab",
                "cost": 6.0,
                "description": "State-of-the-art hyperbaric chambers & physical therapists. Significantly decelerates veteran age decline (Ages 33+)."
            },
            {
                "id": "prop_foundation",
                "name": "⚽ Horizon Grassroots Football Foundation",
                "cost": 4.0,
                "description": "Charitable foundation funding youth soccer training and gear in your hometown."
            },
            {
                "id": "inv_vc",
                "name": "📈 Apex Venture Growth Capital Fund",
                "cost": 3.0,
                "description": "Direct equity investment in early-stage technology and sports innovation startups."
            },
            {
                "id": "inv_supercars",
                "name": "🏎️ Exotic High-Performance Hypercar Fleet",
                "cost": 1.8,
                "description": "Curated collection of bespoke track-ready and luxury grand tourer vehicles."
            }
        ]
        
        owned_props = user.properties if user else []
        available_properties = [
            p for p in all_properties 
            if p["name"] not in owned_props and (p["id"] != "prop_lab" or not getattr(user, 'has_private_lab', False))
        ]

        # Available Family Actions
        available_life_actions = []
        suggested_partner_name = "Elena Rossi"
        if user:
            suggested_partner_name = get_random_female_name_for_country(user.country, self.rng)[2]
            if user.relationship_status == "Single" and user.age >= 18:
                available_life_actions.append({
                    "action": "meet_partner",
                    "title": "💘 Meet Partner / Begin Dating",
                    "description": "Find a supportive partner to share your career journey and personal life."
                })
            elif user.relationship_status == "In a Relationship" and user.age >= 21:
                available_life_actions.append({
                    "action": "get_married",
                    "title": "💍 Wedding & Marriage",
                    "description": f"Celebrate wedding with {user.partner_name or 'your partner'} and build a long-term family foundation."
                })
            elif user.relationship_status == "Married" and user.age >= 23 and len(user.children) < 3:
                child_count = len(user.children)
                available_life_actions.append({
                    "action": "have_child",
                    "title": f"👶 Welcome Child #{child_count + 1}",
                    "description": "Celebrate the birth of a child into the family (future academy legacy!)."
                })

        lifestyle_data = {
            "net_worth": user.net_worth if user else 0.0,
            "annual_wage": user.annual_wage if user else 0.5,
            "relationship_status": user.relationship_status if user else "Single",
            "partner_name": user.partner_name if user else None,
            "partner_backstory": getattr(user, 'partner_backstory', None) if user else None,
            "partner_origin_story": getattr(user, 'partner_origin_story', None) if user else None,
            "partner_meeting_year": getattr(user, 'partner_meeting_year', None) if user else None,
            "meeting_backstories": get_relationship_backstories(),
            "suggested_partner_name": suggested_partner_name,
            "children": user.children if user else [],
            "properties": user.properties if user else [],
            "has_private_lab": getattr(user, 'has_private_lab', False),
            "charities": user.charities if user else [],
            "sponsorship_deals": user.sponsorship_deals if user else [],
            "available_sponsorships": available_sponsorships,
            "available_properties": available_properties,
            "available_life_actions": available_life_actions
        }

        world.current_stage = 7

        return {
            "stage": 6,
            "title": "Offseason Overview & Contract Decisions",
            "season_year": world.current_season,
            "retired_players_count": retired_count,
            "user_player": user.model_dump() if user else None,
            "user_club": user_club.model_dump() if user_club else None,
            "league_name": league.name if league else "",
            "league_country": league.country if league else "",
            "user_offers": [o.model_dump() for o in user_offers],
            "needs_user_decision": len(user_offers) > 0,
            "lifestyle": lifestyle_data
        }

    # -------------------------------------------------------------
    # STAGE 7: TRANSFER WINDOW RESULTS
    # -------------------------------------------------------------
    def _run_stage_7_transfer_window(self, world: WorldState) -> Dict[str, Any]:
        # Process AI club signings adhering to 5-signings cap
        self.transfer_market.process_ai_transfer_window(
            world.clubs, world.players, world.free_agent_ids, world.current_season
        )
        
        # Ensure hard squad limits (18-22) and exact positional minimums (2 GK, 6 DEF, 6 MID, 4 FWD)
        self._stabilize_all_club_squads(world)

        world.current_stage = 8
        user = world.get_user_player()
        user_club = world.get_user_club()
        league = world.leagues.get(user_club.league_id) if user_club else None

        return {
            "stage": 7,
            "title": "Transfer Window Concluded",
            "season_year": world.current_season,
            "user_player": user.model_dump() if user else None,
            "user_club": user_club.model_dump() if user_club else None,
            "league_name": league.name if league else "",
            "league_country": league.country if league else "",
            "total_signings_by_club": {c.name: c.signings_this_window for c in world.clubs.values() if c.signings_this_window > 0}
        }

    # -------------------------------------------------------------
    # STAGE 8: NEW SEASON PREVIEW
    # -------------------------------------------------------------
    def _run_stage_8_new_season_preview(self, world: WorldState) -> Dict[str, Any]:
        user = world.get_user_player()
        user_prev_rating = user.overall_rating if user else 0
        user_season_goals = user.season_goals if user else 0
        user_season_assists = user.season_assists if user else 0
        user_season_matches = user.season_matches if user else 0
        
        # 1. Annual Development & Aging for all players
        user_dev_summary = "⚖️ Subdued Campaign (+0 OVR)"
        for p in world.players.values():
            if not p.is_retired:
                delta, summary = self.dev_engine.process_annual_development(p, world.current_season)
                p.age += 1
                if p.is_user:
                    user_dev_summary = summary
                if p.contract:
                    p.contract.years_remaining = max(0, p.contract.years_remaining - 1)
                    
        user_new_rating = user.overall_rating if user else 0
        user_rating_delta = user_new_rating - user_prev_rating
        dev_report = {
            "prev_rating": user_prev_rating,
            "new_rating": user_new_rating,
            "rating_delta": user_rating_delta,
            "review_summary": user_dev_summary,
            "season_goals": user_season_goals,
            "season_assists": user_season_assists,
            "season_matches": user_season_matches,
            "ga_total": user_season_goals + user_season_assists
        }

        # 2. Heal normal injuries
        self.injury_sys.heal_all_for_offseason(list(world.players.values()))
        
        # 3. Final stabilization check before season roll
        self._stabilize_all_club_squads(world)
        
        # 4. Record Season History Snapshot
        self._record_compact_history(world)
        
        # 5. Check User Retirement (Age >= 42 or user decision)
        if user and user.age >= 42:
            user.is_retired = True
            world.is_career_ended = True

        # 6. Validate Hard Invariants
        is_valid, errors = IntegrityValidator.validate_world_state(world)
        if not is_valid:
            raise WorldIntegrityError(f"Integrity check failed: {'; '.join(errors)}")

        # Advance Season and Reset Stage to 1
        from src.engine.models import SeasonStatRecord
        # Record detailed player season history
        for p in world.players.values():
            if not p.is_retired and (p.season_matches > 0 or p.is_user):
                p_club = world.clubs.get(p.contract.club_id) if p.contract else None
                p_trophies = []
                if p_club:
                    if world.tournament.winner_club_id == p_club.id:
                        p_trophies.append("Continental Champions Trophy 🏆")
                    p_league = world.leagues.get(p_club.league_id)
                    if p_league and p_league.standings and p_league.standings[0].club_id == p_club.id:
                        p_trophies.append(f"{p_league.name} Champion 🏆")
                
                p.history.append(SeasonStatRecord(
                    season_year=world.current_season,
                    club_id=p_club.id if p_club else "",
                    club_name=p_club.name if p_club else "Free Agent",
                    league_id=p_club.league_id if p_club else "",
                    matches_played=p.season_matches,
                    goals=p.season_goals,
                    assists=p.season_assists,
                    clean_sheets=p.season_clean_sheets,
                    saves=p.season_saves,
                    goals_conceded=p.season_goals_conceded,
                    average_rating=round(float(p.overall_rating), 1),
                    trophies_won=p_trophies,
                    awards_won=list(p.season_awards),
                    ending_rating=p.overall_rating,
                    market_value=p.calculate_market_value()
                ))

        world.current_season += 1
        world.current_stage = 1
        
        # Reset season stats on all players
        for p in world.players.values():
            p.reset_season_stats()

        return {
            "stage": 8,
            "title": f"Welcome to Season {world.current_season}",
            "season_year": world.current_season,
            "user_player": user.model_dump() if user else None,
            "user_club": world.get_user_club().model_dump() if world.get_user_club() else None,
            "development_report": dev_report,
            "is_career_ended": world.is_career_ended
        }

    # -------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------
    def _update_league_standings(self, league: League, clubs: Dict[str, Club]):
        standings: List[LeagueStanding] = []
        for cid in league.club_ids:
            c = clubs[cid]
            standings.append(LeagueStanding(
                club_id=c.id,
                club_name=c.name,
                played=38,
                won=c.league_wins,
                drawn=c.league_draws,
                lost=c.league_losses,
                goals_for=c.league_goals_for,
                goals_against=c.league_goals_against,
                goal_difference=c.goal_difference,
                points=c.league_points
            ))
        # Sort by points desc, goal difference desc, goals for desc
        standings.sort(key=lambda s: (s.points, s.goal_difference, s.goals_for), reverse=True)
        league.standings = standings
        
        # Update last_season_rank and recent_ranks on club
        for idx, s in enumerate(standings):
            c = clubs[s.club_id]
            c.last_season_rank = idx + 1
            c.recent_ranks.append(idx + 1)
            if len(c.recent_ranks) > 5:
                c.recent_ranks.pop(0)

    def _distribute_season_payouts(self, world: WorldState):
        """
        Annual Operating Budget Distribution (No Carry-Over):
        Each season, club budgets are reset to the sum of:
        1. League Finishing Prize Money: 1st (400M), 2-4th (200M), 5-10th (60M), 11-20th (20M)
        2. Continental Tournament Prize: winner (300M), runner-up (150M), SF exits (75M), QF exits (40M)
        3. Tier Commercial Baseline:
           - Tier 1 Giant: +90M baseline (Floor: 80M)
           - Tier 2 Challenger: +55M baseline (Floor: 45M)
           - Tier 3 Mid-Table: +35M baseline (Floor: 25M)
           - Tier 4 Underdog: +20M baseline (Floor: 15M)
        15% is automatically deducted for stadium & academy infrastructure maintenance.
        """
        # Reset club budgets annually to prevent runaway multi-decade carry-over
        for club in world.clubs.values():
            club.budget = 0

        # 1. Domestic League Prize Payouts
        for league in world.leagues.values():
            for idx, standing in enumerate(league.standings):
                rank = idx + 1
                club = world.clubs[standing.club_id]
                if rank == 1:
                    payout = 400
                elif rank <= 4:
                    payout = 200
                elif rank <= 10:
                    payout = 60
                else:
                    payout = 15
                infra_cut = int(payout * 0.15)
                club.budget += (payout - infra_cut)

        # 2. Continental Tournament Prize Payouts
        if world.tournament:
            for round_name, m_list in world.tournament.rounds.items():
                for m in m_list:
                    w_id = m.winner_club_id
                    loser_id = m.away_club_id if w_id == m.home_club_id else m.home_club_id
                    
                    if round_name == "Final":
                        if w_id and w_id in world.clubs:
                            world.clubs[w_id].budget += int(300 * 0.85) # Champion (300M - 15% infra)
                        if loser_id in world.clubs:
                            world.clubs[loser_id].budget += int(150 * 0.85) # Runner-up (150M - 15% infra)
                    elif round_name == "Semi-Finals":
                        if loser_id in world.clubs:
                            world.clubs[loser_id].budget += int(75 * 0.85) # SF exit (75M - 15% infra)
                    elif round_name == "Quarter-Finals":
                        if loser_id in world.clubs:
                            world.clubs[loser_id].budget += int(40 * 0.85) # QF exit (40M - 15% infra)
                    elif round_name == "Round of 16":
                        if loser_id in world.clubs:
                            world.clubs[loser_id].budget += int(30 * 0.85) # R16 exit (30M - 15% infra)
                    elif round_name == "Round of 32":
                        if loser_id in world.clubs:
                            world.clubs[loser_id].budget += int(20 * 0.85) # R32 exit (20M - 15% infra)

        # 3. Commercial Sponsorship Baseline & Prestige Safety Net Floors based on canonical tier_number
        tier_baseline_map = {1: (90, 80), 2: (55, 45), 3: (35, 25), 4: (20, 15)}
        for club in world.clubs.values():
            comm_base, budget_floor = tier_baseline_map.get(club.tier_number, (20, 15))
            club.budget += comm_base
            if club.budget < budget_floor:
                club.budget = budget_floor
                
            # Credit accumulated transfer compensation fees on top of baseline/floor
            if getattr(club, "pending_transfer_compensation", 0) > 0:
                club.budget += club.pending_transfer_compensation
                club.pending_transfer_compensation = 0
                
            # Infrastructure upgrade and multi-decade depreciation logic
            if club.infrastructure_level < 5 and club.budget >= 120:
                club.infrastructure_level += 1
                club.budget -= 80
                club.seasons_since_infra_upgrade = 0
            else:
                club.seasons_since_infra_upgrade = getattr(club, "seasons_since_infra_upgrade", 0) + 1
                # Multi-decade depreciation: decay 1 level every 15 seasons without investment (floor 1)
                if club.seasons_since_infra_upgrade >= 15:
                    if club.infrastructure_level > 1:
                        club.infrastructure_level -= 1
                    club.seasons_since_infra_upgrade = 0

        # 4. User Player Salary & Endorsement Earnings Payout
        user = world.get_user_player()
        if user and not user.is_retired:
            ovr = user.overall_rating
            if ovr < 65:
                base_salary = round(0.5 + (ovr - 50) * 0.05, 2)
            elif ovr < 75:
                base_salary = round(1.5 + (ovr - 65) * 0.25, 2)
            elif ovr < 85:
                base_salary = round(4.5 + (ovr - 75) * 0.65, 2)
            elif ovr < 92:
                base_salary = round(11.0 + (ovr - 85) * 1.5, 2)
            else:
                base_salary = round(22.0 + (ovr - 92) * 2.5, 2)
            
            user.annual_wage = base_salary
            earnings = base_salary
            
            # Sponsorship income
            sponsorship_income = sum(deal.get("annual_payout", 0.0) for deal in getattr(user, "sponsorship_deals", []))
            earnings += sponsorship_income
            
            # Venture Capital investment returns (variable with negative years possible)
            user_props = getattr(user, "properties", [])
            has_vc = any("Venture" in p or "inv_vc" in p for p in user_props)
            if has_vc:
                vc_return = round(self.rng.uniform(-0.35, 0.65), 2)
                earnings += vc_return
            
            # Silverware bonuses
            user_club = world.get_user_club()
            if user_club:
                if world.tournament and world.tournament.winner_club_id == user_club.id:
                    earnings += round(base_salary * 0.25, 2)
                league = world.leagues.get(user_club.league_id)
                if league and league.standings and league.standings[0].club_id == user_club.id:
                    earnings += round(base_salary * 0.25, 2)
                    
            user.net_worth = max(0.0, round(user.net_worth + earnings, 2))

    def _get_world_top_scorers(self, world: WorldState) -> List[Dict[str, Any]]:
        all_players = list(world.players.values())
        all_players.sort(key=lambda p: (p.season_goals, p.season_assists), reverse=True)
        return [
            {
                "name": p.name,
                "club_name": p.contract.club_name if p.contract else "Free Agent",
                "goals": p.season_goals,
                "assists": p.season_assists,
                "matches": p.season_matches
            }
            for p in all_players[:10]
        ]

    def _record_compact_history(self, world: WorldState):
        champs: Dict[str, str] = {}
        for lid, l in world.leagues.items():
            if l.standings:
                champs[l.name] = l.standings[0].club_name
                
        user = world.get_user_player()
        user_summary = {
            "age": user.age,
            "overall_rating": user.overall_rating,
            "season_goals": user.season_goals,
            "season_assists": user.season_assists,
            "club_name": user.contract.club_name if user.contract else "Free Agent"
        } if user else None

        world.history.append(CompactSeasonHistory(
            season_year=world.current_season,
            league_champions=champs,
            tournament_champion=world.clubs[world.tournament.winner_club_id].name if world.tournament.winner_club_id in world.clubs else "",
            ballon_dor_winner=world.active_awards.ballon_dor_winner.player_name if world.active_awards and world.active_awards.ballon_dor_winner else "",
            international_champion=world.active_international_tournament.winner_country if world.active_international_tournament else None,
            user_player_summary=user_summary
        ))

    def _stabilize_all_club_squads(self, world: WorldState):
        """
        Guarantees all 100 clubs strictly adhere to:
        1. No player registered in multiple clubs.
        2. Positional minimums: min 2 GK, 6 DEF, 6 MID, 4 FWD.
        3. Squad size limits: min 18, max 22.
        """
        # Step 0: Resolve cross-club duplicate registrations
        player_assigned_club = {} # player_id -> club_id
        for cid, club in list(world.clubs.items()):
            club.player_ids = list(dict.fromkeys(club.player_ids)) # Deduplicate internally
            
        for cid, club in list(world.clubs.items()):
            valid_pids = []
            for pid in club.player_ids:
                if pid not in world.players or world.players[pid].is_retired:
                    continue
                p = world.players[pid]
                contracted_cid = p.contract.club_id if p.contract else cid
                if pid in player_assigned_club:
                    # Conflict detected: assign strictly to their contracted club
                    if contracted_cid == cid:
                        prev_cid = player_assigned_club[pid]
                        if prev_cid in world.clubs and pid in world.clubs[prev_cid].player_ids:
                            world.clubs[prev_cid].player_ids.remove(pid)
                        player_assigned_club[pid] = cid
                        valid_pids.append(pid)
                    else:
                        continue # Skip duplicate in this club
                else:
                    player_assigned_club[pid] = cid
                    valid_pids.append(pid)
            club.player_ids = valid_pids

        for club in world.clubs.values():
            squad_players = [world.players[pid] for pid in club.player_ids if pid in world.players]
            
            gk_count = sum(1 for p in squad_players if p.position == Position.GK)
            def_count = sum(1 for p in squad_players if p.position == Position.DEF)
            mid_count = sum(1 for p in squad_players if p.position == Position.MID)
            fwd_count = sum(1 for p in squad_players if p.position == Position.FWD)
            
            # 1. Fill GKs if < 2
            while gk_count < 2:
                youth = self.youth_sys.generate_annual_intake(club, target_position=Position.GK)
                world.players[youth.id] = youth
                club.player_ids.append(youth.id)
                squad_players.append(youth)
                gk_count += 1
                
            # 2. Fill DEFs if < 6
            while def_count < 6:
                youth = self.youth_sys.generate_annual_intake(club, target_position=Position.DEF)
                world.players[youth.id] = youth
                club.player_ids.append(youth.id)
                squad_players.append(youth)
                def_count += 1
                
            # 3. Fill MIDs if < 6
            while mid_count < 6:
                youth = self.youth_sys.generate_annual_intake(club, target_position=Position.MID)
                world.players[youth.id] = youth
                club.player_ids.append(youth.id)
                squad_players.append(youth)
                mid_count += 1
                
            # 4. Fill FWDs if < 4
            while fwd_count < 4:
                youth = self.youth_sys.generate_annual_intake(club, target_position=Position.FWD)
                world.players[youth.id] = youth
                club.player_ids.append(youth.id)
                squad_players.append(youth)
                fwd_count += 1
                
            # 5. Fill to min 18 if still below
            while len(club.player_ids) < 18:
                youth = self.youth_sys.generate_annual_intake(club)
                world.players[youth.id] = youth
                club.player_ids.append(youth.id)
                squad_players.append(youth)
                
            # 6. Trim if > 22 (trim lowest-rated non-starter, non-user surplus players)
            while len(club.player_ids) > 22:
                non_user_players = [
                    world.players[pid] for pid in club.player_ids 
                    if pid in world.players and not world.players[pid].is_user
                ]
                if not non_user_players:
                    break
                to_remove = None
                for candidate in sorted(non_user_players, key=lambda p: p.overall_rating):
                    cand_pos = candidate.position
                    pos_count = sum(1 for p in squad_players if p.position == cand_pos)
                    min_req = 2 if cand_pos == Position.GK else (6 if cand_pos in [Position.DEF, Position.MID] else 4)
                    if pos_count > min_req:
                        to_remove = candidate
                        break
                        
                if to_remove:
                    club.player_ids.remove(to_remove.id)
                    squad_players.remove(to_remove)
                    world.free_agent_ids.append(to_remove.id)
                    to_remove.contract = None
                else:
                    break
