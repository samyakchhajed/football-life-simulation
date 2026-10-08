import random
from typing import Optional, List, Tuple
from src.engine.models import Player, Position, MilestoneEvent

class DevelopmentEngine:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def process_annual_development(self, player: Player, current_season: int) -> Tuple[int, str]:
        """
        Processes annual attribute progression or decline based strictly on
        on-pitch performance (Goals + Assists for FWD, G+A/Matches for MID/DEF/GK).
        Returns a tuple of (rating_delta, summary_reason).
        """
        old_rating = player.overall_rating
        age = player.age
        
        # Heavy injury penalty during development
        if player.injury.is_career_threatening:
            injury_penalty = self.rng.randint(6, 12)
            player.overall_rating = max(45, player.overall_rating - injury_penalty)
            player.milestones.append(MilestoneEvent(
                season_year=current_season,
                age=age,
                category="injury",
                title="Career-Threatening Injury Impact",
                description=f"Suffered a severe injury causing an attribute drop of -{injury_penalty} rating.",
                club_name=player.contract.club_name if player.contract else "Free Agent"
            ))
            self._sync_attributes(player)
            delta = player.overall_rating - old_rating
            return delta, f"🚑 Severe Injury Setback ({delta} OVR)"

        ga = player.season_goals + player.season_assists
        matches = player.season_matches
        cs = player.season_clean_sheets
        raw_growth = 0
        
        # 1. Performance evaluation based on position
        if player.position == Position.FWD:
            if ga >= 26:
                raw_growth = 5
            elif ga >= 16:
                raw_growth = 3
            elif ga >= 8:
                raw_growth = 1
            else:
                raw_growth = 0
        elif player.position == Position.MID:
            if ga >= 20 or (ga >= 14 and matches >= 30):
                raw_growth = 5
            elif ga >= 12 or (ga >= 8 and matches >= 25):
                raw_growth = 3
            elif ga >= 6 or (ga >= 4 and matches >= 20):
                raw_growth = 1
            else:
                raw_growth = 0
        else: # DEF and GK (Clean sheets + matches required)
            if matches >= 30 and cs >= 13:
                raw_growth = 5
            elif matches >= 25 and cs >= 8:
                raw_growth = 3
            elif matches >= 18 and cs >= 4:
                raw_growth = 1
            else:
                raw_growth = 0

        # 2. Rating-Tier Resistance & Diminishing Returns
        # It gets progressively harder to gain overall rating as players reach higher tiers
        tier_max_growth = 5
        if old_rating >= 92:
            tier_max_growth = 1 if (ga >= 30 or cs >= 16) else 0  # God-Level bottleneck
        elif old_rating >= 85:
            tier_max_growth = 1 if raw_growth >= 3 else 0         # World-Class resistance (max +1)
        elif old_rating >= 78:
            tier_max_growth = min(2, raw_growth)                   # Elite tier (max +2)
        elif old_rating >= 70:
            tier_max_growth = min(3, raw_growth)                   # Established tier (max +3)
        else:
            tier_max_growth = raw_growth                           # Youth / Emerging tier (up to +5)

        # 3. Age-based development phases
        if age <= 23:
            # Youth & Wonderkid phase: potential gap allows full earned growth
            effective_growth = min(raw_growth, tier_max_growth)
            gap = player.potential - player.overall_rating
            if gap > 0:
                growth = min(effective_growth, gap)
            elif ga >= 25 and player.overall_rating < 100:
                growth = min(effective_growth, 1) # Breakthrough beyond initial potential
            else:
                growth = 0
        elif age <= 27:
            # Prime development phase: stricter progression towards peak
            effective_growth = min(raw_growth, tier_max_growth, 3)
            gap = player.potential - player.overall_rating
            if gap > 0:
                growth = min(effective_growth, gap)
            elif ga >= 30 and player.overall_rating < 100:
                growth = min(effective_growth, 1)
            else:
                growth = 0
        elif age <= 30:
            # Prime Plateau (Age 28-30): Growth is rare (max +1) only on stellar seasons
            if (ga >= 28 or (cs >= 15 and matches >= 32)) and player.overall_rating < player.potential:
                growth = min(1, tier_max_growth)
            else:
                growth = 0
        elif age <= 32:
            # Early Veteran Plateau (Age 31-32): High performance maintains peak; otherwise slight drop
            growth = 0
            if ga >= 16 or (matches >= 28 and cs >= 9) or old_rating >= 88:
                return 0, "🛡️ Prime Form Maintained (+0 OVR)"
            elif self.rng.random() < 0.35:
                drop = 1
                player.overall_rating = max(50, player.overall_rating - drop)
                player.physical = max(35, player.physical - 1)
                self._sync_attributes(player)
                delta = player.overall_rating - old_rating
                return delta, f"⏳ Physical Pace Adjustment ({delta} OVR)"
            return 0, "🛡️ Peak Form Maintained (+0 OVR)"
        elif age <= 35:
            # Veteran decline phase (Age 33-35) - Slow graceful decrease (-1 OVR max)
            # Exceptional / Generational players maintain peak (+0 OVR)
            is_exceptional = (old_rating >= 85) or (ga >= 15) or (matches >= 25 and cs >= 8) or (player.career_ballon_dors > 0)
            has_lab = getattr(player, 'has_private_lab', False)
            
            if is_exceptional:
                # Exceptional veterans have world-class technique and longevity
                if ga >= 12 or (matches >= 20 and cs >= 6) or old_rating >= 88:
                    drop = 0
                else:
                    drop = 1 if self.rng.random() < (0.20 if has_lab else 0.40) else 0
            else:
                # Normal player: slow decrease of at most 1 OVR (35% chance to hold form on good season)
                if ga >= 10 or (matches >= 25 and cs >= 6):
                    drop = 0 if self.rng.random() < (0.60 if has_lab else 0.35) else 1
                else:
                    drop = 0 if (has_lab and self.rng.random() < 0.45) else 1

            if drop > 0:
                player.overall_rating = max(40, player.overall_rating - drop)
                player.physical = max(30, player.physical - 1)
                player.attacking = max(30, player.attacking - drop)
                player.defending = max(30, player.defending - drop)
                self._sync_attributes(player)
                delta = player.overall_rating - old_rating
                if is_exceptional:
                    return delta, f"🛡️ Veteran Experience Adjustment ({delta} OVR)"
                return delta, f"⏳ Veteran Age Decline ({delta} OVR)"
            return 0, "🛡️ Elite Veteran Longevity (+0 OVR)"
        else:
            # Late career phase (Age 36+) - Slow graceful decline (-1 to -2 OVR max)
            is_exceptional = (old_rating >= 85) or (ga >= 12) or (matches >= 25 and cs >= 7) or (player.career_ballon_dors > 0)
            has_lab = getattr(player, 'has_private_lab', False)
            
            if is_exceptional:
                # Exceptional superstars drop at most 0 to 1 OVR well into late 30s
                if ga >= 10 or (matches >= 20 and cs >= 5) or old_rating >= 90:
                    drop = 0 if self.rng.random() < (0.75 if has_lab else 0.50) else 1
                else:
                    drop = 0 if (has_lab and self.rng.random() < 0.40) else 1
            else:
                # Normal veterans: slow drop of 1 OVR (2 OVR only if age >= 39 and very quiet season)
                if age >= 39 and ga < 5 and cs < 3 and self.rng.random() < (0.30 if has_lab else 0.60):
                    drop = 2
                else:
                    drop = 0 if (has_lab and self.rng.random() < 0.35) else 1

            if drop > 0:
                player.overall_rating = max(35, player.overall_rating - drop)
                player.physical = max(20, player.physical - drop)
                player.attacking = max(25, player.attacking - drop)
                player.playmaking = max(30, player.playmaking - max(0, drop - 1))
                self._sync_attributes(player)
                delta = player.overall_rating - old_rating
                if is_exceptional:
                    return delta, f"🛡️ Legendary Longevity ({delta} OVR)"
                return delta, f"📉 Late Career Physical Decline ({delta} OVR)"
            return 0, "🛡️ Legendary Longevity (+0 OVR)"

        # Apply growth for young / prime players
        if growth > 0:
            player.overall_rating = min(100, player.overall_rating + growth)
            self._distribute_growth(player, growth)

        self._sync_attributes(player)
        delta = player.overall_rating - old_rating
        
        gap = player.potential - old_rating
        if delta >= 4:
            summary = f"⭐ Explosive Breakthrough (+{delta} OVR Jump)"
        elif delta >= 2:
            summary = f"🔥 Stellar Campaign (+{delta} OVR Jump)"
        elif delta >= 1:
            if gap <= 0:
                summary = "🌟 Potential Breakthrough (+1 OVR Jump)"
            else:
                summary = "📈 Solid Development (+1 OVR Jump)"
        else:
            if raw_growth > 0 and (gap <= 0 or tier_max_growth == 0):
                summary = "⚖️ Potential Ceiling Reached (+0 OVR)"
            else:
                summary = "⚖️ Subdued Campaign (+0 OVR)"
        return delta, summary

    def check_retirement(self, player: Player) -> bool:
        """
        Determines if a player retires at the end of the season.
        Retirement probability rises sharply from mid-30s.
        Mandatory retirement at age 42.
        """
        age = player.age
        if age < 33:
            return False
        if age >= 41:
            return True
            
        prob_map = {
            33: 0.04,
            34: 0.09,
            35: 0.18,
            36: 0.35,
            37: 0.55,
            38: 0.75,
            39: 0.88,
            40: 0.95
        }
        
        prob = prob_map.get(age, 0.95)
        # Rating factor: low rating players retire earlier
        if player.overall_rating < 65:
            prob += 0.20
        return self.rng.random() < prob

    def _distribute_growth(self, player: Player, amount: int):
        if player.position == Position.FWD:
            player.attacking = min(100, player.attacking + amount)
            player.physical = min(100, player.physical + max(0, amount - 1))
            player.playmaking = min(100, player.playmaking + max(0, amount - 2))
        elif player.position == Position.MID:
            player.playmaking = min(100, player.playmaking + amount)
            player.attacking = min(100, player.attacking + max(0, amount - 1))
            player.defending = min(100, player.defending + max(0, amount - 1))
        elif player.position == Position.DEF:
            player.defending = min(100, player.defending + amount)
            player.physical = min(100, player.physical + max(0, amount - 1))
        else: # GK
            player.defending = min(100, player.defending + amount)
            player.physical = min(100, player.physical + max(0, amount - 1))

    def _sync_attributes(self, player: Player):
        player.overall_rating = max(35, min(100, player.overall_rating))
        player.attacking = max(20, min(100, player.attacking))
        player.playmaking = max(20, min(100, player.playmaking))
        player.defending = max(20, min(100, player.defending))
        player.physical = max(20, min(100, player.physical))
