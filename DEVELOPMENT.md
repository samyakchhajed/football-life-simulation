# Development Guide — football-life-simulation

This document provides a comprehensive technical guide for local setup, software architecture, core simulation mechanics, and statistical validation of **football-life-simulation** (Track A). For AWS cloud infrastructure, CI/CD pipelines, and production deployment runbooks, see [DEPLOYMENT.md](DEPLOYMENT.md).

> **Project Status:** **COMPLETE & VERIFIED (DONE)**  
> All phases across Track A (Simulation Engine & Web UI) and Track B (Cloud Infrastructure, EKS Batch Worlds, Serverless Web App) are fully implemented, verified in production, and documented.

---

## 1. Project Evolution & Engineering Roadmap

The project is structured across six sequential phases to guarantee clean domain boundaries, instant local playability, and progressive cloud delivery:

```text
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Local Simulation Core (Track A) [COMPLETED]       │
│  • Pure Python Poisson engine & seeded determinism          │
│  • Player development curves, traits, injuries & awards     │
│  • Hard integrity checker & statistical validation suite    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 2: Zero-Build Web UI & Local Playability [COMPLETED] │
│  • Vanilla HTML5, modern CSS custom properties & ES Modules │
│  • 8-stop season flow, career reports, timeline & lifestyle │
│  • Local FastAPI backend with JSON file storage adapter     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 3: World Factory & 100-Season Template Pool [DONE]   │
│  • 10 global leagues, 200 clubs & 4,000 players             │
│  • 100-season burn-in runner & template manager pool        │
│  • Automated validation gate & invariant verification       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phases 4–6: Cloud Infrastructure & EKS Delivery [VERIFIED] │
│  • 4-Layer Terraform IaC & 6 decoupled GitHub Actions CI/CD │
│  • EKS Kubernetes indexed batch jobs & S3 template upload   │
│  • AWS Lambda FastAPI Function URL & S3 static web app      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Local Setup & Running Guide (Zero Cloud Dependency)

The application is 100% playable and testable on a local development machine with no cloud connections, AWS credentials, or external database installations.

### 2.1 Directory Layout & Prerequisites
- Python 3.11+
- Modern Web Browser (Chrome, Firefox, Edge, Safari)

```text
football-life-simulation/
├── requirements.txt            # Python dependencies (FastAPI, Uvicorn, Pydantic)
├── data/
│   └── templates/              # Persistent 100-season pre-simulated world templates
├── scripts/
│   ├── run_100_season_burnin.py # CLI 100-season burn-in & Quality Gates audit runner
│   └── package_lambda.py       # Serverless package bundler
├── src/
│   ├── engine/                 # Pure Python Simulation Engine
│   │   ├── models/             # Player, Club, League, Contract, Injury, Award, WorldState, International
│   │   ├── traits.py           # 15+ tactical playstyles and traits engine
│   │   ├── match_sim.py        # Poisson distribution, traits & event assignment
│   │   ├── international_engine.py # National teams, 23-man call-ups & 4-year summer cycle
│   │   ├── development.py      # Progression, aging curves & cryo-lab mitigation
│   │   ├── injury_system.py    # Injury rolls & durations
│   │   ├── youth_system.py     # Infrastructure-weighted youth intakes
│   │   ├── transfer_market.py  # AI transfers, contextual bidding & roles
│   │   ├── awards.py           # League awards & World Golden Ball calculation
│   │   ├── storylines.py       # Living world narrative generator
│   │   ├── names_database.py   # 22 nationalities authentic name database
│   │   ├── integrity.py        # Hard invariants & integrity validator
│   │   └── season_workflow.py  # 8-stop season state machine & 32-team tournament
│   ├── world_factory/
│   │   ├── generator.py        # Seeded generator (10 leagues, 200 clubs, 4000 players)
│   │   ├── burnin_runner.py    # 100-season offline burn-in runner
│   │   └── template_manager.py # Pre-simulated template pool manager
│   └── api/
│       ├── storage.py          # Local JSON S3/DDB simulation adapter (.local_data/)
│       ├── lambda_handler.py   # Serverless Mangum ASGI handler
│       └── main.py             # FastAPI REST endpoints
└── frontend/
    ├── index.html              # Single-page interface
    ├── css/
    │   ├── variables.css       # Design tokens & color system
    │   ├── cards.css           # Card styles & rating tiers
    │   └── main.css            # Layouts, tables, modals & stepper
    └── js/
        ├── api_client.js       # Asynchronous HTTP API client
        └── app.js              # Application controller & 8-stage renderers
```

### 2.2 Environment Setup
```bash
# 1. Clone repository and navigate to workspace
cd football-life-simulation

# 2. Set up Python virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install core dependencies
pip install -r requirements.txt
```

---

### 2.3 Running the Backend Service Locally
The local API uses a local filesystem storage adapter (`LOCAL_STORAGE=true`) that emulates S3 saves and DynamoDB caches using local JSON files in `.local_data/`:

```bash
# Start local API with auto-reload
python -m uvicorn src.api.main:app --reload --port 8000
```
- **API Swagger Documentation:** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/healthz`

---

### 2.4 Running the Web Game Frontend Locally
```bash
# Serve the static frontend
cd frontend
python -m http.server 3000
```
Open **`http://localhost:3000`** in your browser. The frontend automatically interacts with `http://localhost:8000` for simulation calls.

---

## 3. Core Simulation Architecture (Track A)

### 3.1 Match Simulation (Poisson Distribution & Playstyles)
Matches are simulated without minute-by-minute loops using a Poisson goal distribution:
1. **Team Strength Computation:**
   $$\text{Attack Strength} = \sum_{\text{starting FWD/MID}} \text{Player Attack Score} + \text{Home Advantage}$$
   $$\text{Defense Strength} = \sum_{\text{starting GK/DEF}} \text{Player Defense Score}$$
2. **Expected Goals ($\lambda$):**
   $$\lambda_{\text{home}} = f(\text{Attack}_{\text{home}}, \text{Defense}_{\text{away}})$$
   $$\lambda_{\text{away}} = f(\text{Attack}_{\text{away}}, \text{Defense}_{\text{home}})$$
3. **Goal & Assist Assignment:**
   - **Goals:** ~72% of total team goals are allocated to forwards using a non-linear power curve on attacking attributes (`(p.attacking / 70.0) ** 2.2`) modulated by playstyle traits (Clinical Finisher $+35\%$, Rapid Counter-Poacher $+25\%$, Big-Game Clutch DNA $+25\%$ in deciders). World-class starting forwards score 20–35 goals across a 38-game season, established forwards score 14–22 goals, and rotational forwards score 8–13 goals.
   - **Assists:** Allocated across positions (~58% MID, ~28% FWD, ~13% DEF) using playmaking power curves (`(p.playmaking / 70.0) ** 2.0`) amplified by playstyles (Midfield Maestro $+45\%$, Dead-Ball Specialist $+30\%$).
4. **Defensive Credits:**
   - Goalkeepers and defenders on the starting lineup receive clean sheet credits and goals-conceded tracking. Goalkeepers accumulate saves and save percentage derived from opponent shot volume, enhanced by Acrobatic Wall and Sweeper Keeper.

---

### 3.2 8-Stop Season State Machine & International Summer Cycle
Each season progresses through 8 discrete stages, writing precomputed documents:

```text
[1. League Season] ──► [2. Tournament Qualified] ──► [3. Tournament Results & Int'l Cup] ──► [4. Awards Ceremony]
                                                                                                       │
[8. New Season Launchpad] ◄── [7. Transfer Window] ◄── [6. Offseason Choices] ◄── [5. Season Summary]
```

- **Stop 1 (League Season):** Simulates 38-round double round-robin across all 10 domestic leagues (England, Spain, Italy, Germany, France, Brazil, Argentina, USA, Japan, India).
- **Stop 2 (Tournament Qualification):** Qualifies Top 3 teams from each of the 10 domestic leagues plus the best two 4th-placed teams ($32$ clubs total) for the Continental Champions Trophy.
- **Stop 3 (Continental Champions Trophy & Summer International Championship):**
  - Simulates 5 knockout rounds (`Round of 32` $\to$ `Round of 16` $\to$ `Quarter-Finals` $\to$ `Semi-Finals` $\to$ `Final`).
  - **Summer International Championship:** Concurrently simulates the international football cycle for 16 national teams based on a 4-year quadrennial rotation:
    - *Season % 4 == 1:* International Qualifiers & Summer Series
    - *Season % 4 == 2:* Continental Nations Cup (16-Team Knockout)
    - *Season % 4 == 3:* Nations League Finals (Final Four)
    - *Season % 4 == 0:* Global World Championship (World Cup)
  - Selects 23-man rosters dynamically from 75% overall rating and 25% normalized season form, appoints captains, simulates Poisson international scorelines, logs individual caps/goals/assists, and crowns the Golden Boot Top Scorer.
- **Stop 4 (Awards Gala):** Computes domestic positional awards and TOTS for all 10 leagues, alongside Continental MVP and the World Golden Ball / World Dream XI.
- **Stop 5 (Season Summary & Career Report):** Highlights seasonal rating changes, market-value deltas, position ranking, milestone badges, contextual rival/benchmark comparisons, and living world news stories.
- **Stop 6 (Offseason Decisions & Lifestyle):** Displays contract status, salary packages, and generates transfer fee bids across 4 prestige tiers (`Tier 1 ★★★★★`, `Tier 2 ★★★★`, `Tier 3 ★★★`, `Tier 4 ★★`) with **expected playing roles** (Guaranteed Starter, Impact Sub / Rotation, Squad Depth / Backup). Manages commercial endorsements, property acquisitions, cryo-lab upgrades, and family milestones.
- **Stop 7 (Transfer Window):** Confirms active contract terms, executes AI club moves adhering to the 5-signings cap, cleanses seller rosters, pays compensation fees to seller budgets, and stabilizes all squads.
- **Stop 8 (New Season Launchpad):** Displays annual performance review (matches, goals, assists, G+A total), synchronized backend performance tier badge (Stellar Campaign (+5 OVR), Veteran Age Decline (-1 OVR), Elite Veteran Longevity (+0 OVR), Potential Ceiling Reached (+0 OVR)), and exact rating change ($prev \to new$) before prompting the user with a dynamic call-to-action button to simulate the next 38 league matches.

---

### 3.3 Domestic Home Country Youth Academy Rule & Transfer Gating
- **Academy Graduation:** Every created footballer strictly starts their career at age 17 graduating from a domestic youth academy within their selected home country.
- **Development Gating:** During their initial 2–3 development seasons ($\text{age} \le 19, \text{OVR} < 76$), transfer offers for both user and AI prospects are restricted to domestic clubs until players prove their quality ($\ge 76$ OVR or age 20+) to unlock international moves.

---

### 3.4 Performance-Driven Player Progression
Attribute growth is calculated strictly from on-pitch match contributions:
- **Forwards (FWD):** $\ge 26$ G+A $\to$ raw +5; $16-25 \to$ raw +3; $8-15 \to$ raw +1; $<8 \to 0$.
- **Midfielders (MID):** $\ge 20$ G+A (or $\ge 14$ with $\ge 30$ matches) $\to$ raw +5; $12-19 \to$ raw +3; $6-11 \to$ raw +1.
- **Defenders & Goalkeepers (DEF / GK):** $\ge 30$ matches & $\ge 13$ clean sheets $\to$ raw +5; $\ge 25$ matches & $\ge 8$ clean sheets $\to$ raw +3; $\ge 18$ matches & $\ge 4$ clean sheets $\to$ raw +1.
- **Rating Tier Resistance & Aging:** Diminishing returns above 78 OVR (max +1 at 85+ OVR). Graceful veteran aging (ages 33+) with 0 OVR decline for exceptional superstars (Elite Veteran Longevity) and cryo-lab mitigation.

---

### 3.5 Living World Storylines Engine
Procedurally generates narrative events from simulation data:
- **Dynasty Declines:** Identifies multi-year championship clubs falling outside the top 4.
- **Wonderkid Breakthroughs:** Highlights teenage players breaking into starting lineups with top-scorer or top-assister performances.
- **Rebuilding Turnarounds:** Highlights low-ranked clubs making major transfer acquisitions and surging up league tables.
- **All-Time Records:** Triggers headlines when career goal, assist, or trophy records are broken.

---

### 3.6 Integrity & Statistical Quality Gates (Gates 1–9)

Executed automatically during the 100-season offline burn-in runner:
```bash
python scripts/run_100_season_burnin.py --seed 77
```

- **Hard Invariants (Gates 1–4):**
  - **Gate 1:** Squad size strictly between 18 and 22 players.
  - **Gate 2:** Positional balance: Minimum 2 GK, 6 DEF, 6 MID, 4 FWD per club.
  - **Gate 3:** Zero negative club balances after transfers and payroll.
  - **Gate 4:** Single-club registration invariant: Every player belongs to at most one club's active roster.
- **Statistical Quality Gates (Gates 5–9):**
  - **Gate 5 (Strength vs Results):** Spearman rank correlation ($\overline{\rho} \ge 0.50$) between pre-season squad strength and final league standings.
  - **Gate 6 (Club Stability):** Mean position change ($\le 3.5$ spots) and wild swings ($\ge 8$ spots $\le 10\%$).
  - **Gate 7 (No Out-of-Nowhere Champions):** Champions from outside top 6 pre-season ranked squads capped at $\le 5\%$.
  - **Gate 8 (Dynasty Cap Audit):** Longest consecutive title runs audited across all 10 leagues (no more than 8 consecutive titles).
  - **Gate 9 (Player Stat Stability & Monotonicity):** Extreme G+A swings ($\ge 20$ delta with $\le 1$ OVR change) capped at $\le 8\%$, and strict rating bracket monotonicity ($\overline{\text{GA}}_{85+} > \overline{\text{GA}}_{78-84} > \overline{\text{GA}}_{70-77} > \overline{\text{GA}}_{<70}$).
