import os
import json
import uuid
import random
from typing import Dict, List, Optional, Any
from src.engine.models import WorldState, Player, Club, Position, Contract, ClubLegend
from src.world_factory.generator import WorldGenerator
from src.world_factory.burnin_runner import WorldBurnInRunner

TEMPLATES_DIR = ".local_data/templates"

class TemplateManager:
    """
    Manages the pool of pre-simulated world templates.
    Enables instant onboarding from mature, equilibrium world templates with genuine histories.
    """
    def __init__(self, templates_dir: str = TEMPLATES_DIR):
        self.templates_dir = templates_dir
        self.search_dirs = [self.templates_dir, "data/templates", ".local_data/templates"]
        for d in self.search_dirs:
            os.makedirs(d, exist_ok=True)

    def list_templates(self) -> List[Dict[str, Any]]:
        templates = []
        seen_ids = set()

        # Check local directories first
        for d in self.search_dirs:
            if not os.path.exists(d):
                continue
            for fname in os.listdir(d):
                if fname.endswith(".json"):
                    fpath = os.path.join(d, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            tpl_id = data.get("template_id", fname.replace(".json", ""))
                            if tpl_id in seen_ids:
                                continue
                            seen_ids.add(tpl_id)
                            templates.append({
                                "template_id": tpl_id,
                                "seed": data.get("seed", 42),
                                "burn_in_seasons": data.get("burn_in_seasons", 100),
                                "rule_version": data.get("rule_version", "1.0.0"),
                                "schema_version": data.get("schema_version", "1.0.0"),
                                "generation_time_seconds": data.get("generation_time_seconds", 0),
                                "file_path": fpath,
                                "source": "local"
                            })
                    except Exception:
                        continue

        # If running in AWS or TEMPLATES_S3_BUCKET is provided, query S3 / DynamoDB
        s3_bucket = os.getenv("TEMPLATES_S3_BUCKET") or os.getenv("WORLD_RESULTS_BUCKET")
        catalog_table = os.getenv("DYNAMODB_CATALOG_TABLE", "world_template_catalog")
        region = os.getenv("AWS_REGION", "ap-south-1")

        if s3_bucket:
            import boto3
            # Try DynamoDB catalog table first
            try:
                dynamodb = boto3.resource("dynamodb", region_name=region)
                table = dynamodb.Table(catalog_table)
                resp = table.scan(Limit=50)
                for item in resp.get("Items", []):
                    tpl_id = item.get("template_id")
                    if tpl_id and tpl_id not in seen_ids:
                        seen_ids.add(tpl_id)
                        templates.append({
                            "template_id": tpl_id,
                            "seed": int(item.get("seed", 42)),
                            "burn_in_seasons": 100,
                            "rule_version": str(item.get("rule_version", "1.0.0")),
                            "schema_version": str(item.get("schema_version", "1.0.0")),
                            "generation_time_seconds": float(item.get("generation_duration_sec", 0)),
                            "s3_uri": item.get("s3_uri"),
                            "s3_key": item.get("s3_key", f"templates/v1/{tpl_id}.json"),
                            "source": "s3"
                        })
            except Exception:
                pass

            # If no items from catalog, list objects directly from S3 templates/v1/ prefix
            if not templates:
                try:
                    s3_client = boto3.client("s3", region_name=region)
                    s3_objs = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix="templates/")
                    for obj in s3_objs.get("Contents", []):
                        key = obj.get("Key", "")
                        if key.endswith(".json"):
                            tpl_id = key.split("/")[-1].replace(".json", "")
                            if tpl_id not in seen_ids:
                                seen_ids.add(tpl_id)
                                templates.append({
                                    "template_id": tpl_id,
                                    "seed": 42,
                                    "burn_in_seasons": 100,
                                    "rule_version": "1.0.0",
                                    "schema_version": "1.0.0",
                                    "s3_key": key,
                                    "source": "s3"
                                })
                except Exception:
                    pass

        return templates

    def get_or_create_template(self, seed: int = 42, burn_in_seasons: int = 100) -> Dict[str, Any]:
        templates = self.list_templates()
        if templates:
            return random.choice(templates)
            
        # If no templates exist in storage, generate an initial equilibrium template
        template_id = f"tpl_seed_{seed}"
        runner = WorldBurnInRunner(
            seed=seed,
            burn_in_seasons=burn_in_seasons,
            output_dir=self.templates_dir
        )
        runner.generate_and_burn_in(template_id=template_id)
        
        # Reload metadata
        templates = self.list_templates()
        return templates[0] if templates else {
            "template_id": template_id,
            "seed": seed,
            "burn_in_seasons": burn_in_seasons,
            "rule_version": "1.0.0",
            "schema_version": "1.0.0"
        }

    def instantiate_career_from_template(
        self,
        template_id: str,
        user_name: str,
        user_country: str,
        user_position: Position,
        rng_seed: Optional[int] = None
    ) -> WorldState:
        """
        Loads a pre-burned-in world template, resets the user's career clock to Season 1,
        and spawns the user's 17-year-old character into a club academy in the mature world.
        """
        fpath = None
        tpl_data = None

        for d in self.search_dirs:
            candidate = os.path.join(d, f"{template_id}.json")
            if os.path.exists(candidate):
                fpath = candidate
                break
        
        if fpath and os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                tpl_data = json.load(f)
        else:
            # Check if template can be fetched from S3
            s3_bucket = os.getenv("TEMPLATES_S3_BUCKET") or os.getenv("WORLD_RESULTS_BUCKET")
            if s3_bucket:
                import boto3
                region = os.getenv("AWS_REGION", "ap-south-1")
                s3_client = boto3.client("s3", region_name=region)
                possible_keys = [
                    f"templates/v1/{template_id}.json",
                    f"templates/{template_id}.json",
                    f"{template_id}.json"
                ]
                all_tpls = self.list_templates()
                for t in all_tpls:
                    if t.get("template_id") == template_id and t.get("s3_key"):
                        possible_keys.insert(0, t["s3_key"])
                        break
                for k in possible_keys:
                    try:
                        resp = s3_client.get_object(Bucket=s3_bucket, Key=k)
                        tpl_data = json.loads(resp["Body"].read().decode("utf-8"))
                        break
                    except Exception:
                        continue

            if not tpl_data:
                # Fallback to first available template
                templates = self.list_templates()
                for t in templates:
                    if t.get("source") == "local" and t.get("file_path") and os.path.exists(t["file_path"]):
                        with open(t["file_path"], "r", encoding="utf-8") as f:
                            tpl_data = json.load(f)
                            break
                    elif t.get("source") == "s3" and s3_bucket and t.get("s3_key"):
                        try:
                            resp = s3_client.get_object(Bucket=s3_bucket, Key=t["s3_key"])
                            tpl_data = json.loads(resp["Body"].read().decode("utf-8"))
                            break
                        except Exception:
                            continue

            if not tpl_data:
                tpl_info = self.get_or_create_template(seed=rng_seed or 42)
                fp = tpl_info.get("file_path", os.path.join(self.templates_dir, f"{tpl_info['template_id']}.json"))
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8") as f:
                        tpl_data = json.load(f)
                else:
                    tpl_data = {"world_state": {}}

        raw_world = tpl_data.get("world_state", {})
        world = WorldState.model_validate(raw_world)
        
        rng = random.Random(rng_seed or world.seed)
        
        # Reset career tracking counters for user's career while preserving world heritage
        world.world_id = f"wld_{uuid.uuid4().hex[:8]}"
        world.current_season = 1
        world.current_stage = 1
        
        # Remove placeholder AI creation player if present
        if world.user_player_id in world.players:
            old_p = world.players[world.user_player_id]
            if old_p.contract and old_p.contract.club_id in world.clubs:
                club = world.clubs[old_p.contract.club_id]
                if old_p.id in club.player_ids:
                    club.player_ids.remove(old_p.id)
            del world.players[world.user_player_id]

        # Select starting club in the user's home country (domestic start rule)
        domestic_clubs = [
            c for c in world.clubs.values() 
            if c.country.strip().lower() == user_country.strip().lower()
        ]
        if not domestic_clubs:
            # Fallback if country has no domestic league
            domestic_clubs = list(world.clubs.values())
            
        user_club = rng.choice(domestic_clubs)
        target_club_id = user_club.id
        
        # Create user player at age 17
        usr_id = f"usr_{uuid.uuid4().hex[:8]}"
        base_pot = 92 + (user_club.infrastructure_level * 1) + rng.randint(2, 6)
        starting_ovr = 60 + (user_club.infrastructure_level * 2) + rng.randint(-2, 3)
        starting_ovr = max(55, min(75, starting_ovr))
        
        user_contract = Contract(
            club_id=user_club.id,
            club_name=user_club.name,
            years_remaining=3,
            total_years=3,
            wage=1.5
        )
        
        user_player = Player(
            id=usr_id,
            name=user_name,
            country=user_country,
            age=17,
            position=user_position,
            overall_rating=starting_ovr,
            potential=min(100, base_pot),
            attacking=starting_ovr + rng.randint(-4, 4),
            playmaking=starting_ovr + rng.randint(-4, 4),
            defending=starting_ovr + rng.randint(-4, 4),
            physical=starting_ovr + rng.randint(-4, 4),
            contract=user_contract,
            market_value=3.5,
            is_user=True
        )
        
        # Replace one same-position player in the club to maintain 20 squad size
        same_pos = [pid for pid in user_club.player_ids if world.players.get(pid) and world.players[pid].position == user_position]
        if same_pos:
            removed_id = same_pos[-1]
            user_club.player_ids.remove(removed_id)
            world.free_agent_ids.append(removed_id)
            if removed_id in world.players:
                world.players[removed_id].contract = None
                
        user_club.player_ids.append(user_player.id)
        world.players[user_player.id] = user_player
        world.user_player_id = user_player.id
        
        # Reset current season stats on all players and clubs so career begins with a clean slate
        for p in world.players.values():
            p.reset_season_stats()
        for c in world.clubs.values():
            c.reset_season_stats()
            
        return world
