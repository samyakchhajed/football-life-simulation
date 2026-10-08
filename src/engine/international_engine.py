import uuid
import random
from typing import Dict, List, Optional, Tuple, Any
from src.engine.models import (
    Player, Position, MilestoneEvent,
    NationalTeam, InternationalMatch, InternationalTournament
)
from src.engine.match_sim import poisson_sample

NATIONAL_TEAMS_CONFIG = [
    {"country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "pri": "#ffffff", "sec": "#dc2626", "fifa": 4, "wc": 1, "cont": 0},
    {"country": "Spain", "flag": "🇪🇸", "pri": "#dc2626", "sec": "#fbbf24", "fifa": 3, "wc": 1, "cont": 3},
    {"country": "Germany", "flag": "🇩🇪", "pri": "#ffffff", "sec": "#111827", "fifa": 5, "wc": 4, "cont": 3},
    {"country": "Italy", "flag": "🇮🇹", "pri": "#1d4ed8", "sec": "#ffffff", "fifa": 6, "wc": 4, "cont": 2},
    {"country": "France", "flag": "🇫🇷", "pri": "#1e3a8a", "sec": "#dc2626", "fifa": 2, "wc": 2, "cont": 2},
    {"country": "Brazil", "flag": "🇧🇷", "pri": "#fbbf24", "sec": "#15803d", "fifa": 1, "wc": 5, "cont": 9},
    {"country": "Argentina", "flag": "🇦🇷", "pri": "#38bdf8", "sec": "#ffffff", "fifa": 2, "wc": 3, "cont": 15},
    {"country": "USA", "flag": "🇺🇸", "pri": "#1e3a8a", "sec": "#dc2626", "fifa": 13, "wc": 0, "cont": 7},
    {"country": "Japan", "flag": "🇯🇵", "pri": "#1e3a8a", "sec": "#ffffff", "fifa": 15, "wc": 0, "cont": 4},
    {"country": "India", "flag": "🇮🇳", "pri": "#ea580c", "sec": "#15803d", "fifa": 85, "wc": 0, "cont": 0},
    {"country": "Netherlands", "flag": "🇳🇱", "pri": "#ea580c", "sec": "#ffffff", "fifa": 7, "wc": 0, "cont": 1},
    {"country": "Portugal", "flag": "🇵🇹", "pri": "#dc2626", "sec": "#15803d", "fifa": 8, "wc": 0, "cont": 1},
    {"country": "Belgium", "flag": "🇧🇪", "pri": "#dc2626", "sec": "#fbbf24", "fifa": 9, "wc": 0, "cont": 0},
    {"country": "Croatia", "flag": "🇭🇷", "pri": "#dc2626", "sec": "#ffffff", "fifa": 10, "wc": 0, "cont": 0},
    {"country": "Uruguay", "flag": "🇺🇾", "pri": "#38bdf8", "sec": "#111827", "fifa": 11, "wc": 2, "cont": 15},
    {"country": "Mexico", "flag": "🇲🇽", "pri": "#15803d", "sec": "#dc2626", "fifa": 14, "wc": 0, "cont": 8},
]

class InternationalEngine:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def initialize_national_teams(self) -> Dict[str, NationalTeam]:
        teams: Dict[str, NationalTeam] = {}
        for cfg in NATIONAL_TEAMS_CONFIG:
            t = NationalTeam(
                id=f"nat_{cfg['country'].lower().replace(' ', '_')}",
                country=cfg["country"],
                fifa_ranking=cfg["fifa"],
                flag_emoji=cfg["flag"],
                primary_color=cfg["pri"],
                secondary_color=cfg["sec"],
                world_cup_titles=cfg["wc"],
                continental_titles=cfg["cont"]
            )
            teams[cfg["country"]] = t
        return teams

    def select_national_rosters(self, national_teams: Dict[str, NationalTeam], players: Dict[str, Player], current_season: int):
        """
        Selects the top 23-man squad and Starting 11 for each active national team.
        """
        for country, nteam in national_teams.items():
            pool = [
                p for p in players.values() 
                if p.country.strip().lower() == country.strip().lower() and not p.is_retired
            ]
            if not pool:
                continue

            # Selection rating: smooth linear model (40% overall rating + continuous stat contribution)
            def _score(p: Player) -> float:
                base = p.overall_rating * 0.40
                if p.position == Position.FWD:
                    stat_points = (p.season_goals * 2.2) + (p.season_assists * 1.0)
                elif p.position == Position.MID:
                    stat_points = (p.season_assists * 2.2) + (p.season_goals * 1.4)
                elif p.position == Position.DEF:
                    stat_points = (p.season_clean_sheets * 2.5) + (p.season_goals * 1.0)
                else:  # GK
                    stat_points = (p.season_clean_sheets * 2.5) + (p.season_saves * 0.05)
                return base + stat_points

            gks = sorted([p for p in pool if p.position == Position.GK], key=_score, reverse=True)
            defs = sorted([p for p in pool if p.position == Position.DEF], key=_score, reverse=True)
            mids = sorted([p for p in pool if p.position == Position.MID], key=_score, reverse=True)
            fwds = sorted([p for p in pool if p.position == Position.FWD], key=_score, reverse=True)

            selected_squad: List[Player] = []
            selected_squad.extend(gks[:2])
            selected_squad.extend(defs[:7])
            selected_squad.extend(mids[:8])
            selected_squad.extend(fwds[:6])

            # Fill to 23 if needed
            selected_ids = [p.id for p in selected_squad]
            rem = [p for p in pool if p.id not in selected_ids]
            rem.sort(key=_score, reverse=True)
            while len(selected_ids) < 23 and rem:
                p_next = rem.pop(0)
                selected_squad.append(p_next)
                selected_ids.append(p_next.id)

            nteam.squad_player_ids = selected_ids

            # Select Starting XI (1 GK, 4 DEF, 4 MID, 2 FWD)
            starters: List[str] = []
            starters.extend([p.id for p in gks[:1]])
            starters.extend([p.id for p in defs[:4]])
            starters.extend([p.id for p in mids[:4]])
            starters.extend([p.id for p in fwds[:2]])
            nteam.starting_xi_ids = starters

            # Appoint Captain (highest caps / veteran in squad)
            if selected_squad:
                capt = max(selected_squad, key=lambda p: (p.international_caps, p.overall_rating))
                nteam.captain_player_id = capt.id
                capt.is_national_team_captain = True

            # Update player national team status & milestones
            for p in selected_squad:
                if p.is_national_team_captain:
                    p.national_team_status = "National Team Captain 🎖️"
                elif p.id in starters:
                    p.national_team_status = "Starting International ⭐"
                else:
                    p.national_team_status = "Squad Regular"

                if p.is_user and p.international_caps == 0:
                    p.milestones.append(MilestoneEvent(
                        season_year=current_season,
                        age=p.age,
                        category="national_team",
                        title=f"{country} Senior National Team Debut",
                        description=f"Received first senior international call-up for {country} at age {p.age}.",
                        club_name=p.contract.club_name if p.contract else "Free Agent"
                    ))

    def simulate_summer_tournament(self, world: Any) -> InternationalTournament:
        """
        Simulates the summer international tournament based on the 4-year cycle:
        Cycle 0: Global World Cup (16 Nations Knockout)
        Cycle 2: Continental Nations Cup
        Cycle 1, 3: International Qualifiers & Friendlies
        """
        if not world.national_teams:
            world.national_teams = self.initialize_national_teams()

        self.select_national_rosters(world.national_teams, world.players, world.current_season)

        cycle = world.current_season % 4
        if cycle == 0:
            tourn_name = "🌍 Global World Championship"
        elif cycle == 2:
            tourn_name = "🏆 Continental Nations Cup"
        elif cycle == 1:
            tourn_name = "🎖️ International Qualifiers & Summer Series"
        else:
            tourn_name = "🥇 Nations League Finals"

        tourn = InternationalTournament(
            id=f"intl_tourn_s{world.current_season}_c{cycle}",
            season_year=world.current_season,
            name=tourn_name,
            cycle_year=cycle if cycle != 0 else 4
        )

        active_nations = list(world.national_teams.keys())
        # Pick top 16 nations based on FIFA ranking
        sorted_nations = sorted(active_nations, key=lambda c: world.national_teams[c].fifa_ranking)
        qualified_16 = sorted_nations[:16]
        tourn.qualified_countries = qualified_16

        # Simulate Knockout: R16 -> QF -> SF -> Final
        current_round_countries = list(qualified_16)
        self.rng.shuffle(current_round_countries)
        
        round_names = ["Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
        
        while len(current_round_countries) > 1:
            round_idx = {16: 0, 8: 1, 4: 2, 2: 3}[len(current_round_countries)]
            r_name = round_names[min(len(round_names)-1, round_idx)]
            next_round_countries = []
            
            for i in range(0, len(current_round_countries), 2):
                if i + 1 >= len(current_round_countries):
                    next_round_countries.append(current_round_countries[i])
                    break
                
                c_home = current_round_countries[i]
                c_away = current_round_countries[i+1]
                
                match = self._simulate_international_match(
                    r_name, tourn_name, c_home, c_away, world.national_teams, world.players
                )
                tourn.matches.append(match)
                next_round_countries.append(match.winner_country)
                
                if r_name == "Final":
                    tourn.winner_country = match.winner_country
                    tourn.runner_up_country = c_away if match.winner_country == c_home else c_home
                    
            current_round_countries = next_round_countries

        # Award trophies & honors to champion squad
        if tourn.winner_country and tourn.winner_country in world.national_teams:
            champ_team = world.national_teams[tourn.winner_country]
            if cycle == 0:
                champ_team.world_cup_titles += 1
            else:
                champ_team.continental_titles += 1
            champ_team.past_honors.append(f"Season {world.current_season} — {tourn_name} Winner")

            for pid in champ_team.squad_player_ids:
                if pid in world.players:
                    p = world.players[pid]
                    trophy_title = f"{tourn_name} Champion"
                    p.international_trophies.append(trophy_title)
                    p.career_trophies += 1
                    if p.is_user:
                        p.milestones.append(MilestoneEvent(
                            season_year=world.current_season,
                            age=p.age,
                            category="trophy",
                            title=f"Won {trophy_title}!",
                            description=f"Led {tourn.winner_country} to international glory in the {tourn_name}.",
                            club_name=p.contract.club_name if p.contract else "Free Agent"
                        ))

        # Golden Boot & Best Player calculation
        all_tourn_scorers: Dict[str, int] = {}
        for m in tourn.matches:
            for s in m.scorers:
                pid = s.get("player_id", "")
                all_tourn_scorers[pid] = all_tourn_scorers.get(pid, 0) + 1

        if all_tourn_scorers:
            top_pid = max(all_tourn_scorers, key=all_tourn_scorers.get)
            if top_pid in world.players:
                top_p = world.players[top_pid]
                tourn.top_scorer_name = f"{top_p.name} ({all_tourn_scorers[top_pid]} Goals)"
                tourn.top_scorer_goals = all_tourn_scorers[top_pid]

        world.active_international_tournament = tourn
        world.international_history.insert(0, tourn)
        return tourn

    def _simulate_international_match(
        self,
        round_name: str,
        comp_name: str,
        home_country: str,
        away_country: str,
        n_teams: Dict[str, NationalTeam],
        players: Dict[str, Player]
    ) -> InternationalMatch:
        ht = n_teams[home_country]
        at = n_teams[away_country]

        h_starters = [players[pid] for pid in ht.starting_xi_ids if pid in players]
        a_starters = [players[pid] for pid in at.starting_xi_ids if pid in players]

        h_rating = sum(p.overall_rating for p in h_starters) / max(1, len(h_starters)) if h_starters else 70.0
        a_rating = sum(p.overall_rating for p in a_starters) / max(1, len(a_starters)) if a_starters else 70.0

        # International match caps recording
        for p in h_starters + a_starters:
            p.international_caps += 1

        delta = h_rating - a_rating
        h_lam = min(4.5, max(0.20, 1.35 + delta * 0.03))
        a_lam = min(4.5, max(0.20, 1.35 - delta * 0.03))

        h_goals = poisson_sample(h_lam, self.rng)
        a_goals = poisson_sample(a_lam, self.rng)

        scorers: List[Dict[str, str]] = []
        assisters: List[Dict[str, str]] = []

        # Assign home goals
        for _ in range(h_goals):
            scorer = self.rng.choice(h_starters) if h_starters else None
            if scorer:
                scorer.international_goals += 1
                scorers.append({"player_id": scorer.id, "player_name": scorer.name, "country": home_country})
                assister = self.rng.choice([p for p in h_starters if p.id != scorer.id]) if len(h_starters) > 1 else None
                if assister:
                    assister.international_assists += 1
                    assisters.append({"player_id": assister.id, "player_name": assister.name, "country": home_country})

        # Assign away goals
        for _ in range(a_goals):
            scorer = self.rng.choice(a_starters) if a_starters else None
            if scorer:
                scorer.international_goals += 1
                scorers.append({"player_id": scorer.id, "player_name": scorer.name, "country": away_country})
                assister = self.rng.choice([p for p in a_starters if p.id != scorer.id]) if len(a_starters) > 1 else None
                if assister:
                    assister.international_assists += 1
                    assisters.append({"player_id": assister.id, "player_name": assister.name, "country": away_country})

        pen_winner = None
        winner = home_country
        if h_goals > a_goals:
            winner = home_country
        elif a_goals > h_goals:
            winner = away_country
        else:
            # Penalty shootout
            if self.rng.random() < (0.50 + delta * 0.01):
                winner = home_country
                pen_winner = home_country
            else:
                winner = away_country
                pen_winner = away_country

        return InternationalMatch(
            id=f"intl_{comp_name}_{round_name}_{home_country}_{away_country}",
            round_name=round_name,
            competition_name=comp_name,
            home_country=home_country,
            away_country=away_country,
            home_goals=h_goals,
            away_goals=a_goals,
            penalty_winner_country=pen_winner,
            winner_country=winner,
            scorers=scorers,
            assisters=assisters
        )
