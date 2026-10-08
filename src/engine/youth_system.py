import random
from typing import Optional, List, Dict
from src.engine.models import Player, Club, Position, Contract
from src.engine.names_database import get_random_name_for_country
from src.engine.traits import assign_initial_traits

class YouthAcademySystem:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate_annual_intake(self, club: Club, target_position: Optional[Position] = None) -> Player:
        """
        Generates 1 youth player (age 17) for a club.
        Club infrastructure level (1-5) boosts potential and starting rating.
        """
        _, _, name = get_random_name_for_country(club.country, self.rng)
        pos = target_position or self.rng.choice([Position.GK, Position.DEF, Position.MID, Position.FWD])
        
        # Base potential by infrastructure level (1-5)
        infra_min_pot = 66 + (club.infrastructure_level * 3)
        infra_max_pot = 76 + (club.infrastructure_level * 4)
        potential = min(100, self.rng.randint(infra_min_pot, infra_max_pot))
        
        # Rare super-wonderkid roll (2% chance)
        if self.rng.random() < 0.02:
            potential = min(100, potential + self.rng.randint(5, 10))
            
        # Starting rating at 17 is typically 50-65
        starting_rating = max(48, int(potential * self.rng.uniform(0.68, 0.76)))
        
        # Distribute attributes
        att = self.rng.randint(starting_rating - 6, starting_rating + 6)
        play = self.rng.randint(starting_rating - 6, starting_rating + 6)
        defe = self.rng.randint(starting_rating - 6, starting_rating + 6)
        phys = self.rng.randint(starting_rating - 4, starting_rating + 6)
        
        if pos == Position.FWD:
            att += 8
            defe -= 8
        elif pos == Position.MID:
            play += 8
        elif pos == Position.DEF or pos == Position.GK:
            defe += 8
            att -= 10
            
        traits = assign_initial_traits(
            pos,
            max(25, min(100, att)),
            max(25, min(100, play)),
            max(25, min(100, defe)),
            max(25, min(100, phys)),
            starting_rating,
            self.rng
        )
            
        contract = Contract(
            club_id=club.id,
            club_name=club.name,
            years_remaining=3,
            total_years=3
        )
        
        player = Player(
            name=name,
            country=club.country,
            age=17,
            position=pos,
            overall_rating=starting_rating,
            potential=potential,
            attacking=max(25, min(100, att)),
            playmaking=max(25, min(100, play)),
            defending=max(25, min(100, defe)),
            physical=max(25, min(100, phys)),
            contract=contract,
            traits=traits
        )
        return player
