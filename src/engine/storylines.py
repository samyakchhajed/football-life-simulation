import random
from typing import List, Dict, Optional
from src.engine.models import WorldState, Player, Club, League, Position

class StorylineGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate_season_storylines(self, world: WorldState) -> List[str]:
        """
        Generates living world news headlines and narrative arcs based on
        actual simulated events across the season.
        """
        headlines: List[str] = []
        user = world.get_user_player()
        
        # 1. User Season Headline
        if user and user.contract:
            club_name = user.contract.club_name
            if user.season_goals >= 25:
                headlines.append(f"⭐ Unstoppable: {user.name} lights up the season with a stunning {user.season_goals} goal haul for {club_name}!")
            elif user.season_clean_sheets >= 14:
                headlines.append(f"🛡️ Wall of Steel: {user.name} anchors {club_name}'s backline with {user.season_clean_sheets} clean sheets!")
            elif user.season_assists >= 15:
                headlines.append(f"🎯 Visionary: {user.name} orchestrates {club_name}'s attack with {user.season_assists} masterclass assists.")
            elif user.season_matches > 30:
                headlines.append(f"📊 Consistent Force: {user.name} completes another dependable campaign at {club_name}.")

        # 2. Rivalry Dynamics
        rival_headline = self._check_rivalry(world)
        if rival_headline:
            headlines.append(rival_headline)
            
        # 3. Fallen Giants (Former champions falling out of top 4)
        for league in world.leagues.values():
            for standing in league.standings:
                club = world.clubs.get(standing.club_id)
                if club and club.league_titles >= 2 and league.standings.index(standing) >= 10:
                    headlines.append(f"📉 Crisis at {club.name}: Traditional powerhouse slumps to a shocking #{league.standings.index(standing)+1} finish.")
                    break
                    
        # 4. Wonderkid Breakthroughs (Age <= 20 with high rating / goals)
        young_stars = [
            p for p in world.players.values() 
            if p.age <= 20 and (p.season_goals >= 15 or p.overall_rating >= 80)
        ]
        if young_stars:
            chosen_star = self.rng.choice(young_stars)
            club_name = chosen_star.contract.club_name if chosen_star.contract else "Top Flight"
            headlines.append(f"🌟 Wonderkid Sensation: 20-year-old {chosen_star.name} emerges as a global superstar at {club_name}!")

        # 5. Continental Champions Glory
        if world.tournament.winner_club_id and world.tournament.winner_club_id in world.clubs:
            winner = world.clubs[world.tournament.winner_club_id]
            headlines.append(f"🏆 Continental Immortality: {winner.name} crowned champions of the Continental Champions Trophy!")
            
        # 6. Rebuilding Club Resurgence
        for club in world.clubs.values():
            if club.signings_this_window >= 3 and club.last_season_rank <= 5:
                headlines.append(f"🚀 Rebuilding Triumph: Strategic transfer investments propel {club.name} into the elite tier.")
                break

        return headlines[:6]

    def _check_rivalry(self, world: WorldState) -> Optional[str]:
        user = world.get_user_player()
        if not user:
            return None
            
        # Find top peer in user's position
        peers = [
            p for p in world.players.values() 
            if p.id != user.id and p.position == user.position and not p.is_retired
        ]
        if not peers:
            return None
            
        top_peer = max(peers, key=lambda p: p.overall_rating)
        
        # If user and top peer are both elite (80+) and close in rating (within 4)
        if user.overall_rating >= 78 and abs(user.overall_rating - top_peer.overall_rating) <= 5:
            user_goals = user.season_goals
            peer_goals = top_peer.season_goals
            peer_club = top_peer.contract.club_name if top_peer.contract else "Rivals"
            
            if user.position == Position.FWD:
                return f"🔥 The Great Rivalry: {user.name} ({user_goals}G) and {top_peer.name} ({peer_goals}G, {peer_club}) battle neck-and-neck for the crown."
            else:
                return f"⚔️ Position Titans: {user.name} and {top_peer.name} ({peer_club}) duel for supremacy as the world's finest {user.position.value}."
        return None
