import random
from typing import List, Dict, Tuple, Optional
from src.engine.models import Position, Player

POSITION_TRAITS_POOL: Dict[Position, List[str]] = {
    Position.FWD: [
        "🎯 Clinical Finisher",
        "🚀 Rapid Counter-Poacher",
        "🛡️ Target Man & Hold-Up",
        "👑 Big-Game Clutch DNA",
        "🌪️ Dribbling Maestro"
    ],
    Position.MID: [
        "🎩 Midfield Maestro",
        "⚡ Box-to-Box Engine",
        "🎯 Dead-Ball Specialist",
        "🌪️ Dribbling Wizard",
        "👑 Big-Game Clutch DNA"
    ],
    Position.DEF: [
        "🧱 Defensive Anchor",
        "✈️ Aerial Fortress",
        "⚡ Modern Ball-Playing CB",
        "🛡️ Sliding Tackler",
        "👑 Big-Game Clutch DNA"
    ],
    Position.GK: [
        "🧤 Acrobatic Wall",
        "🧠 Sweeper Keeper",
        "🎯 Penalty Specialist",
        "👑 Big-Game Clutch DNA"
    ]
}

def assign_initial_traits(
    position: Position,
    attacking: int,
    playmaking: int,
    defending: int,
    physical: int,
    overall_rating: int,
    rng: random.Random
) -> List[str]:
    """
    Assigns 1-2 authentic initial playstyle traits based on position and attribute profiles.
    """
    traits: List[str] = []
    
    if position == Position.FWD:
        if attacking >= 68 and rng.random() < 0.65:
            traits.append("🎯 Clinical Finisher")
        elif physical >= 65 and rng.random() < 0.60:
            traits.append("🛡️ Target Man & Hold-Up")
        elif playmaking >= 60 and rng.random() < 0.55:
            traits.append("🌪️ Dribbling Maestro")
        else:
            traits.append("🚀 Rapid Counter-Poacher")
            
        if overall_rating >= 80 and rng.random() < 0.45:
            traits.append("👑 Big-Game Clutch DNA")
            
    elif position == Position.MID:
        if playmaking >= 68 and rng.random() < 0.65:
            traits.append("🎩 Midfield Maestro")
        elif physical >= 65 and defending >= 60:
            traits.append("⚡ Box-to-Box Engine")
        elif attacking >= 62 and rng.random() < 0.50:
            traits.append("🎯 Dead-Ball Specialist")
        else:
            traits.append("🌪️ Dribbling Wizard")
            
        if overall_rating >= 80 and rng.random() < 0.45:
            traits.append("👑 Big-Game Clutch DNA")
            
    elif position == Position.DEF:
        if defending >= 68 and rng.random() < 0.65:
            traits.append("🧱 Defensive Anchor")
        elif physical >= 65 and rng.random() < 0.60:
            traits.append("✈️ Aerial Fortress")
        elif playmaking >= 58:
            traits.append("⚡ Modern Ball-Playing CB")
        else:
            traits.append("🛡️ Sliding Tackler")
            
        if overall_rating >= 80 and rng.random() < 0.45:
            traits.append("👑 Big-Game Clutch DNA")
            
    else: # GK
        if defending >= 68 and rng.random() < 0.65:
            traits.append("🧤 Acrobatic Wall")
        elif physical >= 65:
            traits.append("🧠 Sweeper Keeper")
        else:
            traits.append("🎯 Penalty Specialist")
            
        if overall_rating >= 80 and rng.random() < 0.45:
            traits.append("👑 Big-Game Clutch DNA")
            
    # Ensure maximum of 2 traits initially, no duplicates
    return list(dict.fromkeys(traits))[:2]
