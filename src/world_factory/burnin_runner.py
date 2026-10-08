import os
import json
import uuid
import time
from typing import Dict, List, Optional
from src.engine.models import WorldState, Position
from src.world_factory.generator import WorldGenerator
from src.engine.season_workflow import SeasonWorkflowEngine
from src.engine.integrity import WorldIntegrityValidator

class WorldBurnInRunner:
    """
    Simulates multi-season offline burn-in for generating validated world templates.
    Used by the World Factory as one indexed Kubernetes worker or locally for validation.
    """
    def __init__(self, seed: int = 42, burn_in_seasons: int = 100, output_dir: str = ".local_data/templates", world_index: int = 0, world_count: int = 1):
        self.seed = seed
        self.burn_in_seasons = burn_in_seasons
        self.output_dir = output_dir
        self.world_index = world_index
        self.world_count = world_count
        self.validator = WorldIntegrityValidator()

    def generate_and_burn_in(self, template_id: Optional[str] = None) -> Dict:
        template_id = template_id or f"world_{self.world_index:03d}_seed_{self.seed}"
        start_time = time.time()
        
        # 1. Initialize fresh seeded world with AI placeholder player
        gen = WorldGenerator(seed=self.seed)
        world = gen.generate_fresh_world(
            user_name="World Creator",
            user_country="England",
            user_position=Position.MID
        )
        
        workflow = SeasonWorkflowEngine(seed=self.seed)
        
        # 2. Simulate N seasons in fast batch mode
        for s in range(1, self.burn_in_seasons + 1):
            world.current_season = s
            workflow.simulate_full_season(world)
            
        elapsed = time.time() - start_time
        
        # 3. Validate World Invariants & Integrity
        report = self.validator.validate_world_state(world)
        if not report["valid"]:
            raise ValueError(f"Template burn-in failed integrity validation: {report['errors']}")
            
        # 4. Compact older history & extract legends
        template_payload = {
            "template_id": template_id,
            "seed": self.seed,
            "world_index": self.world_index,
            "world_count": self.world_count,
            "burn_in_seasons": self.burn_in_seasons,
            "rule_version": world.rule_version,
            "schema_version": world.schema_version,
            "generation_time_seconds": round(elapsed, 2),
            "integrity_report": report,
            "world_state": world.model_dump()
        }
        
        # 5. Persist to template directory
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, f"{template_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(template_payload, f, indent=2)
            
        return {
            "template_id": template_id,
            "seed": self.seed,
            "world_index": self.world_index,
            "world_count": self.world_count,
            "seasons": self.burn_in_seasons,
            "duration_sec": round(elapsed, 2),
            "output_file": out_path,
            "valid": report["valid"]
        }

if __name__ == "__main__":
    runner = WorldBurnInRunner(seed=100, burn_in_seasons=5, world_index=0, world_count=1)
    result = runner.generate_and_burn_in()
    print("Burn-in Template generated successfully:", result)
