import os
import sys
import time
import json
import hashlib
import argparse
from typing import Optional, Dict, List, Any, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.models import WorldState, Position
from src.world_factory.generator import WorldGenerator
from src.engine.season_workflow import SeasonWorkflowEngine
from src.engine.integrity import WorldIntegrityValidator

def canonical_world_hash(world: WorldState) -> str:
    payload = json.dumps(
        world.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def run_100_season_burnin(
    seed: int = 42, 
    output_dir: str = "data/templates", 
    template_id: Optional[str] = None,
    world_index: int = 0,
    world_count: int = 1
):
    print("=" * 70)
    print(f"🚀 STARTING 100-SEASON WORLD SIMULATION (Seed: {seed})")
    print(f"📁 Output Directory: {output_dir}/")
    print(f"🏆 10 Domestic Leagues (200 Clubs) + 32-Team Continental Tournament")
    print(f"🌍 Indexed World: {world_index + 1}/{world_count}")
    print(f"📊 Total Matches: 3,831 matches/season x 100 seasons = 383,100 matches")
    print("=" * 70)

    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate fresh Day-0 world
    print("\n[1/3] Generating fresh Day-0 world with 200 clubs and 4,000 players...")
    gen = WorldGenerator(seed=seed)
    world = gen.generate_fresh_world(
        user_name="World Creator",
        user_country="England",
        user_position=Position.MID
    )
    workflow = SeasonWorkflowEngine(seed=seed)
    validator = WorldIntegrityValidator()
    print("      ✓ Day-0 world initialized successfully.")

    # 2. Simulate 100 seasons
    print("\n[2/3] Simulating 100 seasons in memory...")
    total_goals_recorded = 0
    total_matches_recorded = 0

    spearman_corrs: List[float] = []
    out_of_nowhere_champs = 0
    total_league_campaigns = 0
    club_rank_deltas: List[int] = []
    prev_club_ranks: Dict[str, int] = {}

    for s in range(1, 101):
        season_start = time.time()
        world.current_season = s

        # Gate 5 & 7: Pre-season squad strength ranking per league
        pre_season_ranks: Dict[str, Dict[str, int]] = {}
        for lid, league in world.leagues.items():
            club_strengths = []
            for cid in league.club_ids:
                c = world.clubs[cid]
                squad_ovr, att, df = c.calculate_squad_ratings(world.players)
                club_strengths.append((cid, squad_ovr, att + df))
            club_strengths.sort(key=lambda x: (x[1], x[2]), reverse=True)
            pre_season_ranks[lid] = {cid: idx + 1 for idx, (cid, _, _) in enumerate(club_strengths)}
        
        # Run full 8-stop season state machine
        workflow.simulate_full_season(world)

        # Gate 5, 6, 7: Evaluate league standing vs pre-season strength & stability
        for lid, league in world.leagues.items():
            total_league_campaigns += 1
            pre_ranks = pre_season_ranks[lid]
            sum_d_sq = 0

            for final_idx, standing in enumerate(league.standings):
                final_rank = final_idx + 1
                cid = standing.club_id
                pre_rank = pre_ranks.get(cid, 10)
                sum_d_sq += (pre_rank - final_rank) ** 2

                # Gate 6: Club stability delta
                if cid in prev_club_ranks:
                    club_rank_deltas.append(abs(final_rank - prev_club_ranks[cid]))
                prev_club_ranks[cid] = final_rank

            # Spearman Rank Correlation: rho = 1 - (6 * sum(d^2)) / (n * (n^2 - 1)), n=20 -> 7980
            rho = 1.0 - (6.0 * sum_d_sq) / 7980.0
            spearman_corrs.append(rho)

            # Gate 7: Check if champion was outside top 6 pre-season strength
            if league.standings:
                champ_cid = league.standings[0].club_id
                if pre_ranks.get(champ_cid, 1) > 6:
                    out_of_nowhere_champs += 1

        # Accumulate stats for metric verification
        for league in world.leagues.values():
            for std in league.standings:
                total_goals_recorded += std.goals_for
            total_matches_recorded += 380
        total_matches_recorded += 31 # 32-team tournament matches

        # Progress reporting every 10 seasons
        if s % 10 == 0 or s == 1:
            elapsed = time.time() - start_time
            matches_simulated = s * 3831
            rate = matches_simulated / elapsed if elapsed > 0 else 0
            print(f"      Season {s:3d}/100 | {matches_simulated:6,d} matches | {elapsed:5.1f}s elapsed | {rate:6.0f} matches/sec")

    total_duration = time.time() - start_time
    print(f"\n      ✓ 100 Seasons completed in {total_duration:.1f} seconds ({total_duration/60:.2f} minutes)!")

    # 3. Validation & Integrity Check
    print("\n[3/3] Executing Hard Invariant & Statistical Integrity Validation...")
    report = validator.validate_world_state(world)
    if not report.valid:
        print("      ❌ Integrity validation failed with errors:")
        for err in report.errors:
            print(f"         - {err}")
        sys.exit(1)
    print("      ✓ Hard Invariants Passed: Squad sizes 18-22, positional minimums, and zero budget deficits verified.")

    # 4. Statistical Metrics Audit
    goals_per_match = total_goals_recorded / total_matches_recorded if total_matches_recorded > 0 else 0
    print("\n" + "=" * 70)
    print("📊 100-SEASON STATISTICAL METRICS SUMMARY")
    print("=" * 70)
    print(f"• Total Seasons Simulated:     100")
    print(f"• Total Matches Simulated:     {total_matches_recorded:,}")
    print(f"• Total Goals Scored:          {total_goals_recorded:,}")
    print(f"• Overall Scoring Average:     {goals_per_match:.2f} goals/match (Target: 2.50 - 3.00)")
    
    # Tier Distribution
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for c in world.clubs.values():
        tier_counts[c.tier_number] = tier_counts.get(c.tier_number, 0) + 1
    print(f"\n🏆 Prestige Tier Distribution (200 Clubs across 10 Leagues):")
    print(f"   👑 Tier 1 (★★★★★): {tier_counts[1]:2d} clubs ({tier_counts[1]/2:.1f}%)")
    print(f"   💎 Tier 2 (★★★★) : {tier_counts[2]:2d} clubs ({tier_counts[2]/2:.1f}%)")
    print(f"   ⚡ Tier 3 (★★★)  : {tier_counts[3]:2d} clubs ({tier_counts[3]/2:.1f}%)")
    print(f"   🛡️ Tier 4 (★★)   : {tier_counts[4]:2d} clubs ({tier_counts[4]/2:.1f}%)")

    # Top Dynasty Champions
    top_clubs = sorted(world.clubs.values(), key=lambda c: (c.league_titles + c.tournament_titles * 2), reverse=True)[:5]
    print(f"\n👑 Top 5 Most Decorated Historic Clubs After 100 Seasons:")
    for rank, c in enumerate(top_clubs, 1):
        print(f"   {rank}. {c.name} ({world.leagues[c.league_id].name}) — {c.league_titles} League Titles, {c.tournament_titles} Continental Cups | {c.tier_name}")

    # 5. Consecutive Title Streak Audit (Dynasty Cap Verification)
    sorted_history = sorted(world.history, key=lambda h: h.season_year)
    league_streaks: Dict[str, Dict[str, Any]] = {}
    
    for lid, league in world.leagues.items():
        curr_holder = None
        curr_streak = 0
        curr_start = 1
        
        max_streak = 0
        max_holder = "None"
        max_start = 1
        max_end = 1
        
        for h in sorted_history:
            champ = h.league_champions.get(league.name)
            if champ:
                if champ == curr_holder:
                    curr_streak += 1
                else:
                    if curr_streak > max_streak:
                        max_streak = curr_streak
                        max_holder = curr_holder
                        max_start = curr_start
                        max_end = h.season_year - 1
                    curr_holder = champ
                    curr_streak = 1
                    curr_start = h.season_year
        if curr_streak > max_streak:
            max_streak = curr_streak
            max_holder = curr_holder
            max_start = curr_start
            max_end = len(sorted_history)
            
        league_streaks[league.name] = {
            "club": max_holder,
            "max_consecutive_titles": max_streak,
            "period": f"Seasons {max_start}–{max_end}" if max_streak > 1 else f"Season {max_start}"
        }

    # Continental Tournament Streak
    curr_tourn_holder = None
    curr_tourn_streak = 0
    curr_tourn_start = 1
    max_tourn_streak = 0
    max_tourn_holder = "None"
    max_tourn_start = 1
    max_tourn_end = 1
    
    for h in sorted_history:
        champ = h.tournament_champion
        if champ:
            if champ == curr_tourn_holder:
                curr_tourn_streak += 1
            else:
                if curr_tourn_streak > max_tourn_streak:
                    max_tourn_streak = curr_tourn_streak
                    max_tourn_holder = curr_tourn_holder
                    max_tourn_start = curr_tourn_start
                    max_tourn_end = h.season_year - 1
                curr_tourn_holder = champ
                curr_tourn_streak = 1
                curr_tourn_start = h.season_year
    if curr_tourn_streak > max_tourn_streak:
        max_tourn_streak = curr_tourn_streak
        max_tourn_holder = curr_tourn_holder
        max_tourn_start = curr_tourn_start
        max_tourn_end = len(sorted_history)

    print("\n" + "=" * 70)
    print("🔥 100-SEASON CONSECUTIVE TITLE STREAK REPORT (Dynasty Analysis)")
    print("=" * 70)
    print("🏆 Domestic League Record Streaks:")
    for l_name, s_info in league_streaks.items():
        print(f"   • {l_name:<28}: {s_info['club']} — {s_info['max_consecutive_titles']} consecutive ({s_info['period']})")
    print(f"\n⭐ Continental Champions Trophy Record Streak:")
    print(f"   • {max_tourn_holder} — {max_tourn_streak} consecutive titles ({f'Seasons {max_tourn_start}–{max_tourn_end}' if max_tourn_streak > 1 else f'Season {max_tourn_start}'})")
    
    max_league_dynasty = max((s['max_consecutive_titles'] for s in league_streaks.values()), default=0)

    # 6. Statistical Quality Gates Audit (Gates 5 - 9)
    # Gate 5: Strength vs Results
    mean_spearman = sum(spearman_corrs) / len(spearman_corrs) if spearman_corrs else 0.0
    gate5_pass = mean_spearman >= 0.50

    # Gate 6: Club Stability
    mean_rank_delta = sum(club_rank_deltas) / len(club_rank_deltas) if club_rank_deltas else 0.0
    large_jumps = sum(1 for d in club_rank_deltas if d >= 8)
    large_jump_pct = (large_jumps / len(club_rank_deltas) * 100) if club_rank_deltas else 0.0
    gate6_pass = (mean_rank_delta <= 3.5) and (large_jump_pct <= 10.0)

    # Gate 7: No Out-of-Nowhere Champions
    out_of_nowhere_pct = (out_of_nowhere_champs / total_league_campaigns * 100) if total_league_campaigns > 0 else 0.0
    gate7_pass = out_of_nowhere_pct <= 5.0

    # Gate 9: Player Stat Stability & Monotonicity (Computed per position)
    player_ga_deltas = []
    extreme_ga_swings = 0
    total_consecutive_player_seasons = 0
    
    # Attacker G+A buckets (FWD & MID)
    attacker_ovr_buckets = {"85+": [], "78-84": [], "70-77": [], "<70": []}
    # Defender & GK Defensive Impact buckets (DEF & GK: Clean Sheets)
    defender_ovr_buckets = {"85+": [], "78-84": [], "70-77": [], "<70": []}

    for p in world.players.values():
        is_attacker = p.position in (Position.FWD, Position.MID)
        for idx, rec in enumerate(p.history):
            ga = rec.goals + rec.assists
            cs = rec.clean_sheets
            ovr = rec.ending_rating
            
            if is_attacker:
                if ovr >= 85:
                    attacker_ovr_buckets["85+"].append(ga)
                elif ovr >= 78:
                    attacker_ovr_buckets["78-84"].append(ga)
                elif ovr >= 70:
                    attacker_ovr_buckets["70-77"].append(ga)
                else:
                    attacker_ovr_buckets["<70"].append(ga)
            else:
                if ovr >= 85:
                    defender_ovr_buckets["85+"].append(cs)
                elif ovr >= 78:
                    defender_ovr_buckets["78-84"].append(cs)
                elif ovr >= 70:
                    defender_ovr_buckets["70-77"].append(cs)
                else:
                    defender_ovr_buckets["<70"].append(cs)

            if idx > 0 and is_attacker:
                prev_rec = p.history[idx - 1]
                if rec.matches_played >= 25 and prev_rec.matches_played >= 25:
                    delta_ga = abs(ga - (prev_rec.goals + prev_rec.assists))
                    player_ga_deltas.append(delta_ga)
                    total_consecutive_player_seasons += 1
                    if delta_ga >= 20 and abs(rec.ending_rating - prev_rec.ending_rating) <= 1:
                        extreme_ga_swings += 1

    extreme_ga_pct = (extreme_ga_swings / total_consecutive_player_seasons * 100) if total_consecutive_player_seasons > 0 else 0.0
    
    mean_ga_85 = sum(attacker_ovr_buckets["85+"]) / len(attacker_ovr_buckets["85+"]) if attacker_ovr_buckets["85+"] else 0.0
    mean_ga_78 = sum(attacker_ovr_buckets["78-84"]) / len(attacker_ovr_buckets["78-84"]) if attacker_ovr_buckets["78-84"] else 0.0
    mean_ga_70 = sum(attacker_ovr_buckets["70-77"]) / len(attacker_ovr_buckets["70-77"]) if attacker_ovr_buckets["70-77"] else 0.0
    mean_ga_sub70 = sum(attacker_ovr_buckets["<70"]) / len(attacker_ovr_buckets["<70"]) if attacker_ovr_buckets["<70"] else 0.0
    
    mean_cs_85 = sum(defender_ovr_buckets["85+"]) / len(defender_ovr_buckets["85+"]) if defender_ovr_buckets["85+"] else 0.0
    mean_cs_78 = sum(defender_ovr_buckets["78-84"]) / len(defender_ovr_buckets["78-84"]) if defender_ovr_buckets["78-84"] else 0.0
    mean_cs_70 = sum(defender_ovr_buckets["70-77"]) / len(defender_ovr_buckets["70-77"]) if defender_ovr_buckets["70-77"] else 0.0
    mean_cs_sub70 = sum(defender_ovr_buckets["<70"]) / len(defender_ovr_buckets["<70"]) if defender_ovr_buckets["<70"] else 0.0

    attacker_buckets_populated = all(attacker_ovr_buckets.values())
    defender_buckets_populated = all(defender_ovr_buckets.values())
    attacker_monotonicity_pass = attacker_buckets_populated and (mean_ga_85 >= mean_ga_78 >= mean_ga_70 >= mean_ga_sub70)
    defender_monotonicity_pass = defender_buckets_populated and (mean_cs_85 >= mean_cs_78 >= mean_cs_70 >= mean_cs_sub70)
    monotonicity_pass = attacker_monotonicity_pass and defender_monotonicity_pass
    gate9_pass = (extreme_ga_pct <= 8.0) and monotonicity_pass

    # Gate 8: Dynasty audit upper bound
    gate8_pass = max_league_dynasty <= 8

    # Gate 10: Pydantic schema round-trip compatibility
    round_trip_world = WorldState.model_validate(world.model_dump())
    gate10_pass = (
        round_trip_world.model_dump(mode="json") == world.model_dump(mode="json")
        and world.rule_version == "1.0.0"
        and world.schema_version == "1.0.0"
        and len(world.clubs) == 200
        and len(world.players) >= 4000
    )

    # Gate 11: Canonical serialization determinism across a model round-trip
    state_hash = canonical_world_hash(world)
    round_trip_hash = canonical_world_hash(round_trip_world)
    gate11_pass = state_hash == round_trip_hash

    # Gate 12: Scoring Distribution Band (2.30 - 3.10 goals/match)
    gate12_pass = (2.30 <= goals_per_match <= 3.10)

    print("\n" + "=" * 70)
    print("🛡️ STATISTICAL QUALITY GATES VERIFICATION (Gates 5–12)")
    print("=" * 70)
    print(f"5.  Strength vs Results (Spearman ρ):  ρ = {mean_spearman:.2f} (Target: ≥ 0.50)  ──► [{'PASS ✓' if gate5_pass else 'FAIL ✗'}]")
    print(f"6.  Club Stability:                    Mean Δ = {mean_rank_delta:.2f}, Swings ≥8 = {large_jump_pct:.1f}% (Targets: ≤3.5, ≤10%)  ──► [{'PASS ✓' if gate6_pass else 'FAIL ✗'}]")
    print(f"7.  No Out-of-Nowhere Champions:       {out_of_nowhere_champs}/{total_league_campaigns} ({out_of_nowhere_pct:.1f}%) outside Top 6 (Target: ≤ 5.0%)  ──► [{'PASS ✓' if gate7_pass else 'FAIL ✗'}]")
    print(f"8.  Dynasty Audit:                     Longest = {max_league_dynasty} in a row (Maximum: 8)  ──► [{'PASS ✓' if gate8_pass else 'FAIL ✗'}]")
    print(f"9.  Player Stat Stability & Output:    Extreme Swings = {extreme_ga_pct:.1f}%, Attacker G+A Monotonicity: {mean_ga_85:.1f} > {mean_ga_78:.1f} > {mean_ga_70:.1f} > {mean_ga_sub70:.1f}  ──► [{'PASS ✓' if gate9_pass else 'FAIL ✗'}]")
    print(f"10. Schema & Model Compatibility:      Rule v{world.rule_version} / Schema v{world.schema_version} (200 Clubs, 4000 Players)  ──► [{'PASS ✓' if gate10_pass else 'FAIL ✗'}]")
    print(f"11. Canonical State Determinism:       Round-trip hash comparison  ──► [{'PASS ✓' if gate11_pass else 'FAIL ✗'}]")
    print(f"12. Scoring Distribution Band:         {goals_per_match:.2f} goals/match (Acceptance Band: 2.30 - 3.10)  ──► [{'PASS ✓' if gate12_pass else 'FAIL ✗'}]")
    print("=" * 70)

    # 7. Persist Output File
    actual_template_id = template_id or f"world_{world_index:03d}_seed_{seed}_v{world.rule_version}"

    all_gates_passed = gate5_pass and gate6_pass and gate7_pass and gate8_pass and gate9_pass and gate10_pass and gate11_pass and gate12_pass

    template_payload = {
        "template_id": actual_template_id,
        "seed": seed,
        "status": "APPROVED" if all_gates_passed else "REJECTED",
        "burn_in_seasons": 100,
        "rule_version": world.rule_version,
        "schema_version": world.schema_version,
        "content_hash": state_hash,
        "generation_time_seconds": round(total_duration, 2),
        "total_matches_simulated": total_matches_recorded,
        "goals_per_match": round(goals_per_match, 2),
        "tier_distribution": tier_counts,
        "dynasty_report": {
            "max_league_dynasty": max_league_dynasty,
            "max_continental_dynasty": max_tourn_streak,
            "league_streaks": league_streaks,
            "continental_streak": {
                "club": max_tourn_holder,
                "streak": max_tourn_streak,
                "period": f"Seasons {max_tourn_start}–{max_tourn_end}" if max_tourn_streak > 1 else f"Season {max_tourn_start}"
            }
        },
        "quality_gate_results": {
            "gate1_to_4_invariants": {
                "passed": report.valid,
                "errors": report.errors
            },
            "gate5_strength_vs_results": {
                "metric": "Spearman Rank Correlation (rho)",
                "value": round(mean_spearman, 3),
                "threshold": ">= 0.50",
                "passed": gate5_pass
            },
            "gate6_club_stability": {
                "mean_rank_delta": round(mean_rank_delta, 2),
                "large_jumps_ge8_pct": round(large_jump_pct, 2),
                "thresholds": "mean <= 3.5, ge8 <= 10.0%",
                "passed": gate6_pass
            },
            "gate7_out_of_nowhere_champions": {
                "count": out_of_nowhere_champs,
                "total_campaigns": total_league_campaigns,
                "pct": round(out_of_nowhere_pct, 2),
                "threshold": "<= 5.0%",
                "passed": gate7_pass
            },
            "gate8_dynasty_audit": {
                "max_league_dynasty": max_league_dynasty,
                "max_continental_dynasty": max_tourn_streak,
                "maximum_allowed": 8,
                "passed": gate8_pass
            },
            "gate9_player_stat_stability": {
                "extreme_ga_swings_pct": round(extreme_ga_pct, 2),
                "attacker_mean_ga_by_ovr": {
                    "85+": round(mean_ga_85, 1),
                    "78-84": round(mean_ga_78, 1),
                    "70-77": round(mean_ga_70, 1),
                    "<70": round(mean_ga_sub70, 1)
                },
                "defender_mean_cs_by_ovr": {
                    "85+": round(mean_cs_85, 1),
                    "78-84": round(mean_cs_78, 1),
                    "70-77": round(mean_cs_70, 1),
                    "<70": round(mean_cs_sub70, 1)
                },
                "attacker_monotonicity_passed": attacker_monotonicity_pass,
                "defender_monotonicity_passed": defender_monotonicity_pass,
                "passed": gate9_pass
            },
            "gate10_schema_compatibility": {
                "rule_version": world.rule_version,
                "schema_version": world.schema_version,
                "round_trip_validated": True,
                "passed": gate10_pass
            },
            "gate11_serialization_determinism": {
                "hash_algorithm": "SHA-256",
                "round_trip_hash_match": gate11_pass,
                "passed": gate11_pass
            },
            "gate12_scoring_band": {
                "goals_per_match": round(goals_per_match, 2),
                "band": "2.30 - 3.10",
                "passed": gate12_pass
            }
        },
        "integrity_report": report,
        "world_state": world.model_dump()
    }

    out_path = os.path.join(output_dir, f"{actual_template_id}.json")
    default_path = os.path.join(output_dir, f"template_seed{seed}_100s.json")

    # ── Worker Write Protocol (P4 Section 4) ─────────────────────────────────
    # 1. Serialize final payload exactly once to world_bytes (plain uncompressed JSON)
    world_bytes = json.dumps(template_payload, indent=2, ensure_ascii=False).encode("utf-8")
    content_hash = hashlib.sha256(world_bytes).hexdigest()

    with open(out_path, "wb") as f:
        f.write(world_bytes)

    with open(default_path, "wb") as f:
        f.write(world_bytes)

    # 2. Upload to S3 using conditional write (If-None-Match: *)
    results_bucket = os.getenv("WORLD_RESULTS_BUCKET")
    dynamo_table = os.getenv("DYNAMODB_TABLE", "world_template_catalog")
    region_name = os.getenv("AWS_REGION", "ap-south-1")

    if results_bucket:
        import boto3
        from botocore.exceptions import ClientError
        from decimal import Decimal

        s3 = boto3.client("s3", region_name=region_name)
        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        table = dynamodb.Table(dynamo_table)

        # Key format: templates/v1/world_<index>_seed_<seed>_<hash[:12]>.json
        result_key = f"templates/v1/world_{world_index:03d}_seed_{seed}_{content_hash[:12]}.json"
        s3_uri = f"s3://{results_bucket}/{result_key}"

        try:
            s3.put_object(
                Bucket=results_bucket,
                Key=result_key,
                Body=world_bytes,
                ContentType="application/json",
                IfNoneMatch="*"
            )
            print(f"☁️ Uploaded immutable world to {s3_uri}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("PreconditionFailed", "412"):
                print(f"⚠️ S3 object already exists at {s3_uri}. Verifying SHA-256 hash...")
                existing_obj = s3.get_object(Bucket=results_bucket, Key=result_key)
                existing_bytes = existing_obj["Body"].read()
                existing_hash = hashlib.sha256(existing_bytes).hexdigest()
                if existing_hash == content_hash:
                    print(f"✓ S3 object hash verified ({content_hash[:12]}). Safe retry acknowledged.")
                else:
                    raise RuntimeError(f"Hash mismatch on existing S3 template! Expected {content_hash}, got {existing_hash}")
            else:
                raise e

        # 3. DynamoDB catalog record with attribute_not_exists
        duration_sec = Decimal(str(round(time.time() - start_time, 2)))
        gates_summary = {k: v.get("passed", False) if isinstance(v, dict) else bool(v) for k, v in template_payload["quality_gate_results"].items()}
        all_passed = all(gates_summary.values())

        catalog_item = {
            "template_id": actual_template_id,
            "seed": seed,
            "content_hash": content_hash,
            "generation_duration_sec": duration_sec,
            "quality_gate_results": gates_summary,
            "status": "APPROVED" if all_passed else "REJECTED",
            "s3_uri": s3_uri,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        try:
            table.put_item(
                Item=catalog_item,
                ConditionExpression="attribute_not_exists(template_id)"
            )
            print(f"📋 DynamoDB catalog registered: {actual_template_id} -> {catalog_item['status']}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                print(f"⚠️ DynamoDB template_id '{actual_template_id}' already registered. Safe retry acknowledged.")
            else:
                print(f"⚠️ DynamoDB write failed: {e}")

    file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("\n" + "=" * 70)
    print(f"💾 TEMPLATE SAVED SUCCESSFULLY!")
    print(f"📄 Versioned: {out_path}")
    print(f"📄 Canonical: {default_path}")
    print(f"📦 Size:      {file_size_mb:.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="100-Season World Simulation Burn-in Runner")
    parser.add_argument("--seed", type=int, default=42, help="RNG Seed for world generation")
    parser.add_argument("--output-dir", type=str, default="data/templates", help="Output directory for template JSON")
    parser.add_argument("--template-id", type=str, default=None, help="Custom template identifier")
    parser.add_argument("--world-index", type=int, default=int(os.getenv("WORLD_INDEX", "0")), help="Zero-based indexed world worker number")
    parser.add_argument("--world-count", type=int, default=int(os.getenv("WORLD_COUNT", "1")), help="Total worlds in the EKS batch")
    args = parser.parse_args()

    worker_seed = args.seed + args.world_index

    run_100_season_burnin(
        seed=worker_seed,
        output_dir=args.output_dir,
        template_id=args.template_id,
        world_index=args.world_index,
        world_count=args.world_count
    )
