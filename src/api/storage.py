import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.engine.models import WorldState

LOCAL_DATA_DIR = Path(".local_data")
WORLDS_DIR = LOCAL_DATA_DIR / "worlds"
SCREENS_DIR = LOCAL_DATA_DIR / "screens"
SAVES_DIR = LOCAL_DATA_DIR / "saves"

class LocalStorageAdapter:
    def __init__(self):
        try:
            WORLDS_DIR.mkdir(parents=True, exist_ok=True)
            SCREENS_DIR.mkdir(parents=True, exist_ok=True)
            SAVES_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def save_world(self, world: WorldState) -> str:
        """Saves current world state and creates versioned history snapshot"""
        # Save live state
        live_path = WORLDS_DIR / f"{world.world_id}_live.json"
        with open(live_path, "w", encoding="utf-8") as f:
            f.write(world.model_dump_json(indent=2))

        # Save pointer to latest active world
        latest_path = WORLDS_DIR / "latest_live.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump({"world_id": world.world_id}, f)
            
        # Create immutable version snapshot
        version_id = f"v_s{world.current_season}_st{world.current_stage}_{uuid.uuid4().hex[:6]}"
        version_path = WORLDS_DIR / f"{world.world_id}_{version_id}.json"
        with open(version_path, "w", encoding="utf-8") as f:
            f.write(world.model_dump_json())
            
        return version_id

    def get_active_world(self) -> Optional[WorldState]:
        latest_path = WORLDS_DIR / "latest_live.json"
        if latest_path.exists():
            try:
                with open(latest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    wid = data.get("world_id")
                    if wid:
                        return self.load_world(wid)
            except Exception:
                pass
        return None

    def load_world(self, world_id: str) -> Optional[WorldState]:
        live_path = WORLDS_DIR / f"{world_id}_live.json"
        if not live_path.exists():
            return None
        with open(live_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return WorldState.model_validate(data)

    def save_screen_document(self, world_id: str, season_or_stage: int, stage_or_payload: Any, payload: Optional[Dict[str, Any]] = None):
        if payload is not None:
            season = int(season_or_stage)
            stage = int(stage_or_payload)
            screen_path = SCREENS_DIR / f"{world_id}_s{season}_stage_{stage}.json"
            content = payload
        else:
            stage = int(season_or_stage)
            screen_path = SCREENS_DIR / f"{world_id}_stage_{stage}.json"
            content = stage_or_payload
        with open(screen_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)

    def get_screen_document(self, world_id: str, season_or_stage: int, stage: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if stage is not None:
            season = int(season_or_stage)
            screen_path = SCREENS_DIR / f"{world_id}_s{season}_stage_{stage}.json"
            if not screen_path.exists():
                screen_path = SCREENS_DIR / f"{world_id}_stage_{stage}.json"
        else:
            st = int(season_or_stage)
            screen_path = SCREENS_DIR / f"{world_id}_stage_{st}.json"
        if not screen_path.exists():
            return None
        with open(screen_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_manual_save(self, world: WorldState, save_name: str) -> Dict[str, Any]:
        save_id = f"save_{uuid.uuid4().hex[:8]}"
        save_path = SAVES_DIR / f"{save_id}.json"
        
        save_record = {
            "save_id": save_id,
            "save_name": save_name,
            "world_id": world.world_id,
            "season": world.current_season,
            "stage": world.current_stage,
            "player_name": world.get_user_player().name if world.get_user_player() else "Player",
            "club_name": world.get_user_club().name if world.get_user_club() else "Free Agent",
            "overall_rating": world.get_user_player().overall_rating if world.get_user_player() else 0,
            "world_payload": world.model_dump()
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_record, f, indent=2)
            
        return save_record

    def list_saves(self) -> List[Dict[str, Any]]:
        saves = []
        for file in SAVES_DIR.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saves.append({
                        "save_id": data.get("save_id"),
                        "save_name": data.get("save_name"),
                        "season": data.get("season"),
                        "stage": data.get("stage"),
                        "player_name": data.get("player_name"),
                        "club_name": data.get("club_name"),
                        "overall_rating": data.get("overall_rating")
                    })
            except Exception:
                continue
        return saves

    def load_save(self, save_id: str) -> Optional[WorldState]:
        save_path = SAVES_DIR / f"{save_id}.json"
        if not save_path.exists():
            return None
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            world_payload = data.get("world_payload")
            if world_payload:
                world = WorldState.model_validate(world_payload)
                self.save_world(world) # Make active
                return world
        return None


class S3StorageAdapter:
    """
    S3-backed storage adapter for AWS Lambda deployments.
    Persists active career states, stage screen projections, and manual saves into Amazon S3.
    """
    def __init__(self, bucket_name: Optional[str] = None, region: Optional[str] = None):
        import boto3
        self.bucket = (
            bucket_name
            or os.getenv("SAVES_S3_BUCKET")
            or os.getenv("TEMPLATES_S3_BUCKET")
            or f"football-life-templates-{os.getenv('AWS_REGION', 'ap-south-1')}"
        )
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self.s3 = boto3.client("s3", region_name=self.region)

    def _put_json(self, key: str, payload: Any):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json"
        )

    def _get_json(self, key: str) -> Optional[Any]:
        from botocore.exceptions import ClientError
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            return json.loads(resp["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            raise

    def save_world(self, world: WorldState) -> str:
        """Saves current world state and creates versioned history snapshot in S3"""
        live_key = f"sessions/{world.world_id}/world_state_live.json"
        self._put_json(live_key, world.model_dump(mode="json"))

        # Save pointer to latest active session
        self._put_json("sessions/latest_live.json", {"world_id": world.world_id})

        version_id = f"v_s{world.current_season}_st{world.current_stage}_{uuid.uuid4().hex[:6]}"
        version_key = f"sessions/{world.world_id}/versions/{version_id}.json"
        self._put_json(version_key, world.model_dump(mode="json"))
        return version_id

    def get_active_world(self) -> Optional[WorldState]:
        latest_data = self._get_json("sessions/latest_live.json")
        if latest_data and "world_id" in latest_data:
            return self.load_world(latest_data["world_id"])
        return None

    def load_world(self, world_id: str) -> Optional[WorldState]:
        live_key = f"sessions/{world_id}/world_state_live.json"
        data = self._get_json(live_key)
        if not data:
            return None
        return WorldState.model_validate(data)

    def save_screen_document(self, world_id: str, season_or_stage: int, stage_or_payload: Any, payload: Optional[Dict[str, Any]] = None):
        if payload is not None:
            season = int(season_or_stage)
            stage = int(stage_or_payload)
            key = f"sessions/{world_id}/screens/s{season}_stage_{stage}.json"
            content = payload
        else:
            stage = int(season_or_stage)
            key = f"sessions/{world_id}/screens/stage_{stage}.json"
            content = stage_or_payload
        self._put_json(key, content)

    def get_screen_document(self, world_id: str, season_or_stage: int, stage: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if stage is not None:
            season = int(season_or_stage)
            key = f"sessions/{world_id}/screens/s{season}_stage_{stage}.json"
            doc = self._get_json(key)
            if not doc:
                key = f"sessions/{world_id}/screens/stage_{stage}.json"
                doc = self._get_json(key)
            return doc
        st = int(season_or_stage)
        key = f"sessions/{world_id}/screens/stage_{st}.json"
        return self._get_json(key)

    def create_manual_save(self, world: WorldState, save_name: str) -> Dict[str, Any]:
        save_id = f"save_{uuid.uuid4().hex[:8]}"
        save_key = f"saves/{save_id}.json"
        user_p = world.get_user_player()
        user_c = world.get_user_club()
        save_record = {
            "save_id": save_id,
            "save_name": save_name,
            "world_id": world.world_id,
            "season": world.current_season,
            "stage": world.current_stage,
            "player_name": user_p.name if user_p else "Player",
            "club_name": user_c.name if user_c else "Free Agent",
            "overall_rating": user_p.overall_rating if user_p else 0,
            "world_payload": world.model_dump(mode="json")
        }
        self._put_json(save_key, save_record)
        return save_record

    def list_saves(self) -> List[Dict[str, Any]]:
        saves = []
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix="saves/"):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                if key.endswith(".json"):
                    data = self._get_json(key)
                    if data:
                        saves.append({
                            "save_id": data.get("save_id"),
                            "save_name": data.get("save_name"),
                            "season": data.get("season"),
                            "stage": data.get("stage"),
                            "player_name": data.get("player_name"),
                            "club_name": data.get("club_name"),
                            "overall_rating": data.get("overall_rating")
                        })
        return saves

    def load_save(self, save_id: str) -> Optional[WorldState]:
        key = f"saves/{save_id}.json"
        data = self._get_json(key)
        if not data:
            return None
        world_payload = data.get("world_payload")
        if world_payload:
            world = WorldState.model_validate(world_payload)
            self.save_world(world)
            return world
        return None


def get_storage_adapter():
    """Returns S3StorageAdapter if running in AWS / Lambda, otherwise LocalStorageAdapter"""
    is_cloud = (
        os.getenv("STORAGE_BACKEND", "").lower() == "s3"
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "LAMBDA_TASK_ROOT" in os.environ
    )
    if is_cloud:
        return S3StorageAdapter()
    return LocalStorageAdapter()
