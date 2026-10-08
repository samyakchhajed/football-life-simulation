from typing import List, Dict, Tuple, Any, Iterator
from src.engine.models import WorldState, Position

class WorldIntegrityError(Exception):
    pass

class ValidationResult(dict):
    """
    Result object supporting both dict access (report['valid'], report['errors'])
    and tuple unpacking (is_valid, errors = validator.validate_world_state(world)).
    """
    def __init__(self, valid: bool, errors: List[str]):
        super().__init__({"valid": valid, "errors": errors})

    @property
    def valid(self) -> bool:
        return self["valid"]

    @property
    def errors(self) -> List[str]:
        return self["errors"]

    def __iter__(self) -> Iterator[Any]:
        return iter((self["valid"], self["errors"]))

class IntegrityValidator:
    @staticmethod
    def validate_world_state(world: WorldState) -> ValidationResult:
        """
        Validates hard invariants before persisting a new world state version:
        1. Squad size within limits (18 - 22 players per club).
        2. Positional minimum make-up (min 2 GK, 6 DEF, 6 MID, 4 FWD).
        3. No negative club budget balances.
        4. No player registered with more than one club.
        5. User player must exist and have a valid contract (unless retired).
        """
        errors: List[str] = []
        registered_players: Dict[str, str] = {} # player_id -> club_id
        
        # 1. Club checks
        for cid, club in world.clubs.items():
            # Squad size check
            squad_size = len(club.player_ids)
            if squad_size < 18 or squad_size > 22:
                errors.append(f"Club {club.name} ({cid}) has illegal squad size: {squad_size} (Expected 18-22).")
                
            # Budget check
            if club.budget < 0:
                errors.append(f"Club {club.name} ({cid}) has negative budget: {club.budget}M.")
                
            # Positional composition check
            for pid in club.player_ids:
                if pid not in world.players:
                    errors.append(f"Club {club.name} references missing player: {pid}.")
            squad_players = [world.players[pid] for pid in club.player_ids if pid in world.players]
            counts = {
                Position.GK: sum(1 for p in squad_players if p.position == Position.GK),
                Position.DEF: sum(1 for p in squad_players if p.position == Position.DEF),
                Position.MID: sum(1 for p in squad_players if p.position == Position.MID),
                Position.FWD: sum(1 for p in squad_players if p.position == Position.FWD),
            }
            if counts[Position.GK] < 2:
                errors.append(f"Club {club.name} has only {counts[Position.GK]} GKs (min 2 required).")
            if counts[Position.DEF] < 6:
                errors.append(f"Club {club.name} has only {counts[Position.DEF]} DEFs (min 6 required).")
            if counts[Position.MID] < 6:
                errors.append(f"Club {club.name} has only {counts[Position.MID]} MIDs (min 6 required).")
            if counts[Position.FWD] < 4:
                errors.append(f"Club {club.name} has only {counts[Position.FWD]} FWDs (min 4 required).")
                
            # Duplicate registration check
            for pid in club.player_ids:
                if pid in registered_players:
                    errors.append(f"Player {pid} registered in multiple clubs: {registered_players[pid]} and {cid}.")
                registered_players[pid] = cid

        # Contract references must point to the player's registered club.
        for pid, player in world.players.items():
            if not player.contract:
                continue
            club = world.clubs.get(player.contract.club_id)
            if not club or pid not in club.player_ids:
                errors.append(f"Player {pid} has an orphaned contract for club {player.contract.club_id}.")
                
        # 3. User player check
        user_p = world.get_user_player()
        if not user_p:
            errors.append(f"User player {world.user_player_id} not found in world players.")
        elif not user_p.is_retired and not user_p.contract:
            errors.append(f"User player {world.user_player_id} has no active contract.")

        is_valid = len(errors) == 0
        return ValidationResult(valid=is_valid, errors=errors)

WorldIntegrityValidator = IntegrityValidator

