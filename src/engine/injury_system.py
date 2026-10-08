import random
from typing import Optional, List
from src.engine.models import Player, InjuryState, InjurySeverity

class InjurySystem:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def process_match_injuries(self, players: List[Player]):
        """
        Evaluates injury rolls for participating players in a match week.
        Decrements weeks remaining and protection periods for injured/recovering players.
        """
        for p in players:
            # Handle active injury countdown
            if p.injury.weeks_remaining > 0:
                p.injury.weeks_remaining -= 1
                if p.injury.weeks_remaining == 0:
                    # Injury healed, activate protection period
                    p.injury.severity = InjurySeverity.NONE
                    p.injury.protection_weeks_remaining = 4
                continue
                
            # Handle protection countdown
            if p.injury.protection_weeks_remaining > 0:
                p.injury.protection_weeks_remaining -= 1
                continue
                
            # Roll for new injury during match play
            # Baseline injury chance ~ 2.5% per match per active player
            base_risk = 0.025
            
            # Age modifier (rises after 30)
            if p.age >= 30:
                base_risk += (p.age - 29) * 0.005
                
            # Physical attribute mitigation
            physical_mitigation = (100 - p.physical) * 0.0003
            total_risk = max(0.008, base_risk + physical_mitigation)
            
            if self.rng.random() < total_risk:
                self._apply_new_injury(p)

    def _apply_new_injury(self, player: Player):
        roll = self.rng.random()
        
        # Rare life-threatening (0.2% of injuries)
        if roll < 0.002:
            player.injury = InjuryState(
                severity=InjurySeverity.CAREER_THREAT,
                description="Severe Spinal / Cardiac Complication",
                weeks_remaining=12,
                protection_weeks_remaining=8,
                is_career_threatening=True
            )
            return
            
        # Heavy: 9-12 weeks (~10% of injuries)
        if roll < 0.10:
            duration = self.rng.randint(9, 12)
            player.injury = InjuryState(
                severity=InjurySeverity.HEAVY,
                description="Cruciate Ligament Tear",
                weeks_remaining=duration,
                protection_weeks_remaining=4
            )
        # Medium: 4-8 weeks (~35% of injuries)
        elif roll < 0.45:
            duration = self.rng.randint(4, 8)
            player.injury = InjuryState(
                severity=InjurySeverity.MEDIUM,
                description="Hamstring / Ankle Strain",
                weeks_remaining=duration,
                protection_weeks_remaining=3
            )
        # Small: 1-3 weeks (~55% of injuries)
        else:
            duration = self.rng.randint(1, 3)
            player.injury = InjuryState(
                severity=InjurySeverity.SMALL,
                description="Minor Muscle Knock",
                weeks_remaining=duration,
                protection_weeks_remaining=2
            )

    def heal_all_for_offseason(self, players: List[Player]):
        """Heals all non-career-threatening injuries at the close of the season"""
        for p in players:
            if not p.injury.is_career_threatening:
                p.injury = InjuryState()
