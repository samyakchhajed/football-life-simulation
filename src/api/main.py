import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from src.engine.models import Position, WorldState, Contract
from src.world_factory.generator import WorldGenerator
from src.world_factory.template_manager import TemplateManager
from src.world_factory.burnin_runner import WorldBurnInRunner
from src.engine.season_workflow import SeasonWorkflowEngine
from src.api.storage import get_storage_adapter

app = FastAPI(
    title="The Football Life Engine API",
    description="Data-driven career football simulation engine with 8-stop season workflow",
    version="1.0.0"
)

# In AWS Lambda, CORS is handled natively at the Function URL infrastructure layer (lambda.tf).
# Emitting CORS headers from both FastAPI CORSMiddleware and AWS Lambda Function URL causes duplicate
# 'Access-Control-Allow-Origin' headers, which browsers reject with net::ERR_FAILED.
# We enable CORSMiddleware only in non-Lambda environments (e.g. local uvicorn development).
if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

storage = get_storage_adapter()
engine = SeasonWorkflowEngine(seed=42)
template_manager = TemplateManager()

# In-memory active world reference and current live screen for local play
active_world: Optional[WorldState] = None
active_screen: Optional[Dict[str, Any]] = None

def _get_active_world() -> WorldState:
    global active_world
    if not active_world:
        active_world = storage.get_active_world()
    if not active_world:
        raise HTTPException(status_code=404, detail="No active world found. Create one first.")
    return active_world

class CreatePlayerRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    country: str = Field(default="England")
    position: Position = Field(default=Position.FWD)
    seed: int = Field(default=42)
    template_id: Optional[str] = None

class GenerateTemplateRequest(BaseModel):
    seed: int = Field(default=42)
    burn_in_seasons: int = Field(default=100)

class UserChoiceRequest(BaseModel):
    choice_type: str # "transfer", "injury"
    selected_offer_id: Optional[str] = None # None means become free agent or renew
    retire_choice: Optional[bool] = None

class ManualSaveRequest(BaseModel):
    save_name: str = Field(default="Career Save Point")

class SaveImportRequest(BaseModel):
    world_payload: Dict[str, Any]

@app.get("/healthz")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/world/templates")
def list_world_templates():
    return {"templates": template_manager.list_templates()}

@app.get("/api/world/template")
def get_random_template():
    tpl = template_manager.get_or_create_template()
    return {"template": tpl}

@app.post("/api/world/generate-template")
def generate_new_template(req: GenerateTemplateRequest):
    runner = WorldBurnInRunner(seed=req.seed, burn_in_seasons=req.burn_in_seasons)
    res = runner.generate_and_burn_in()
    return {"status": "success", "result": res}

@app.post("/api/world/new")
@app.post("/api/world/create")
def create_new_world(req: CreatePlayerRequest):
    global active_world, active_screen
    
    # Check if we should instantiate from pre-simulated template pool
    available_templates = template_manager.list_templates()
    if req.template_id or available_templates:
        tpl_id = req.template_id or available_templates[0]["template_id"]
        active_world = template_manager.instantiate_career_from_template(
            template_id=tpl_id,
            user_name=req.name,
            user_country=req.country,
            user_position=req.position,
            rng_seed=req.seed
        )
    else:
        # Fallback to procedural generator if no template exists
        generator = WorldGenerator(seed=req.seed)
        active_world = generator.generate_fresh_world(
            user_name=req.name,
            user_country=req.country,
            user_position=req.position
        )
        
    storage.save_world(active_world)
    
    user = active_world.get_user_player()
    user_club = active_world.get_user_club()
    league = active_world.leagues.get(user_club.league_id) if user_club else None
    
    # Career Origin Prologue Narrative
    origin_story = {
        "title": f"The Genesis: {user.name}'s Rise from the Academy",
        "player_name": user.name,
        "age": user.age,
        "position": user.position.value,
        "country": user.country,
        "club_name": user_club.name if user_club else "Top Club",
        "club_country": user_club.country if user_club else "Europe",
        "league_name": league.name if league else "Top Flight",
        "infrastructure_level": user_club.infrastructure_level if user_club else 1,
        "narrative": (
            f"At 17 years of age, {user.name} has officially completed graduation from the youth academy of {user_club.name if user_club else 'the club'} "
            f"in {league.name if league else 'the premier league'} ({league.country if league else 'Europe'}). "
            f"Equipped with an initial rating of {user.overall_rating} and a high ceiling potential, the manager has handed {user.name} "
            f"the starting number in the first team. The world of 10 global leagues and 200 historic clubs lies ahead."
        )
    }
    
    # Execute and generate Stage 1 live simulation screen directly
    init_screen = engine.execute_current_stage(active_world)
    active_screen = init_screen
    storage.save_screen_document(active_world.world_id, 1, 1, init_screen)
    storage.save_world(active_world)
    
    return {
        "world_id": active_world.world_id,
        "user_player": user.model_dump() if user else None,
        "user_club": user_club.model_dump() if user_club else None,
        "league_name": league.name if league else "",
        "league_country": league.country if league else "",
        "origin_story": origin_story,
        "current_season": active_world.current_season,
        "current_stage": active_world.current_stage
    }

@app.get("/api/world/state")
def get_world_state():
    world = _get_active_world()
    user = world.get_user_player()
    user_club = world.get_user_club()
    league = world.leagues.get(user_club.league_id) if user_club else None
    
    return {
        "world_id": world.world_id,
        "current_season": world.current_season,
        "current_stage": world.current_stage,
        "is_career_ended": world.is_career_ended,
        "user_player": user.model_dump() if user else None,
        "user_club": user_club.model_dump() if user_club else None,
        "league_name": league.name if league else "",
        "league_country": league.country if league else "",
        "pending_offers": [o.model_dump() for o in world.pending_user_offers]
    }

@app.get("/api/game/current-screen")
def get_current_screen():
    global active_screen
    world = _get_active_world()
    if active_screen:
        return active_screen
    
    # Check if a screen document exists for current season & stage
    target_stage = world.current_stage - 1 if world.current_stage > 1 else 1
    screen = storage.get_screen_document(world.world_id, world.current_season, target_stage)
    if not screen:
        screen = engine.execute_current_stage(world)
        screen_stage = screen.get("stage", world.current_stage)
        screen_season = screen.get("season_year", world.current_season)
        storage.save_screen_document(world.world_id, screen_season, screen_stage, screen)
        storage.save_world(world)
    active_screen = screen
    return screen

@app.post("/api/game/next-step")
def advance_next_step():
    global active_screen
    world = _get_active_world()
    if world.is_career_ended:
        return {"message": "Career has concluded.", "is_career_ended": True}
        
    screen = engine.execute_current_stage(world)
    active_screen = screen
    screen_stage = screen.get("stage", world.current_stage)
    screen_season = screen.get("season_year", world.current_season)
    storage.save_screen_document(world.world_id, screen_season, screen_stage, screen)
    storage.save_world(world)
    
    return {
        "current_stage": world.current_stage,
        "current_season": world.current_season,
        "screen": screen
    }

@app.post("/api/game/choice")
def submit_user_choice(req: UserChoiceRequest):
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User player not found.")
        
    if req.choice_type == "transfer":
        if req.selected_offer_id:
            # Find chosen offer
            chosen_offer = next(
                (o for o in world.pending_user_offers if o.offer_id == req.selected_offer_id), 
                None
            )
            if not chosen_offer:
                raise HTTPException(status_code=400, detail="Offer not found.")
                
            # Remove from old club roster
            if user.contract and user.contract.club_id in world.clubs:
                old_club = world.clubs[user.contract.club_id]
                if user.id in old_club.player_ids:
                    old_club.player_ids.remove(user.id)
                # Buyer pays compensation fee to seller
                old_club.budget += chosen_offer.compensation_fee
                
            # Add to new club
            new_club = world.clubs[chosen_offer.club_id]
            new_club.budget = max(0, new_club.budget - chosen_offer.compensation_fee)
            if user.id not in new_club.player_ids:
                new_club.player_ids.append(user.id)
            new_club.signings_this_window += 1
            
            user.contract = Contract(
                club_id=new_club.id,
                club_name=new_club.name,
                years_remaining=chosen_offer.contract_years,
                total_years=chosen_offer.contract_years
            )
            
            # Record milestone
            from src.engine.models import MilestoneEvent
            user.milestones.append(MilestoneEvent(
                season_year=world.current_season,
                age=user.age,
                category="transfer",
                title=f"Transferred to {new_club.name}" if not chosen_offer.is_renewal else f"Extended Contract with {new_club.name}",
                description=chosen_offer.contextual_reason,
                club_name=new_club.name
            ))
            
        world.pending_user_offers = []
        storage.save_world(world)
        return {"status": "success", "new_club": user.contract.club_name if user.contract else "Free Agent"}
        
class LifestyleActionRequest(BaseModel):
    action_type: str # "buy_property", "sign_sponsorship", "family_action"
    item_id: Optional[str] = None
    sub_action: Optional[str] = None
    custom_name: Optional[str] = None
    backstory_id: Optional[str] = None

@app.post("/api/game/lifestyle-action")
def perform_lifestyle_action(req: LifestyleActionRequest):
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User player not found.")
        
    from src.engine.models import MilestoneEvent
    from src.engine.names_database import RELATIONSHIP_BACKSTORIES
    club_name = user.contract.club_name if user.contract else "Free Agent"
    
    if req.action_type == "buy_property":
        cost_map = {
            "prop_penthouse": (2.5, "🏢 Metropolitan Skyline Penthouse", "Acquired Skyline Penthouse", "Purchased a luxury city penthouse overlooking the metropolis skyline."),
            "prop_villa": (8.0, "🏡 Azure Coastline Seaside Villa", "Acquired Seaside Estate", "Purchased a luxury private Mediterranean coastal estate for rest and focus."),
            "prop_lab": (6.0, "🧬 Biomechanic Cryo-Recovery Lab", "Commissioned Cryo-Recovery Lab", "Built state-of-the-art hyperbaric chambers and cryo facilities, decelerating veteran physical decline."),
            "prop_foundation": (4.0, "⚽ Horizon Grassroots Football Foundation", "Launched Grassroots Foundation", "Established a charitable grassroots youth soccer academy and training foundation."),
            "inv_vc": (3.0, "📈 Apex Venture Growth Capital Fund", "Invested in Venture Fund", "Direct equity investment in early-stage technology and sports innovation startups."),
            "inv_supercars": (1.8, "🏎️ Exotic High-Performance Hypercar Fleet", "Acquired Hypercar Collection", "Curated collection of bespoke track-ready and luxury grand tourer vehicles.")
        }
        if req.item_id not in cost_map:
            raise HTTPException(status_code=400, detail="Invalid property ID.")
            
        cost, prop_name, m_title, m_desc = cost_map[req.item_id]
        if user.net_worth < cost:
            raise HTTPException(status_code=400, detail=f"Insufficient net worth (€{user.net_worth:.1f}M / €{cost:.1f}M required).")
            
        user.net_worth = round(user.net_worth - cost, 2)
        if prop_name not in user.properties:
            user.properties.append(prop_name)
        if req.item_id == "prop_lab":
            user.has_private_lab = True
        if req.item_id == "prop_foundation" and prop_name not in user.charities:
            user.charities.append(prop_name)
            
        user.milestones.append(MilestoneEvent(
            season_year=world.current_season,
            age=user.age,
            category="milestone",
            title=m_title,
            description=m_desc,
            club_name=club_name
        ))
        storage.save_world(world)
        return {"status": "success", "message": f"Successfully purchased {prop_name}!", "net_worth": user.net_worth}
        
    elif req.action_type == "sign_sponsorship":
        spons_map = {
            "spons_boot": (70, 1.5, "⚡ AeroStrike Pro Footwear Partnership", "Signed AeroStrike Boot Endorsement", "Signed a marquee global signature boot deal with AeroStrike Pro Footwear."),
            "spons_watch": (80, 4.0, "⌚ Chronos Geneva Horology Ambassador", "Chronos Watch Ambassador", "Named global ambassador for Chronos Haute Horlogerie luxury timepieces."),
            "spons_global": (88, 10.0, "🌐 OmniTech Global Brand Icon", "OmniTech Global Campaign Face", "Prime digital and billboard campaign face for OmniTech Global Conglomerate.")
        }
        if req.item_id not in spons_map:
            raise HTTPException(status_code=400, detail="Invalid sponsorship ID.")
            
        min_ovr, payout, s_name, m_title, m_desc = spons_map[req.item_id]
        if user.overall_rating < min_ovr:
            raise HTTPException(status_code=400, detail=f"Requires minimum overall rating of {min_ovr} (Current: {user.overall_rating}).")
            
        active_ids = [d.get("id") for d in user.sponsorship_deals]
        if req.item_id not in active_ids:
            user.sponsorship_deals.append({
                "id": req.item_id,
                "name": s_name,
                "annual_payout": payout
            })
            user.milestones.append(MilestoneEvent(
                season_year=world.current_season,
                age=user.age,
                category="milestone",
                title=m_title,
                description=m_desc,
                club_name=club_name
            ))
            
        storage.save_world(world)
        return {"status": "success", "message": f"Successfully signed {s_name}!"}
        
    elif req.action_type == "family_action":
        # Helper to find backstory dict
        def find_backstory(bs_id_or_title: Optional[str]):
            if not bs_id_or_title:
                return RELATIONSHIP_BACKSTORIES[0]
            for bs in RELATIONSHIP_BACKSTORIES:
                if bs["id"] == bs_id_or_title or bs["title"] == bs_id_or_title:
                    return bs
            return RELATIONSHIP_BACKSTORIES[0]

        if req.sub_action == "meet_partner":
            partner = req.custom_name or "Elena Rossi"
            backstory = find_backstory(req.backstory_id)
            user.relationship_status = "In a Relationship"
            user.partner_name = partner
            user.partner_backstory = backstory["title"]
            user.partner_origin_story = backstory["description"]
            user.partner_meeting_year = world.current_season
            
            meet_narrative = backstory["meet_narrative"].format(partner=partner)
            user.milestones.append(MilestoneEvent(
                season_year=world.current_season,
                age=user.age,
                category="milestone",
                title=f"Started New Relationship with {partner} 💘",
                description=meet_narrative,
                club_name=club_name
            ))
            storage.save_world(world)
            return {"status": "success", "message": f"Relationship started with {partner} ({backstory['title']})!"}
            
        elif req.sub_action == "get_married":
            partner = user.partner_name or "Partner"
            backstory = find_backstory(user.partner_backstory)
            wedding_narrative = backstory["wedding_narrative"].format(partner=partner)
            user.relationship_status = "Married"
            user.milestones.append(MilestoneEvent(
                season_year=world.current_season,
                age=user.age,
                category="milestone",
                title=f"Wedding & Marriage with {partner} 💍",
                description=wedding_narrative,
                club_name=club_name
            ))
            storage.save_world(world)
            return {"status": "success", "message": f"Married to {partner}!"}
            
        elif req.sub_action == "have_child":
            last_name = user.name.split()[-1] if user.name else "Junior"
            child_default = f"Leo {last_name}" if len(user.children) == 0 else f"Sofia {last_name}"
            child_name = req.custom_name or child_default
            backstory = find_backstory(user.partner_backstory)
            child_narrative = backstory["child_narrative"].format(child=child_name, partner=user.partner_name or 'Partner')
            user.children.append(child_name)
            user.milestones.append(MilestoneEvent(
                season_year=world.current_season,
                age=user.age,
                category="milestone",
                title=f"Welcomed Child {child_name} 👶",
                description=child_narrative,
                club_name=club_name
            ))
            storage.save_world(world)
            return {"status": "success", "message": f"Welcomed {child_name} to the family!"}
            
    return {"status": "ignored"}

@app.get("/api/game/timeline")
def get_player_timeline():
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User player not found.")
    return {
        "player_id": user.id,
        "name": user.name,
        "age": user.age,
        "position": user.position.value,
        "overall_rating": user.overall_rating,
        "career_matches": user.career_matches,
        "career_goals": user.career_goals,
        "career_assists": user.career_assists,
        "career_clean_sheets": user.career_clean_sheets,
        "career_saves": user.career_saves,
        "career_trophies": user.career_trophies,
        "career_ballon_dors": user.career_ballon_dors,
        "market_value_m": user.calculate_market_value(),
        "history": [h.model_dump() for h in user.history],
        "milestones": [m.model_dump() for m in user.milestones]
    }

@app.get("/api/game/comparisons")
def get_player_comparisons():
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Get top 5 peers in same position
    peers = [
        p for p in world.players.values() 
        if p.position == user.position and not p.is_retired and p.id != user.id
    ]
    peers.sort(key=lambda p: p.overall_rating, reverse=True)
    
    return {
        "user_player": user.model_dump(),
        "top_peers": [p.model_dump() for p in peers[:5]]
    }

@app.get("/api/player/{player_id}")
def get_player_details(player_id: str):
    world = _get_active_world()
    if player_id not in world.players:
        raise HTTPException(status_code=404, detail="Player not found.")
    p = world.players[player_id]
    p_dict = p.model_dump()
    if p.contract and p.contract.club_id in world.clubs:
        c = world.clubs[p.contract.club_id]
        p_dict["club_name"] = c.name
        p_dict["club_id"] = c.id
        if c.league_id in world.leagues:
            leg = world.leagues[c.league_id]
            p_dict["league_name"] = leg.name
            p_dict["league_country"] = leg.country
    return p_dict

@app.get("/api/club/{club_id}")
def get_club_details(club_id: str):
    world = _get_active_world()
    if club_id not in world.clubs:
        raise HTTPException(status_code=404, detail="Club not found.")
    c = world.clubs[club_id]
    league = world.leagues.get(c.league_id)
    
    starters_dict = c.get_first_choice_squad(world.players)
    starter_ids = {p.id for p_list in starters_dict.values() for p in p_list}
    
    squad_players = []
    for pid in c.player_ids:
        if pid in world.players:
            p_data = world.players[pid].model_dump()
            p_data["is_starter"] = pid in starter_ids
            p_data["is_user"] = (pid == world.user_player_id)
            squad_players.append(p_data)
            
    # Sort squad: starting 11 first, then by rating desc
    squad_players.sort(key=lambda p: (1 if p["is_starter"] else 0, p["overall_rating"]), reverse=True)
    
    return {
        "club": c.model_dump(),
        "league_name": league.name if league else "Unknown League",
        "league_country": league.country if league else "Europe",
        "squad": squad_players,
        "starter_count": len(starter_ids),
        "total_squad_count": len(squad_players)
    }

@app.get("/api/game/my-club")
def get_user_club_details():
    world = _get_active_world()
    user_club = world.get_user_club()
    if not user_club:
        raise HTTPException(status_code=404, detail="User is currently a free agent.")
    return get_club_details(user_club.id)

@app.get("/api/world/clubs")
def get_all_world_clubs():
    world = _get_active_world()
    result = []
    for lid, league in world.leagues.items():
        league_clubs = []
        for cid in league.club_ids:
            if cid in world.clubs:
                c = world.clubs[cid]
                league_clubs.append({
                    "id": c.id,
                    "name": c.name,
                    "short_name": c.short_name,
                    "country": c.country,
                    "budget": c.budget,
                    "infrastructure_level": c.infrastructure_level,
                    "league_titles": c.league_titles,
                    "tournament_titles": c.tournament_titles,
                    "founded_year": c.founded_year,
                    "stadium_name": c.stadium_name,
                    "stadium_capacity": c.stadium_capacity,
                    "historical_rival": c.historical_rival,
                    "squad_size": len(c.player_ids),
                    "primary_color": c.primary_color,
                    "secondary_color": c.secondary_color
                })
        result.append({
            "league_id": lid,
            "league_name": league.name,
            "league_country": league.country,
            "clubs": league_clubs
        })
    return result

@app.post("/api/saves/manual")
def make_manual_save(req: ManualSaveRequest):
    world = _get_active_world()
    save_rec = storage.create_manual_save(world, req.save_name)
    return {"status": "saved", "save": save_rec}

@app.get("/api/saves")
def list_saves():
    return storage.list_saves()

@app.post("/api/saves/{save_id}/load")
def load_saved_world(save_id: str):
    global active_world, active_screen
    world = storage.load_save(save_id)
    if not world:
        raise HTTPException(status_code=404, detail="Save not found.")
    active_world = world
    active_screen = None
    storage.save_world(active_world)
    return {
        "status": "loaded",
        "world_id": active_world.world_id,
        "current_season": active_world.current_season,
        "current_stage": active_world.current_stage
    }

@app.get("/api/saves/export")
def export_world_json():
    world = _get_active_world()
    return world.model_dump()

@app.post("/api/saves/import")
def import_world_json(req: SaveImportRequest):
    global active_world, active_screen
    try:
        imported_world = WorldState.model_validate(req.world_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    active_world = imported_world
    active_screen = None
    storage.save_world(active_world)
    return {
        "status": "imported",
        "world_id": active_world.world_id,
        "current_season": active_world.current_season,
        "current_stage": active_world.current_stage
    }

def build_retirement_summary(world: WorldState) -> Dict[str, Any]:
    user = world.get_user_player()
    if not user:
        return {}
        
    clubs_map: Dict[str, Dict[str, Any]] = {}
    peak_rating = user.overall_rating
    
    # Process season-by-season history
    for h in user.history:
        c_name = h.club_name or "Free Agent"
        if c_name not in clubs_map:
            clubs_map[c_name] = {
                "club_name": c_name,
                "seasons": [],
                "matches": 0,
                "goals": 0,
                "assists": 0,
                "clean_sheets": 0,
                "ending_ratings": [],
                "trophies": [],
                "awards": [],
                "is_legend": False,
                "legend_title": None
            }
        c_entry = clubs_map[c_name]
        c_entry["seasons"].append(h.season_year)
        c_entry["matches"] += h.matches_played
        c_entry["goals"] += h.goals
        c_entry["assists"] += h.assists
        c_entry["clean_sheets"] += h.clean_sheets
        c_entry["ending_ratings"].append(h.ending_rating)
        c_entry["trophies"].extend(getattr(h, "trophies_won", getattr(h, "trophies", [])))
        c_entry["awards"].extend(getattr(h, "awards_won", getattr(h, "awards", [])))
        if h.ending_rating > peak_rating:
            peak_rating = h.ending_rating

    # If user has current season stats not yet saved in history
    if user.season_matches > 0 and user.contract:
        c_name = user.contract.club_name
        if c_name not in clubs_map:
            clubs_map[c_name] = {
                "club_name": c_name,
                "seasons": [world.current_season],
                "matches": user.season_matches,
                "goals": user.season_goals,
                "assists": user.season_assists,
                "clean_sheets": user.season_clean_sheets,
                "ending_ratings": [user.overall_rating],
                "trophies": [],
                "awards": list(user.season_awards),
                "is_legend": False,
                "legend_title": None
            }

    # Evaluate Tier-Scaled Hall of Fame Legend status per club
    inducted_clubs = []
    for c_name, data in clubs_map.items():
        trophy_count = len(data["trophies"])
        has_bdr = any("Golden Ball" in aw or "Ballon d'Or" in aw for aw in data["awards"])
        
        # Find club entity to get its prestige tier
        club_entity = next((c for c in world.clubs.values() if c.name == c_name), None)
        # Calculate tenure-averaged club tier to prevent both underdog inversion penalties and low-tier loopholes
        if club_entity:
            c_tier_num = club_entity.tier_number
            # If the club reached Tier 1 during tenure but player entered during an underdog era, average tier applies
            tenure_length = len(data["seasons"])
            if trophy_count >= 1 and c_tier_num == 1 and tenure_length <= 5:
                c_tier_num = max(1, min(4, round((c_tier_num + 3) / 2)))
            c_tier_name = club_entity.tier_name
            c_stars = club_entity.tier_stars
        else:
            c_tier_num = 3
            c_tier_name = "⚡ Tier 3 • Mid-Table Established"
            c_stars = "★★★"
        
        data["club_tier"] = c_tier_name
        data["club_stars"] = c_stars
        data["tier_number"] = c_tier_num

        is_legend = False
        reason = ""
        threshold_desc = ""
        
        # Tier-Scaled Legend Threshold Criteria
        if c_tier_num == 1:
            threshold_desc = "Tier 1 Giant Criteria: 200+ Apps (6+ Seasons), 4+ Trophies, 120+ Goals, 70+ Assists, 60+ CS, or World Golden Ball (60+ Apps)"
            if data["matches"] >= 200 and len(data["seasons"]) >= 6:
                is_legend = True
                reason = f"Club Era Pillar & Giant Centurion ({data['matches']} Apps across {len(data['seasons'])} Seasons)"
            elif trophy_count >= 4 and data["matches"] >= 80:
                is_legend = True
                reason = f"Dynasty Silverware Leader ({trophy_count} Trophies Won)"
            elif data["goals"] >= 120:
                is_legend = True
                reason = f"All-Time Giant Goalscoring Icon ({data['goals']} Goals)"
            elif data["assists"] >= 70:
                is_legend = True
                reason = f"All-Time Giant Playmaker Icon ({data['assists']} Assists)"
            elif data["clean_sheets"] >= 60:
                is_legend = True
                reason = f"All-Time Giant Defensive Titan ({data['clean_sheets']} Clean Sheets)"
            elif has_bdr and data["matches"] >= 60:
                is_legend = True
                reason = "World Golden Ball Superstar at Continental Giant"
        elif c_tier_num == 2:
            threshold_desc = "Tier 2 Challenger Criteria: 150+ Apps (5+ Seasons), 3+ Trophies, 85+ Goals, 55+ Assists, 45+ CS, or World Golden Ball (40+ Apps)"
            if data["matches"] >= 150 and len(data["seasons"]) >= 5:
                is_legend = True
                reason = f"Club Pillar & Centurion ({data['matches']} Apps across {len(data['seasons'])} Seasons)"
            elif trophy_count >= 3 and data["matches"] >= 60:
                is_legend = True
                reason = f"Silverware Leader ({trophy_count} Trophies Won)"
            elif data["goals"] >= 85:
                is_legend = True
                reason = f"All-Time Goalscoring Icon ({data['goals']} Goals)"
            elif data["assists"] >= 55:
                is_legend = True
                reason = f"Master Playmaker Icon ({data['assists']} Assists)"
            elif data["clean_sheets"] >= 45:
                is_legend = True
                reason = f"Defensive Wall Icon ({data['clean_sheets']} Clean Sheets)"
            elif has_bdr and data["matches"] >= 40:
                is_legend = True
                reason = "World Golden Ball Superstar at Challenger"
        elif c_tier_num == 3:
            threshold_desc = "Tier 3 Mid-Table Criteria: 120+ Apps (4+ Seasons), 2+ Trophies, 60+ Goals, 40+ Assists, 35+ CS, or World Golden Ball"
            if data["matches"] >= 120 and len(data["seasons"]) >= 4:
                is_legend = True
                reason = f"Loyal Club Centurion ({data['matches']} Apps across {len(data['seasons'])} Seasons)"
            elif trophy_count >= 2 and data["matches"] >= 40:
                is_legend = True
                reason = f"Historic Silverware Era Leader ({trophy_count} Trophies Won)"
            elif data["goals"] >= 60:
                is_legend = True
                reason = f"Goalscoring Hero ({data['goals']} Goals)"
            elif data["assists"] >= 40:
                is_legend = True
                reason = f"Playmaker Hero ({data['assists']} Assists)"
            elif data["clean_sheets"] >= 35:
                is_legend = True
                reason = f"Defensive Wall Hero ({data['clean_sheets']} Clean Sheets)"
            elif has_bdr:
                is_legend = True
                reason = "World Golden Ball Winner at Club"
        else: # Tier 4 Underdog
            threshold_desc = "Tier 4 Underdog Criteria: 100+ Apps (3+ Seasons), 1+ Miracle Trophy (30+ Apps), 40+ Goals, 25+ Assists, or 20+ CS"
            if data["matches"] >= 100 or len(data["seasons"]) >= 3:
                is_legend = True
                reason = f"Underdog Club Savior & Centurion ({data['matches']} Apps across {len(data['seasons'])} Seasons)"
            elif trophy_count >= 1 and data["matches"] >= 30:
                is_legend = True
                reason = f"Miracle Silverware Champion ({trophy_count} Historic Trophy)"
            elif data["goals"] >= 40:
                is_legend = True
                reason = f"Cult Hero Striker ({data['goals']} Goals)"
            elif data["assists"] >= 25:
                is_legend = True
                reason = f"Cult Hero Playmaker ({data['assists']} Assists)"
            elif data["clean_sheets"] >= 20:
                is_legend = True
                reason = f"Cult Hero Defensive Pillar ({data['clean_sheets']} Clean Sheets)"
            elif has_bdr:
                is_legend = True
                reason = "World Golden Ball Winner at Underdog"
            
        data["threshold_desc"] = threshold_desc

        if is_legend:
            data["is_legend"] = True
            data["legend_title"] = reason
            inducted_clubs.append({
                "club_name": c_name,
                "club_tier": c_tier_name,
                "club_stars": c_stars,
                "reason": reason,
                "matches": data["matches"],
                "goals": data["goals"],
                "assists": data["assists"],
                "trophies": trophy_count
            })
            
            # Formally induct into club model's Hall of Fame legends list
            for club in world.clubs.values():
                if club.name == c_name:
                    already_inducted = any(l.player_id == user.id for l in club.legends)
                    if not already_inducted:
                        from src.engine.models.club import ClubLegend
                        years_str = f"S{min(data['seasons'])}-S{max(data['seasons'])}" if data['seasons'] else f"Season {world.current_season}"
                        club.legends.append(ClubLegend(
                            player_id=user.id,
                            name=user.name,
                            country=user.country,
                            position=user.position.value,
                            years_active=years_str,
                            matches=data["matches"],
                            goals=data["goals"],
                            assists=data["assists"],
                            trophies=trophy_count,
                            legacy_score=round(float(user.overall_rating) * 1.25, 1)
                        ))

    # Evaluate League Legend Status
    leagues_map: Dict[str, Dict[str, Any]] = {}
    for c_name, c_data in clubs_map.items():
        found_league = None
        for lg in world.leagues.values():
            if any(world.clubs[cid].name == c_name for cid in lg.club_ids if cid in world.clubs):
                found_league = lg
                break
        
        if found_league:
            l_name = found_league.name
            if l_name not in leagues_map:
                leagues_map[l_name] = {
                    "league_name": l_name,
                    "country": found_league.country,
                    "matches": 0,
                    "goals": 0,
                    "assists": 0,
                    "clean_sheets": 0,
                    "titles": 0,
                    "awards_count": 0
                }
            leagues_map[l_name]["matches"] += c_data["matches"]
            leagues_map[l_name]["goals"] += c_data["goals"]
            leagues_map[l_name]["assists"] += c_data["assists"]
            leagues_map[l_name]["clean_sheets"] += c_data["clean_sheets"]
            leagues_map[l_name]["titles"] += sum(1 for t in c_data["trophies"] if "Division" in t or "Liga" in t or "Campionato" in t or "Championnat" in t or "Title" in t or "Champions" in t)
            leagues_map[l_name]["awards_count"] += len([a for a in c_data["awards"] if l_name in a or "Player of the Season" in a or "Team of the Season" in a])

    inducted_leagues = []
    for l_name, l_data in leagues_map.items():
        is_lg_legend = False
        lg_reason = ""
        if l_data["matches"] >= 220:
            is_lg_legend = True
            lg_reason = f"League Centurion & Iron Man ({l_data['matches']} Appearances)"
        elif l_data["titles"] >= 4:
            is_lg_legend = True
            lg_reason = f"League Dynasty Titan ({l_data['titles']} Domestic League Titles)"
        elif l_data["goals"] >= 100:
            is_lg_legend = True
            lg_reason = f"All-Time League Centurion Scorer ({l_data['goals']} Goals)"
        elif l_data["assists"] >= 65:
            is_lg_legend = True
            lg_reason = f"All-Time Master Playmaker ({l_data['assists']} Assists)"
        elif l_data["clean_sheets"] >= 60:
            is_lg_legend = True
            lg_reason = f"All-Time League Defensive Titan ({l_data['clean_sheets']} Clean Sheets)"
        elif l_data["awards_count"] >= 4:
            is_lg_legend = True
            lg_reason = f"Multi-Award League Dominator ({l_data['awards_count']} POTY / TOTS Awards)"
            
        if is_lg_legend:
            inducted_leagues.append({
                "league_name": l_name,
                "country": l_data["country"],
                "reason": lg_reason,
                "matches": l_data["matches"],
                "goals": l_data["goals"],
                "assists": l_data["assists"],
                "titles": l_data["titles"]
            })

    # Evaluate Continental Tournament Legend Status
    tourn_trophies = sum(1 for h in user.history for t in getattr(h, "trophies_won", getattr(h, "trophies", [])) if "Continental" in t or "Cup" in t or "Champions" in t or "Europa" in t)
    tourn_awards = [a for h in user.history for a in getattr(h, "awards_won", getattr(h, "awards", [])) if "Continental" in a or "Tournament" in a]
    has_tourn_pott = any("Player of the Tournament" in a for a in tourn_awards)
    has_tourn_boot = any("Continental Golden Boot" in a for a in tourn_awards)
    
    inducted_tournaments = []
    if tourn_trophies >= 2 and len(user.history) >= 4:
        inducted_tournaments.append({
            "competition": "Continental Cup of Champions",
            "reason": f"Multi-Time European Champion ({tourn_trophies} Continental Trophies Won)"
        })
    elif has_tourn_pott and tourn_trophies >= 1:
        inducted_tournaments.append({
            "competition": "Continental Cup of Champions",
            "reason": "Continental Tournament MVP & Champion"
        })
    elif has_tourn_boot and tourn_trophies >= 1:
        inducted_tournaments.append({
            "competition": "Continental Cup of Champions",
            "reason": "Continental Golden Boot Top Scorer & Champion"
        })

    # Evaluate Global World Immortal Status
    world_hall_of_fame = None
    has_world_golden_ball = user.career_ballon_dors > 0
    is_god_level = peak_rating >= 93
    world_xi_count = sum(1 for h in user.history for a in getattr(h, "awards_won", getattr(h, "awards", [])) if "World Dream XI" in a or "FIFPRO" in a)
    
    if user.career_ballon_dors >= 2 or (is_god_level and user.career_trophies >= 6 and world_xi_count >= 3) or (has_world_golden_ball and user.career_trophies >= 4 and world_xi_count >= 2):
        reasons = []
        if has_world_golden_ball:
            reasons.append(f"{user.career_ballon_dors}x World Golden Ball Winner")
        if is_god_level:
            reasons.append(f"God-Level Rating Peak ({peak_rating} OVR)")
        if world_xi_count > 0:
            reasons.append(f"{world_xi_count}x World Dream XI Selections")
        if user.career_trophies >= 4:
            reasons.append(f"{user.career_trophies} Career Trophies")
            
        world_hall_of_fame = {
            "title": "👑 Immortal Legend of World Football",
            "reason": " • ".join(reasons) if reasons else "Transcendent Global Icon"
        }

    # Evaluate National Team / International Legend Status
    inducted_international = []
    intl_trophies_count = len(user.international_trophies) if isinstance(user.international_trophies, list) else int(user.international_trophies)
    if user.international_caps >= 50 or user.international_goals >= 25 or intl_trophies_count >= 1:
        reasons = []
        if user.international_caps >= 100:
            reasons.append(f"International Centurion ({user.international_caps} Caps)")
        elif user.international_caps >= 50:
            reasons.append(f"National Legend ({user.international_caps} Caps)")
        if user.international_goals >= 30:
            reasons.append(f"All-Time Top Scorer ({user.international_goals} Int'l Goals)")
        elif user.international_goals >= 15:
            reasons.append(f"{user.international_goals} International Goals")
        if intl_trophies_count > 0:
            reasons.append(f"{intl_trophies_count}x International Champion")
        if user.is_national_team_captain:
            reasons.append("National Team Captain")
            
        inducted_international.append({
            "country": user.country,
            "reason": " • ".join(reasons) if reasons else f"Honored International for {user.country}",
            "caps": user.international_caps,
            "goals": user.international_goals,
            "assists": user.international_assists,
            "trophies": intl_trophies_count
        })

    return {
        "player_id": user.id,
        "player_name": user.name,
        "country": user.country,
        "position": user.position.value,
        "age": user.age,
        "final_rating": user.overall_rating,
        "peak_rating": peak_rating,
        "total_seasons": len(user.history) + (1 if user.season_matches > 0 else 0),
        "career_matches": user.career_matches,
        "career_goals": user.career_goals,
        "career_assists": user.career_assists,
        "career_clean_sheets": user.career_clean_sheets,
        "career_saves": user.career_saves,
        "career_trophies": user.career_trophies,
        "career_ballon_dors": user.career_ballon_dors,
        "international_caps": user.international_caps,
        "international_goals": user.international_goals,
        "international_assists": user.international_assists,
        "international_trophies": user.international_trophies,
        "national_team_status": user.national_team_status,
        "is_national_team_captain": user.is_national_team_captain,
        "clubs_played_for": list(clubs_map.values()),
        "inducted_clubs": inducted_clubs,
        "inducted_leagues": inducted_leagues,
        "inducted_tournaments": inducted_tournaments,
        "inducted_international": inducted_international,
        "world_hall_of_fame": world_hall_of_fame,
        "milestones": [m.model_dump() for m in user.milestones]
    }

@app.get("/api/world/international/tournament")
def get_international_tournament():
    world = _get_active_world()
    active_tourn = world.active_international_tournament
    history = world.international_history
    return {
        "active_tournament": active_tourn.model_dump() if active_tourn else None,
        "history_count": len(history),
        "recent_tournaments": [t.model_dump() for t in history[-5:]] if history else []
    }

@app.get("/api/player/national-team")
def get_player_national_team():
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User player not found.")
        
    nt = world.national_teams.get(user.country)
    squad_players = []
    if nt and nt.squad_player_ids:
        for pid in nt.squad_player_ids:
            p = world.get_player(pid)
            if p:
                squad_players.append({
                    "id": p.id,
                    "name": p.name,
                    "position": p.position.value,
                    "rating": p.overall_rating,
                    "form": getattr(p, "form", round(p.season_goals * 0.4 + p.season_assists * 0.3, 1)),
                    "club": p.contract.club_name if p.contract else "Free Agent",
                    "caps": p.international_caps,
                    "goals": p.international_goals,
                    "is_user": p.is_user
                })
        # Sort squad by rating descending
        squad_players.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "country": user.country,
        "national_team": nt.model_dump() if nt else None,
        "user_status": user.national_team_status,
        "is_captain": user.is_national_team_captain,
        "caps": user.international_caps,
        "goals": user.international_goals,
        "assists": user.international_assists,
        "trophies": user.international_trophies,
        "squad": squad_players
    }

@app.post("/api/game/action/retire")
def retire_player():
    world = _get_active_world()
    user = world.get_user_player()
    if not user:
        raise HTTPException(status_code=404, detail="User player not found.")
    
    user.is_retired = True
    world.is_career_ended = True
    summary = build_retirement_summary(world)
    storage.save_world(world)
    return {"status": "retired", "summary": summary}

@app.get("/api/game/retirement-summary")
def get_retirement_summary():
    world = _get_active_world()
    return build_retirement_summary(world)

