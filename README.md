# The Football Life Engine

A data-driven single-player career football simulation and Kubernetes infrastructure experiment. Built with a pure Python deterministic simulation engine, a zero-build Vanilla web interface, AWS-managed **EKS**, **Terraform**, **GitHub Actions**, and versioned world-state storage.

> **Project Purpose & Architecture:** The Football Life Engine is designed as a dual-track software engineering showcase:
> - **Part 1 (World Factory on Kubernetes):** Generate 100 independent, 100-season worlds in AWS-managed EKS. Each world uses its own seed and worker workload so Kubernetes scheduling, worker resource pressure, parallelism, autoscaling, observability, and failure recovery can be measured.
> - **Part 2 (Playable Career Game):** Select a validated generated world and run the single-player career simulation across 10 domestic leagues (200 clubs), a 32-team Continental Champions Trophy, and a 16-nation international cycle. This part is playable locally and later becomes the application workload on AWS.
> - Terraform provisions the infrastructure and GitHub Actions provides keyless CI/CD through AWS OIDC. These cloud deployment files are still being built.
>
> The game is fully playable **locally with zero cloud dependencies** (HTML/CSS/JS frontend + Python backend). AWS deployment is the planned Part 1 and Part 2 delivery path.

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRACK A — PLAYABLE GAME (Local / AWS)                                       │
│                                                                                                          │
│   BROWSER (Vanilla HTML5 + CSS + ES Modules)                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐                   │
│   │  8-Stop Season Stepper · Player Card · League Tables · Awards · Timeline        │                   │
│   └──────────────────────────────┬──────────────────────────────────────────────────┘                   │
│                                  │ HTTPS REST (JSON)                                                     │
│                                  ▼                                                                       │
│   GAME API (FastAPI / Uvicorn — Local: port 8000)                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐                   │
│   │  Session state · Stage navigation · Career choices · Saves (export / import)   │                   │
│   │  LOCAL: LocalStorageAdapter (.local_data/)    AWS: Lambda + S3 (Mangum ASGI)     │                   │
│   └──────────────────────────────┬──────────────────────────────────────────────────┘                   │
│                                  │ reads validated template at career start                              │
│                                  ▼                                                                       │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                              STORAGE LAYER (Two-Tier)                                            │  │
│   │                                                                                                  │  │
│   │  Persistent Template Repository           Live World & Session State                             │  │
│   │  ─────────────────────────────            ─────────────────────────                              │  │
│   │  LOCAL  : data/templates/*.json           LOCAL  : .local_data/ (worlds / screens / saves)       │  │
│   │  AWS    : S3  s3://.../templates/         AWS    : S3 (Object Versioning) + DynamoDB             │  │
│   │            DynamoDB template catalog              screen cache (≤90 KB/item) + save index        │  │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRACK B — KUBERNETES WORLD FACTORY (AWS EKS)                                │
│                                                                                                          │
│   GitHub (source of truth)                                                                               │
│       │                                                                                                  │
│       ▼  GitHub Actions (CI/CD — OIDC keyless auth to AWS)                                              │
│       │  • Unit tests + simulation quality gates (goals/match, dynasty audit, rating drift)             │
│       │  • Terraform plan / apply                                                                        │
│       ▼                                                                                                  │
│   Terraform (IaC — Mumbai ap-south-1)                                                                   │
│       Provisions: EKS cluster · node groups · IAM roles · S3 buckets · DynamoDB tables                  │
│       │                                                                                                  │
│       ▼                                                                                                  │
│   AWS-managed EKS — Indexed Kubernetes Job (100 completions, 1 worker per world)                        │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │  Worker N  (seed = base_seed + N)                                                               │  │
│   │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐  │  │
│   │  │  WorldBurnInRunner  (100 seasons · 383,100 matches · ~3-4 min/world)                      │  │  │
│   │  │  → 12 statistical quality gates (Spearman ρ, dynasty cap, goal band, determinism …)       │  │  │
│   │  │  → on PASS: publish template JSON to S3 + metadata to DynamoDB (status: APPROVED)         │  │  │
│   │  │  → on FAIL: record gate report (status: REJECTED) — run is still accounted for            │  │  │
│   │  └───────────────────────────────────────────────────────────────────────────────────────────┘  │  │
│   │  Kubernetes experiments run on this workload:                                                   │  │
│   │  • Parallel scheduling & queue depth      • CPU/memory pressure & pod autoscaling              │  │
│   │  • Pod restart & failed-worker recovery   • Prometheus/Grafana via kubectl port-forward        │  │
│   │  • Node autoscaling under load            • Evidence export → cluster teardown                 │  │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                          │
│   Cloud constraints: Mumbai (ap-south-1) only · $195 credits (expires ~Mar 2027)                        │
│   Never leave unused resources running. Export metrics before teardown.                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities & Engineering Highlights

### Track A — Simulation Engine & Game Experience
- **10 Global Domestic Leagues & 200 Clubs:** Worldwide football ecosystem across Europe, South America, North America, and Asia:
  - Premier Division (England - 20 clubs)
  - Liga Primera (Spain - 20 clubs)
  - Serie Campionato (Italy - 20 clubs)
  - Meister Liga (Germany - 20 clubs)
  - Ligue Championnat (France - 20 clubs)
  - Brasileirao Super Serie (Brazil - 20 clubs)
  - Liga Argentina Primera (Argentina - 20 clubs)
  - Major Soccer Championship (USA - 20 clubs)
  - Japan Super League (Japan - 20 clubs)
  - Indian Super Championship (India - 20 clubs)
- **Domestic Home Country Youth Academy Rule:** Every created footballer strictly starts their career at age 17 graduating from a domestic youth academy within their selected home country. During their initial 2–3 development seasons ($\text{age} \le 19, \text{OVR} < 76$), both user and AI prospect transfer offers are restricted to domestic clubs until players prove their quality ($\ge 76$ OVR or age 20+) to unlock international moves.
- **32-Team Continental Champions Trophy Tournament:** Scaled tournament featuring Top 3 clubs from each of the 10 leagues ($30$) + Best 2 4th-place wildcards ($2$) across a 5-round single-elimination bracket (`Round of 32` $\to$ `Round of 16` $\to$ `Quarter-Finals` $\to$ `Semi-Finals` $\to$ `Final`).
- **International Football & Quadrennial Summer Championship Cycle:**
  - **16 Global National Teams:** Authentic international sides with real flags, FIFA world rankings, and historical tournament counts (England, Spain, Germany, Italy, France, Brazil, Argentina, USA, Japan, India, Netherlands, Portugal, Belgium, Croatia, Uruguay, Mexico).
  - **Dynamic 23-Man Squad Call-ups:** Roster selection calculated annually from 75% overall rating and 25% normalized season form, selecting starting XIs and appointing national team captains based on international caps and veteran status.
  - **4-Year Summer International Tournament Cycle (Simulated in Stage 3):**
    - *Season % 4 == 1:* International Qualifiers & Summer Series
    - *Season % 4 == 2:* Continental Nations Cup (16-Team Knockout)
    - *Season % 4 == 3:* Nations League Finals (Final Four)
    - *Season % 4 == 0:* Global World Championship / World Cup
  - **International Caps & Golden Boot:** Every international match simulates Poisson scorelines, credits individual caps, goals, and assists, awards the Golden Boot Top Scorer, and crowns international champions.
- **12 Statistical Quality & Integrity Gates (Gates 1–12):** Built-in mathematical validation during 100-season template generation:
  - *Gate 1 (Completeness):* Exactly 200 clubs and 4,000 active players.
  - *Gate 2 (Uniqueness):* Global club namespace uniqueness.
  - *Gate 3 (Attribute Bounds):* $40 \le \text{OVR} \le 100$, $17 \le \text{Age} \le 42$.
  - *Gate 4 (Deduplication):* Single-club registration invariant.
  - *Gate 5 (Strength vs Results):* Spearman rank correlation ($\overline{\rho} \ge 0.50$, empirical $\sim 0.54 - 0.57$) between pre-season squad strength and final league standings.
  - *Gate 6 (Club Stability):* Mean position change ($\le 3.5$ spots) and share of large swings ($\ge 8$ spots $\le 10\%$, empirical $\sim 4.0 - 5.5\%$).
  - *Gate 7 (No Out-of-Nowhere Champions):* Champions originating from outside top 6 pre-season ranked squads capped at $\le 5\%$.
  - *Gate 8 (Dynasty Cap Audit):* Tracks and rejects league title streaks longer than 8 consecutive seasons.
  - *Gate 9 (Position-Separated Player Stat Stability & Monotonicity):* Extreme G+A swings capped at $\le 8\%$, with position-separated rating bracket monotonicity:
    - *Attacker Monotonicity (FWD / MID):* $\overline{\text{GA}}_{85+} > \overline{\text{GA}}_{78-84} > \overline{\text{GA}}_{70-77} > \overline{\text{GA}}_{<70}$.
    - *Defender / Goalkeeper Monotonicity (DEF / GK):* $\overline{\text{CS}}_{85+} \ge \overline{\text{CS}}_{78-84} \ge \overline{\text{CS}}_{70-77} \ge \overline{\text{CS}}_{<70}$.
  - *Gate 10 (Schema Compatibility):* Validates full Pydantic model serialization and deserialization across all entities.
  - *Gate 11 (Canonical State Determinism):* Verifies identical SHA-256 hashes before and after a Pydantic serialization round trip.
  - *Gate 12 (Goal Scoring Band Tolerance):* Total league match scoring strictly contained within $[2.30, 3.10]$ goals/match.
- **Signature Playstyles & Tactical Traits Engine:** 15+ position-specific and all-around traits (Clinical Finisher, Rapid Counter-Poacher, Target Man & Hold-Up, Big-Game Clutch DNA, Midfield Maestro, Box-to-Box Engine, Dead-Ball Specialist, Defensive Anchor, Aerial Fortress, Acrobatic Wall, Sweeper Keeper) that directly boost match engine goal conversion, assists, and saves.
- **22 Global Nationalities & Dynamic Name Generator:** Authentic geographic names database (England, Spain, France, Germany, Italy, Portugal, Netherlands, Belgium, Norway, Sweden, Croatia, Denmark, Russia, Brazil, Argentina, Uruguay, Colombia, India, Australia, Japan, South Korea, USA) with country-specific auto-name selection and dice randomization.
- **Stage 6 Offseason Lifestyle, Wealth & Personal Life System:**
  - **Wealth & Wages:** Club salaries paid annually, boosted by silverware bonuses and commercial deals.
  - **Commercial Sponsorships:** Tiered fictional brand partnerships (AeroStrike Pro Footwear Deal at 70+ OVR, Chronos Geneva Watch Ambassador at 80+ OVR, OmniTech Global Campaign Icon at 88+ OVR) generating recurring earnings.
  - **Real Estate, Labs & Financial Investments:** Acquire Metropolitan Penthouses (€2.5M), Azure Seaside Villas (€8.0M), Grassroots Youth Foundations (€4.0M), Venture Growth Funds (€3.0M, variable $-\text{€}0.35\text{M}$ to $+\text{€}0.65\text{M}$ annual return), Exotic Hypercars (€1.8M), and the Biomechanic Cryo-Recovery Lab (€6.0M, significantly mitigates age 33+ veteran decline).
  - **Love Life & Meeting Backstories (5 Origin Archetypes):** Personal life features 5 meeting narrative backstories (Childhood Sweetheart, University & Studies Friend, Grassroots Charity Gala, Serendipitous City Encounter, Creative & Media Professional) with authentic female first and last names tailored to each player's home country.
  - **Family & Life Journey Milestones:** Relationship progression (Start Dating with chosen meeting backstory $\to$ Wedding & Marriage Ceremony $\to$ Welcome Children) seamlessly generates custom narrative milestones in career history and timeline.
- **Pure Python Deterministic Engine:** Poisson-based match engine with compressed star ratings, home advantage, and seeded reproducibility ($\sim 1,500\text{ matches/sec}$).
- **Card UI & Holographic Badging:** Card-based visual presentation across rating tiers (Bronze, Silver, Gold, Elite, World-Class, God-Level) with detailed attribute breakdowns, position badges, and club crests.
- **Club Prestige & Tier Classification:** 200 clubs categorized into 4 mutually exclusive prestige tiers blending sporting form, recent era silverware, and historical heritage floors:
  - Tier 1 — Elite Domestic Heavyweights / Title Contenders (★★★★★): Rolling 3-season rank $\le 4.0$ OR $\ge 2$ Era Silverware Trophies OR ($\ge 25$ lifetime trophies with $\overline{R}_3 \le 6.0$). Commercial Baseline: +€90M (Floor: €80M).
  - Tier 2 — Continental Trophy Challengers (★★★★): Rolling rank 4.1–8.0 OR $\ge 1$ Era Silverware Trophy OR $\ge 15$ lifetime trophies (Historic Titan Floor). Commercial Baseline: +€55M (Floor: €45M).
  - Tier 3 — Mid-Table Established (★★★): Rolling rank 8.1–14.0 OR $\ge 5$ lifetime trophies (Historic Heritage Floor). Commercial Baseline: +€35M (Floor: €25M).
  - Tier 4 — Top-Flight Underdogs (★★): Rolling rank $> 14.0$ with $< 5$ lifetime trophies. Commercial Baseline: +€20M (Floor: €15M).
- **Anti-Ratchet Multi-Decade Facility Depreciation:** Training and youth facilities naturally age down 1 level every 15 seasons without investment, preserving long-term competitive mobility.
- **Authentic 100-Season Simulated History:** Every club features founding years (1885–1928), named stadiums with seating capacities, derby rivals, 100-season simulated championship rolls, historical trophy cabinets, all-time record holders, and retired club legends. Template files ($\sim 35\text{ MB}$ uncompressed / $\sim 6\text{ MB}$ gzipped) deserialize in $\sim 200 - 450\text{ ms}$.
- **Performance-Driven Player Progression & Rating Tier Resistance:** Growth is strictly earned through on-pitch metrics combined with diminishing returns by rating band (God-Level $\ge 92$: max +1; World-Class 85–91: max +1; Elite 78–84: max +2; Established 70–77: max +3; Youth $<70$: up to +5). Forwards require $\ge 26$ G+A for raw 5, Midfielders $\ge 20$ G+A, and Defenders/GKs strictly require $\ge 30$ matches & $\ge 13$ clean sheets. All players can reach up to a maximum potential and overall rating of 100.
- **Graceful Veteran Aging & Exceptional Superstar Longevity (Ages 33+):** Slow gradual decline (-1 OVR max per year) for normal players, while exceptional / generational stars ($\ge 85$ OVR, World Golden Ball winners, or players with $\ge 15$ G+A / $\ge 8$ CS) experience 0 OVR decline (Elite Veteran Longevity), preserving world-class quality well into late 30s.
- **Commercial Baseline & Operating Safety Net Floors:** Clubs receive guaranteed annual commercial baseline revenue based on canonical tier along with guaranteed operating budget floors. Transfer compensation fees are credited on top of the annual baseline, with zero multi-decade unspent budget hoarding.
- **3-Season Form Trajectory & Club Performance Visibility:** Dynamic rolling 3-season performance trajectory badges (Title Contender, Sleeping Giant in Rebuild, Rising Force, Continental Contender, Stable Mid-Table, Battling Relegation) and historical rank sequences (e.g. `1st -> 2nd -> 1st`) displayed on Transfer Bid cards, Club Modals, and the World Directory.
- **Open Transfer Market & Tactical Roles:** Bids from interested clubs are generated every offseason window, complete with expected roles (Guaranteed Starter, Impact Sub / Rotation, Squad Depth / Backup), salary packages, silverware bonuses, buyout release clauses, and transfer compensation fees.
- **Multi-Tier Hall of Fame & Tier-Scaled Legend Recognition:**
  - Tier-Scaled Club Legend: Scaled by club caliber evaluated against tenure-averaged club tier — Tier 1 Giants require era-defining legacy ($\ge 200$ apps, 6+ seasons, $\ge 4$ trophies, $\ge 120$ goals, $\ge 70$ assists, or $\ge 60$ CS), Tier 2 Challengers ($\ge 150$ apps, $\ge 3$ trophies, $\ge 85$ goals), Tier 3 Mid-Table ($\ge 120$ apps, $\ge 2$ trophies, $\ge 60$ goals), Tier 4 Underdogs ($\ge 100$ apps, miracle trophy, $\ge 40$ goals).
  - Domestic League Hall of Fame: Domestic iron-man status ($\ge 220$ league apps, $\ge 4$ league titles, $\ge 100$ league goals, $\ge 65$ assists, $\ge 60$ CS, or $\ge 4$ TOTS/POTY honors).
  - Continental Tournament Hall of Fame: Conferred for European cup glory ($\ge 2$ continental trophies, Tournament MVP + $\ge 1$ cup, or Continental Golden Boot + $\ge 1$ cup).
  - International National Team Hall of Fame: Inducted for international excellence ($\ge 100$ caps Centurion, $\ge 50$ caps Legend, $\ge 30$ international goals, World Cup/Continental trophy winner, or National Team Captain).
  - World Immortal Status: Conferred for all-time global greatness ($\ge 2$ World Golden Balls, God-Level peak $\ge 93$ OVR with $\ge 4$ major trophies & $\ge 3$ World Dream XIs).
- **Multi-Tier Silverware & Positional Awards Architecture:**
  - Per-League Accolades (All 10 Leagues): Player of the Season (MVP), Golden Boot (Top Striker), Midfielder of the Season (Playmaker), Defender of the Season, Golden Glove (Best GK), and Young Player of the Season (U21).
  - Official League Team of the Season (TOTS): 11-player Best XI (1 GK, 4 DEF, 3 MID, 3 FWD) generated for each domestic league.
  - Continental Tournament Honors: Continental Player of the Tournament, Continental Golden Boot, and Positional Best awards across continental cups.
  - Global Silverware Gala: World Golden Ball (World Player of the Year), World Golden Glove (World Best GK), World Golden Boot (World Striker of the Year), World Golden Boy (World Best U21), World Defender & Midfielder of the Year, and the World Dream XI.
- **8-Stop Season Flow with Dynamic Navigation:** Paced turn-based progression with stage-specific dynamic action buttons:
  1. *League Season* (Tables, fixtures, roll of champions, world top scorers across 10 leagues).
  2. *Tournament Qualified* (32-team continental bracket and qualified clubs).
  3. *Tournament Results & International Summer Championship* (5 knockout rounds: R32 $\to$ R16 $\to$ QF $\to$ SF $\to$ Final, Continental Roll of Honor, and Summer World Cup/Continental Cup tournament results).
  4. *Awards Ceremony* (World Golden Ball, World Golden Glove, World Golden Boot, World Golden Boy, World Dream XI, Continental Bests, Domestic Positional Trophies & League TOTS XIs across 10 leagues).
  5. *Season Summary & Career Report* (Deltas, milestones, rival gaps, living world news).
  6. *Offseason Decisions & Lifestyle* (Transfer bids, contract packages, brand endorsements, luxury properties, cryo-lab, family milestones).
  7. *Transfer Window Results* (Active contract confirmation, global roster movements, stabilized squads).
  8. *New Season Launchpad* (Detailed development review, G+A breakdown, $prev \to new$ rating progression, and domestic kick-off).
- **Career Depth & Storylines:**
  - Career Reports: Season-by-season rating/market-value progression, rank, team performance, and personal milestones.
  - Career Timeline: Interactive historical log of clubs, trophies, awards, injuries, and milestones.
  - Contextual Player Benchmarking: Dynamic relationship classification comparing the user against position peers (World Benchmark early in career; Division Peer; and Direct Rival when reaching $\ge 78$ OVR).
  - Living World Storylines: Procedural narratives on declining dynasties, rising wonderkids, rebuilding squads, and broken records.

### Track B — DevOps, Cloud Infrastructure & Progressive Delivery
- **Part 1 EKS World Factory:** Runs 100 independent 100-season world-generation workers in the Mumbai region (`ap-south-1`). The workload is suitable for experiments involving worker CPU/memory load, parallelism, node scaling, pod recovery, observability, and service load balancing.
- **Part 2 Career Runtime:** Loads one validated world template and advances the player's eight-stop season workflow. It does not perform the 100-world bulk generation during gameplay.
- **Terraform Infrastructure as Code:** Provisions the EKS platform and supporting AWS resources with separate bootstrap state where required.
- **GitHub Actions CI/CD:** Uses repository-scoped AWS OIDC authentication without long-lived cloud credentials.
- **Automated Simulation Quality Gates:** Validates statistical drift in goals, title dynasties, player development, roster integrity, and deterministic seeded output.
- **Versioned World State:** Stores generated templates and career snapshots so a previous valid state can be restored without recomputing the entire world.
- **Zero Client-Side SDKs:** Pure Vanilla HTML5/CSS/JavaScript with ES Modules, zero npm bloat, and fast local execution.

---

## DynamoDB Table Schema

All application metadata, world states, and cached screens are persisted with clean indexing:

| Entity Type | Partition Key (`PK`) | Sort Key (`SK`) | Key Attributes |
|---|---|---|---|
| **World Template Catalog** | `template_id` | `seed` | `content_hash`, `generation_duration_sec`, `quality_gate_results`, `status`, `s3_uri`, `created_at` |
| **Active World Metadata** | `WORLD#<worldId>` | `METADATA` | `rule_version`, `schema_version`, `seed`, `current_season`, `current_stage`, `s3_key`, `updated_at` |
| **Save State** | `SAVE#<saveId>` | `SNAPSHOT` | `save_name`, `world_id`, `season_number`, `stage_number`, `s3_version_id`, `saved_at` |
| **Screen Document Cache** | `WORLD#<worldId>` | `STAGE#<stageNum>` | `stage_key`, `screen_payload_json`, `generated_at` |

---

## API Surface (RESTful JSON)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/world/new` | Initializes a new user career by cloning a verified 100-season pre-simulated world template |
| `GET` | `/api/world/state` | Returns active world state and current stage metadata |
| `GET` | `/api/game/current-screen` | Reads precomputed document for the current season stop (1–8) |
| `POST` | `/api/game/next-step` | Advances simulation to next stop or triggers season runner |
| `POST` | `/api/game/choice` | Submits user decision (contract renewal, transfer choice, injury choice) |
| `POST` | `/api/game/lifestyle-action` | Executes lifestyle actions (sponsorship, real estate, cryo-lab, family) |
| `GET` | `/api/world/international/tournament` | Returns current active international tournament bracket and historical winners |
| `GET` | `/api/player/national-team` | Returns user player's national team squad, caps, goals, and captaincy status |
| `GET` | `/api/game/timeline` | Returns player career history, milestones, and comparisons |
| `GET` | `/api/game/comparisons` | Returns positional benchmarks, division peers, and direct rivals |
| `POST` | `/api/saves/manual` | Creates a manual save snapshot pointing to current S3 version |
| `GET` | `/api/saves` | Lists available save points for the user |
| `POST` | `/api/saves/{saveId}/load` | Loads world state from a specific save snapshot |
| `GET` | `/api/saves/export` | Exports full world state document as downloadable JSON |
| `POST` | `/api/saves/import` | Validates and imports an external world JSON document wrapped as `{"world_payload": {...}}` |

---

## Running Locally

The project is built to run 100% locally with zero cloud dependencies using Python and a standard web browser:

### 1. Prerequisites & Environment Setup
```bash
# Clone or navigate to the project directory
cd football-life-simulation

# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Local Backend Server
```bash
# Start the FastAPI server with local storage mode
python -m uvicorn src.api.main:app --reload --port 8000
```
- API Swagger Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/healthz`

### 3. Open the Frontend
Serve the static frontend via Python:
```bash
cd frontend
python -m http.server 3000
```
Visit **`http://localhost:3000`** in your browser to start playing.

---

## Two-Part Execution Model

### Part 1 — Generate 100 Worlds on EKS

One worker generates one world using one explicit seed and runs the existing 100-season burn-in. The Kubernetes implementation should run these workers as an indexed batch workload with a stable mapping such as `world-index -> seed`. Each worker must write its result, quality-gate report, duration, and resource metadata to shared versioned storage.

The EKS experiments are centred on this workload:

- Parallel worker execution and queue depth.
- CPU and memory pressure on Kubernetes workers.
- Pod restart and failed-worker recovery.
- Node and workload autoscaling.
- Prometheus/Grafana workload and node metrics.
- An HTTP coordinator or status service behind a Kubernetes load balancer where load-balancer behaviour is being measured.

The EKS batch must not silently generate only one world when the requested count is 100. A run is complete only when all 100 world results have either passed validation or have a recorded failure.

### Part 2 — Run and Play One World

The career game consumes one validated world template. The local development check intentionally runs only one generation:

```bash
python scripts/run_100_season_burnin.py --seed 42 --output-dir data/templates
```

That local run validates engine behaviour and output shape. It is not intended to reproduce the EKS workload or generate the complete 100-world pool on the laptop.

## Cloud Deployment & CI/CD Pipeline (Track B)

```text
[GitHub] ──► [GitHub Actions] ──► [Terraform] ──► [AWS EKS]
 (Source)      • Tests            • Infrastructure   • 100-world generation,
               • Quality gates    • OIDC auth       analysis, and observability
```

1. **Bootstrap Terraform Remote State Backend:**
   Provisions S3 remote state backend and DynamoDB lock table via GitHub Actions (or local one-time bootstrap). The GitHub Actions OIDC role is pre-configured.

2. **Trigger GitHub Actions Workflows (Manual Dispatch):**
   - **Persistent Data:** Run `data.yml` to provision immutable S3 template buckets, DynamoDB catalog, and ECR.
   - **Container Build:** Run `image.yml` to build worker container and push dual-tagged images (`sha-<commit>` and `latest`) to ECR.
   - **EKS Cluster:** Run `eks.yml` with `apply` to provision VPC, EKS cluster, node groups, and Pod Identity.
   - **EKS Teardown:** Run `eks.yml` with `destroy` (requires typed `DESTROY` confirmation) after experiments are complete.
   - **Playable Web App:** Run `webapp.yml` with `apply` to deploy the Lambda API and S3 frontend. The GitHub Actions run summary outputs the live clickable game link.
3. **Execute Portfolio Experiments:**
  - *Experiment 1 (100-World Workload):* Run 100 independent world-generation workers on EKS.
  - *Live Batch Status:* Inspect Coordinator NLB (`kubectl get svc -n worldgen worldgen-coordinator-lb`) and query `http://<nlb-url>/status`.
  - *Experiment 2 (Observability):* Inspect Prometheus & Grafana via temporary port-forwarding (`kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80`).
  - *Experiment 3 (Scaling and Teardown):* Measure workload scaling, export evidence, and remove unused resources.

---

## Project Structure

```text
football-life-simulation/
├── .github/
│   └── workflows/                 # Gated GitHub Actions workflows (bootstrap, data, image, eks, webapp)
├── terraform/                     # Multi-layer Terraform (bootstrap, data, eks, webapp)
├── worker/                        # Worker container Dockerfile & entrypoint
├── k8s/
│   └── worldgen/                  # Consolidated manifests (stage1.yaml, stage2.yaml, coordinator.yaml)
├── data/
│   └── templates/                 # Pre-simulated 100-season world template pool
├── frontend/                      # Zero-build Vanilla Web Interface
│   ├── css/                       # Modern responsive styles & card system
│   ├── js/                        # Modular ES6 client, API adapter & state handlers
│   └── index.html                 # Main application single-page interface
├── scripts/
│   └── run_100_season_burnin.py   # 100-season offline template generator & gate runner
├── src/
│   ├── api/                       # FastAPI routes, storage adapters & request schemas
│   ├── engine/                    # Pure Python deterministic simulation engine
│   │   ├── models/                # Dataclasses & Pydantic models (Player, Club, League)
│   │   ├── awards.py              # Domestic, continental & global silverware engine
│   │   ├── development.py         # Player progression, trait effects & aging curves
│   │   ├── injury_system.py       # Deterministic injury & recovery calculations
│   │   ├── integrity.py           # World integrity & statistical anomaly validators
│   │   ├── international_engine.py# 16-team national squads & 4-year summer cycle
│   │   ├── match_sim.py           # High-speed Poisson match simulator
│   │   ├── names_database.py      # 22-country male & female name pools + backstories
│   │   ├── season_workflow.py     # 8-stop season state machine & document generator
│   │   ├── storylines.py          # Living world news & emergent narrative generator
│   │   ├── transfer_market.py     # Offseason bidding, roles & compensation fees
│   │   └── youth_system.py        # Youth academy intakes & home-country rules
│   └── world_factory/             # World generation & burn-in template manager
├── DESIGN_DECISIONS.md            # Comprehensive Architecture Decision Records (ADR)
├── DEVELOPMENT_AND_DEPLOYMENT.md  # Detailed operational runbook & AWS deployment guide
├── requirements.txt               # Python package dependencies
└── README.md                      # Primary project documentation
```
