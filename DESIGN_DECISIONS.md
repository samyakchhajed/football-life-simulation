# Architectural Design Decisions — The Football Life Engine

This document records every significant architectural, simulation, data-plane, and cloud engineering decision made for **The Football Life Engine**. It details what was chosen, what was explicitly rejected, and the technical rationale behind each decision.

---

## 1. Game Design & Core Simulation Engine (Track A)

### Decision: Pure Python Poisson Simulation Engine with Seeded Randomness
- **Chosen:** A deterministic team-level Poisson goal-distribution model written in pure Python. Team attacking and defensive ratings are computed from healthy first-choice players plus a fixed home advantage factor. Goal and assist shares are allocated using compressed star weighting. All random generation uses explicit seed streams.
- **Rejected:** Minute-by-minute event simulation, physics-based match rendering, or LLM-based narrative generation during match runs.
- **Rationale:**
  - **Extreme Throughput:** A full 100-season world burn-in for 10 leagues and 32-team tournaments (3,831 matches/season $\times$ 100 seasons $= \mathbf{383,100\text{ matches}}$) executes in $\sim 3.5 - 4.5$ minutes in memory on a single CPU core without GPU overhead.
  - **Deterministic Reproducibility:** Every match and season outcome can be deterministically re-run and audited from the world seed, enabling reliable regression testing.
  - **Statistically Grounded:** Poisson distributions accurately reflect real-world football scoreline frequencies (~2.5–3.0 goals per match average).

### Decision: First-Choice Defensive Credit & Position-Normalized Scoring
- **Chosen:** A fixed club tactical formation (e.g. 1 GK, 4 DEF, 4 MID, 2 FWD) where healthy squad members are ranked by position scores. Only starting goalkeepers and defenders accumulate defensive credits (clean sheets, goals conceded, saves, save %). Award calculations normalize scores within positions.
- **Rejected:** Equal defensive credit for entire squads or unranked rotations.
- **Rationale:**
  - **Award Parity:** Prevents goal-scoring forwards from dominating all individual awards by establishing comparable, normalized performance metrics for defenders and goalkeepers.
  - **User Career Clarity:** The user's player is guaranteed first-choice status at their club, ensuring their defensive and offensive contributions directly shape team outcomes.

### Decision: Multi-Tier Silverware System, Per-League Positional Trophies & TOTS XIs
- **Chosen:** A tiered domestic, continental, and global awards ecosystem:
  - **Domestic League Awards (All 10 Leagues):** Player of the Season (MVP), Golden Boot (Forward of the Season), Midfielder of the Season (Playmaker), Defender of the Season, Golden Glove (Goalkeeper of the Season), and Young Player of the Season (U21).
  - **Official League Team of the Season (TOTS):** 11-player Best XI (1 GK, 4 DEF, 3 MID, 3 FWD) computed per league based on statistical impact scores.
  - **Continental Tournament Awards:** Continental Player of the Tournament, Continental Golden Boot, and Positional honors for continental competitions.
  - **Global Silverware Gala:** World Golden Ball (World Player of the Year), World Golden Glove (World Best GK), World Golden Boot (World Striker of the Year), World Golden Boy (World Best U21), World Defender & Midfielder of the Year, and the World Dream XI.
  - **Milestone & History Sync:** Automatically recorded in player milestones, trophy cabinets, season history records, and club Hall of Fame qualifications.
- **Rejected:** Flat awards that only recognize overall highest rated player or lump all leagues into a single global award without domestic recognition, or using copyrighted real-world trophy names.
- **Rationale:**
  - **Immersive Football Experience:** Delivers realistic football ceremonies and accolades while avoiding copyrighted real-world trademarks.
  - **Positional Representation:** Players playing at GK, DEF, or MID have direct positional silverware and Team of the Season accolades to fight for throughout their career.
  - **Long-term Career Satisfaction:** Gives user footballers a rich progression of milestones: earning their first League TOTS inclusion $\to$ winning League Positional Trophy $\to$ winning World Golden Ball $\to$ making the World Dream XI.

### Decision: 10 Global Domestic Leagues & 200 Clubs Ecosystem
- **Chosen:** Expanded the world from 5 European leagues to 10 premier global leagues across Europe, South America, North America, and Asia:
  1. Premier Division (England - 20 clubs)
  2. Liga Primera (Spain - 20 clubs)
  3. Serie Campionato (Italy - 20 clubs)
  4. Meister Liga (Germany - 20 clubs)
  5. Ligue Championnat (France - 20 clubs)
  6. Brasileirao Super Serie (Brazil - 20 clubs)
  7. Liga Argentina Primera (Argentina - 20 clubs)
  8. Major Soccer Championship (USA - 20 clubs)
  9. Japan Super League (Japan - 20 clubs)
  10. Indian Super Championship (India - 20 clubs)
- **Rationale:** Delivers true worldwide scope and allows footballers from Asia, the Americas, and Europe to start or transfer across the globe.

### Decision: 32-Team Continental Champions Trophy Tournament
- **Chosen:** Scaled the knockout tournament from 16 to 32 qualified clubs:
  - **Qualification Formula:** Top 3 teams from each of the 10 leagues ($3 \times 10 = 30$ teams) + Best 2 teams from the 4th-placed clubs across all 10 leagues (ranked by points, GD, GF) = exactly 32 clubs.
  - **5-Round Knockout Bracket:** Round of 32 (16 matches) $\to$ Round of 16 (8 matches) $\to$ Quarter-Finals (4 matches) $\to$ Semi-Finals (2 matches) $\to$ Final (1 match).
- **Rationale:** Perfectly harmonizes qualification with 10 leagues while maximizing competitive drama.

### Decision: Signature Playstyles & Tactical Traits Engine
- **Chosen:** A dynamic playstyle trait engine featuring 15+ position-specific and all-around tactical traits (Clinical Finisher, Rapid Counter-Poacher, Target Man & Hold-Up, Big-Game Clutch DNA, Midfield Maestro, Box-to-Box Engine, Dead-Ball Specialist, Defensive Anchor, Aerial Fortress, Acrobatic Wall, Sweeper Keeper) that mathematically modify Poisson match calculations (e.g. $+35\%$ goal conversion for Clinical Finisher, $+45\%$ assists for Midfield Maestro, $+25\%$ big-game clutch boost, $+1$ to $+2$ extra saves for Acrobatic Wall).
- **Rejected:** Passive decorative badges that have no effect on gameplay or match simulations.
- **Rationale:**
  - **Tactical Realism:** Gives players and stars distinctive identities where a target striker behaves differently from a rapid counter-poacher or deep playmaker.
  - **Interactive Progression:** Traits dynamically influence match results and appear prominently across player cards and profiles.

### Decision: Expanded Global Nationalities & Dynamic Country-Specific Name Generator
- **Chosen:** An authentic 22-nation geographic database (England, Spain, France, Germany, Italy, Portugal, Netherlands, Belgium, Norway, Sweden, Croatia, Denmark, Russia, Brazil, Argentina, Uruguay, Colombia, India, Australia, Japan, South Korea, USA). Selecting any country in the creation modal dynamically updates the footballer name input with authentic first and last names, accompanied by a dice randomization button.
- **Rejected:** Generic Western-only name lists or requiring players to type names manually without regional suggestions.
- **Rationale:**
  - **Cultural Realism:** Matches realistic football nationality distributions and creates authentic player identities from day one.
  - **Instant Frictionless Creation:** Users can either pick the auto-generated authentic name or type any custom name.

### Decision: Annual Single-Window Transfers with Compensation Fees
- **Chosen:** Transfers and contract renewals take place strictly once per year during the designated offseason window. Bidding clubs pay 100% of the player's market value as a compensation fee to the selling club's *subsequent year's* budget. Signing caps (maximum 5 signings per club per window) are enforced.
- **Rejected:** Mid-season transfer windows, multi-club chain trades in the same window, or tedious club-level wage-bill and tax accounting.
- **Rationale:**
  - **Clean Statistical Boundaries:** Annual windows ensure single-season statistical counters remain clean without split-season tracking across multiple clubs.
  - **Dynasty Prevention:** Paying compensation fees into next year's budget prevents rich clubs from instantly reinvesting transfer windfalls to dominate the same window.
  - **Focused Player Experience:** Eliminates tedious administrative club bookkeeping (club tax sheets, payroll reconciliation) while preserving player-facing roleplay wealth and lifestyle choices.

### Decision: Domestic Home Country Youth Academy Starting Rule & Development Gating
- **Chosen:** Every user player strictly starts their career at age 17 graduating from a domestic youth academy within their selected home country. During their initial 2–3 development seasons ($\text{age} \le 19, \text{OVR} < 76$), both user bids and AI prospect transfers are restricted to domestic clubs in their home nation until they prove their quality ($\ge 76$ OVR or age 20+) to unlock foreign/international transfers.
- **Rejected:** Randomly placing a young 17-year-old English/Brazilian academy prospect into foreign leagues on Day 0 or allowing unproven teenagers to jump immediately to foreign mega-clubs.
- **Rationale:**
  - **Authentic Career Realism:** Reflects real-world football pathways where young prospects establish themselves in their domestic league pyramid before earning high-profile international moves.
  - **Narrative Origin:** Creates a clear narrative arc: hometown academy graduate $\to$ domestic star $\to$ international superstar.

### Decision: International Football & Quadrennial Summer Championship Cycle
- **Chosen:** A full international football simulation engine featuring:
  - **16 Global National Teams:** England, Spain, Germany, Italy, France, Brazil, Argentina, USA, Japan, India, Netherlands, Portugal, Belgium, Croatia, Uruguay, Mexico.
  - **Dynamic 23-Man Squad Selection & Captaincy:** Evaluated annually from 75% overall rating and 25% normalized season form, with captains chosen by caps and veteran status.
  - **4-Year Summer Championship Cycle (Simulated in Stage 3):**
    - *Season % 4 == 1:* International Qualifiers & Summer Series
    - *Season % 4 == 2:* Continental Nations Cup (16-Team Knockout)
    - *Season % 4 == 3:* Nations League Finals (Final Four)
    - *Season % 4 == 0:* Global World Championship (World Cup)
  - **Performance Tracking:** Poisson match simulation, caps/goals/assists logging, Golden Boot awards, and International Hall of Fame inductions.
- **Rejected:** Continuous mid-season international breaks (which interrupt domestic league momentum) or purely decorative national team badges.
- **Rationale:**
  - **High-Impact Pacing:** Scheduling international tournaments during the summer window (Stage 3) ensures domestic league focus during Stages 1–2 while providing dramatic summer tournaments every season.
  - **Complete Football Career Legacy:** Allows players to pursue both club glory (League Titles & Continental Cups) and national glory (World Cup & Continental Cups).

### Decision: 12 Statistical & Integrity Quality Gates for World Verification (Gates 1–12)
- **Chosen:** Incorporated 12 comprehensive mathematical validation and structural integrity gates into the 100-season offline burn-in runner (`scripts/run_100_season_burnin.py`):
  - **Gates 1–4 (Structural Invariants):** Validates that all 200 clubs maintain valid squad sizes ($18 - 22$ players), strictly fulfill positional minimums (min 2 GK, 6 DEF, 6 MID, 4 FWD), maintain zero cross-club duplicate player registrations, and zero orphaned contracts.
  - **Gate 5 (Strength vs Results):** Spearman rank correlation ($\overline{\rho} \ge 0.50$, empirical range $\sim 0.54 - 0.57$) between pre-season squad strength and final league standings across all 10 leagues.
  - **Gate 6 (Club Stability):** Mean rank change ($\le 3.5$ spots) and share of extreme swings ($\ge 8$ spots $\le 10\%$, empirical range $\sim 4.0 - 5.5\%$).
  - **Gate 7 (No Out-of-Nowhere Champions):** Champions originating from outside the top 6 pre-season ranked squads capped at $\le 5\%$.
  - **Gate 8 (Dynasty Cap Audit):** Audits consecutive title streaks across all leagues and rejects any streak longer than 8 seasons.
  - **Gate 9 (Position-Separated Player Stat Stability & Monotonicity):** Year-over-year G+A swing bounds ($\le 8\%$) and position-separated rating bracket monotonicity:
    - *Attacker Monotonicity (FWD / MID):* $\overline{\text{GA}}_{85+} > \overline{\text{GA}}_{78-84} > \overline{\text{GA}}_{70-77} > \overline{\text{GA}}_{<70}$.
    - *Defender / Goalkeeper Monotonicity (DEF / GK):* $\overline{\text{CS}}_{85+} \ge \overline{\text{CS}}_{78-84} \ge \overline{\text{CS}}_{70-77} \ge \overline{\text{CS}}_{<70}$.
  - **Gate 10 (Schema Compatibility):** Validates full Pydantic model serialization and deserialization across all world entities for forward-compatible schema evolution.
  - **Gate 11 (Canonical State Determinism):** Verifies identical SHA-256 hashes before and after a Pydantic serialization round trip.
  - **Gate 12 (Goal Scoring Band Tolerance):** Total league match scoring strictly contained within $[2.30, 3.10]$ goals/match (operating target $[2.50, 3.00]$).
- **Rejected:** Relying solely on basic unit tests or subjective manual spot-checking.
- **Rationale:**
  - **Statistical Quality Assurance:** Guarantees that generated world templates are mathematically balanced, competitive, and realistic before any user launches a career.

### Decision: Pre-Simulated World Template Pool (100-Season Offline Burn-In)
- **Chosen:** New user careers are instantiated instantly from a pool of validated, pre-simulated world templates generated through a comprehensive **100-season offline burn-in** (via `WorldBurnInRunner` locally or on EKS). When a user joins at age 17, they graduate into a mature club academy within an equilibrium world with authentic emergent history, verified invariants, and equilibrium operating budgets (with zero multi-decade carry-over).
- **Sizing & Performance Reality:** A full 100-season template spanning 10 leagues, 200 clubs, and ~4,000 active/historical players produces an uncompressed JSON payload of **$\sim 35\text{ MB}$** (**$\sim 6\text{ MB}$ gzipped**). Local parse and deserialization into Pydantic models executes in **$\sim 200 - 450\text{ ms}$** in memory.
- **Rejected:** Day-0 unsimulated purely random worlds (which cause erratic table flips where 20-title giants finish bottom-table due to cold-start roll variance).
- **Rationale:**
  - **Authentic Emergent Equilibrium:** 100 seasons of Poisson matches, transfers, and academy promotions allow club budgets, squad depths, and reputation hierarchies to settle naturally into realistic competitive tiers.
  - **Instant User Onboarding:** Instantiating a career from an existing equilibrium template takes milliseconds, completely decoupling the deep 100-season simulation compute from the user's signup flow.
  - **Verified Quality & Integrity:** Every template in the pool passes automated integrity checks (`WorldIntegrityValidator`) before being published.
  - **Zero Real-World Trademark Collision:** All 200 clubs, 10 leagues, stadiums, brand sponsorships, and trophies are purely fictional and original.

---

## 2. Career Depth, Storylines & UX Principles

### Decision: Meaning-First Additions Over Action Overhead
- **Chosen:** Enriched the game with **Career Reports**, **Interactive Career Timelines**, **Positional Player Comparisons**, **Contextual Transfer Explanations**, **Living World Storylines**, and an **Offseason Lifestyle & Wealth Hub**, all derived automatically from simulation counters and salary progression.
- **Rejected:** Interactive training mini-games, press conference mini-games, or continuous energy/morale micromanagement chores.
- **Rationale:**
  - **High Narrative Depth, Low Friction:** Players experience a consequential, story-rich career through meaningful feedback, tangible off-pitch rewards (like the cryo-lab), and world visibility without tedious daily chores.
  - **Pure Data Derivation:** All narrative elements (rising wonderkids, fallen giants, rival gaps) are computed directly from stored historical snapshots without adding runtime complexity.

### Decision: Stage 6 Offseason Personal Life, Wealth, Family & Sponsorship System
- **Chosen:** An interactive Lifestyle & Wealth system in Stage 6:
  - **Commercial Sponsorships:** Tiered endorsements (Tier-1 Boot Deal, Swiss Watch Ambassador, Global Mega-Brand Face) unlocked by rating and silverware, paying annual earnings into player net worth.
  - **Real Estate & High-Tech Facilities:** Acquisition of Luxury Penthouses, Mediterranean Seaside Villas, Grassroots Youth Football Foundations, and a Private Cryo-Recovery & Biometrics Lab (which halves veteran age decline for ages 33+).
  - **Love Life & Meeting Backstories (5 Origin Archetypes):** Personal life includes 5 rich meeting backstories (Childhood Sweetheart, University & Studies Friend, Grassroots Charity Gala, Serendipitous City Encounter, Creative & Media Professional), paired with a culturally authentic female name database across all 22 supported countries (`COUNTRY_FEMALE_FIRST_NAMES`).
  - **Dynamic Milestone Narratives:** Meeting narratives, wedding ceremony descriptions, and childbirth milestone events dynamically incorporate the chosen meeting backstory archetype (e.g. hometown academy roots vs. charity gala wedding).
  - **Family & Life Journey:** Relationship progression (Single $\to$ In a Relationship $\to$ Married $\to$ Children), with life events recorded in career history and timeline.
  - **Contract Packages:** Bids explicitly display Annual Salary, Silverware Bonus, and Buyout Release Clauses.
- **Rejected:** Complex micro-transactions, tedious tax/agent accounting, or superficial prompts without narrative continuity.
- **Rationale:**
  - **Immersive Career Roleplay:** Simulates the authentic personal off-pitch life and status of a superstar footballer with cultural grounding and narrative continuity across decades, while providing tangible longevity benefits (Cryo-Lab).

### Decision: 8-Stop Fixed Season Screen Flow with Precomputed Documents
- **Chosen:** Each simulated season is broken down into exactly 8 distinct stops (League View, Tournament Qualification, Tournament Results, Awards Ceremony, Season Summary & Career Report, Offseason & Lifestyle Choices, Transfer Window Results, New Season Preview). At each stop, the engine writes a static, precomputed result document.
- **Rejected:** Real-time dynamic SQL/NoSQL query aggregation or infinite-scroll click-through pages.
- **Rationale:**
  - **Game Pacing:** Delivers a structured, dramatic progression (~200 deliberate stops over a full career).
  - **O(1) Screen Retrieval:** UI screens perform a simple single-document fetch from DynamoDB/S3 with zero joins, zero sorting, and instant page renders.

### Decision: Contextual Rivalry & Benchmark Classification
- **Chosen:** Dynamic categorization in the positional comparison modal. Established world superstars (85+ OVR) are labeled World Benchmark / World Class early in the user's career, representing aspirational targets. The Direct Rival status is activated only once the player enters the elite tier ($\ge 78$ OVR) and is closely matched within $\pm 5$ OVR, battling directly for domestic titles and the World Golden Ball.
- **Rejected:** Flatly labeling all top world players as "RIVAL" regardless of the user's current age or rating.
- **Rationale:**
  - **Narrative Authenticity:** A 17-year-old academy graduate (60 OVR) does not have a direct rivalry with a 94 OVR global superstar; framing them as benchmarks contextualizes developmental progression.
  - **Earned Rivalries:** Unlocking direct rivalry tags at elite ratings provides a satisfying emotional milestone when the user approaches world-class parity.

### Decision: Expected Playing Role Differentiation on Transfer Bids
- **Chosen:** Bidding clubs assign an explicit `expected_role` to each offer: Guaranteed Starter, Impact Sub / Rotation, or Squad Depth / Backup. Heavyweight contenders can bid on younger high-potential players for bench/sub depth.
- **Rejected:** Assuming all signed players are automatically first-choice starters across every club tier.
- **Rationale:**
  - **Strategic Player Agency:** Gives the user a meaningful career dilemma: remain a guaranteed starting pillar at a mid-table side, or join a prestigious powerhouse as an impact sub to contest continental trophies while developing.
  - **Realistic Transfer Market:** Reflects real-world football dynamics where top clubs sign promising talents as rotation options before promoting them to full starters.

### Decision: Strict Single-Club Invariant & Automated Roster Resolution
- **Chosen:** Strict enforcement of the single-club registration invariant: every active player belongs to at most one club's `player_ids` list. AI transfers automatically detach players from selling clubs and credit 100% compensation fees to selling club budgets. `_stabilize_all_club_squads` includes a pre-pass that resolves any cross-club duplicate registrations.
- **Rejected:** Permitting shared/dual registrations or deferring roster cleanup to save export time.
- **Rationale:**
  - **Simulation Stability:** Prevents corrupted duplicate match participation and conflicting statistic accumulation.
  - **Hard Integrity Invariant:** Ensures that validation checks pass cleanly across all 100 seasons without manual database intervention.

### Decision: 4-Tier Club Prestige Classification (Sporting Form, Era Silverware & Heritage Floors)
- **Chosen:** Classified all 200 clubs across the 10 leagues into 4 mutually exclusive Prestige Tiers calculated canonically by blending sporting form, recent era dominance, and institutional heritage floors:
  - **Tier 1 — Elite Domestic Heavyweights / Title Contenders (★★★★★):**
    - $\overline{R}_3 \le 4.0$ OR $\text{Era Silverware} \ge 2$ trophies (last 15 seasons) OR ($\text{Total Trophies} \ge 25 \text{ and } \overline{R}_3 \le 6.0$).
    - Commercial Baseline: **+€90M/yr** (Budget Floor: **€80M**).
  - **Tier 2 — Continental Trophy Challengers (★★★★):**
    - $\overline{R}_3 \in (4.0, 8.0]$ OR $\text{Era Silverware} \ge 1$ trophy (last 15 seasons) OR $\text{Total Trophies} \ge 15$ (Historic Titan Floor: multi-decade giants never fall below Tier 2).
    - Commercial Baseline: **+€55M/yr** (Budget Floor: **€45M**).
  - **Tier 3 — Mid-Table Established (★★★):**
    - $\overline{R}_3 \in (8.0, 14.0]$ OR $\text{Total Trophies} \ge 5$ (Historic Heritage Floor: decorated clubs never drop to Tier 4).
    - Commercial Baseline: **+€35M/yr** (Budget Floor: **€25M**).
  - **Tier 4 — Top-Flight Underdogs (★★):**
    - $\overline{R}_3 > 14.0$ with $< 5$ total lifetime trophies.
    - Commercial Baseline: **+€20M/yr** (Budget Floor: **€15M**).
- **Bootstrap Seasons (1–3):** During initial seasons before 3 full seasons exist, $\overline{R}_3$ is computed from the average of all available recorded seasons to date.
- **Era Silverware Definition:** Silverware won within the preceding 15 seasons counts toward dynamic upward mobility (1 point per Continental Champions Trophy or Domestic League Championship). Winning 1 trophy elevates a club to Tier 2, while $\ge 2$ trophies (or top-4 sustained rank) qualifies for Tier 1. Trophies older than 15 seasons naturally expire from era calculations.
- **Preventing Unbounded Ratchets via Multi-Decade Facility Depreciation & Budget Resets:** While historical heritage floors provide realistic baseline prestige for decorated clubs (mirroring real-world global football institutions that retain commercial gravity even during rebuilding cycles), permanent economic ratchets are prevented by:
  1. *Annual Operating Budgets with Zero Hoarding:* Transfer budgets reset each season to baseline + league/cup prize money, crediting transfer compensation on top of the annual baseline.
  2. *Multi-Decade Facility Depreciation:* Club training and youth academy facilities naturally age down 1 level every 15 seasons unless re-invested into, ensuring clubs must actively compete to sustain high youth generation.
- **Rejected:** Unbounded cumulative inflation without decay or budget-based tier gates (which made Tier 4 mathematically unreachable).
- **Rationale:**
  - **Dynamic Mobility with Institutional Realism:** Underdogs that surge into top 4 promote to Tier 1; legendary clubs retain authentic historical prestige floors without locking the entire pyramid into permanent inflation.
  - **Intuitive Scouting & Clean Separation:** Tiers accurately reflect sustained sporting performance, recent silverware, and historical prestige without rigid artificial quotas.

### Decision: Performance-Driven Player Progression & Rating Tier Resistance
- **Chosen:** Player growth is strictly earned through rigorous on-pitch metrics combined with **Rating Tier Resistance (Diminishing Returns)**:
  - **Positional Performance Output:**
    - *Forwards:* $\ge 26$ G+A $\to$ raw 5, $16-25 \to$ raw 3, $8-15 \to$ raw 1, $<8 \to 0$.
    - *Midfielders:* $\ge 20$ G+A (or $\ge 14$ G+A with $\ge 30$ apps) $\to$ raw 5, $12-19 \to$ raw 3, $6-11 \to$ raw 1.
    - *Defenders / GKs:* Requires defensive solidity, not just appearances: $\ge 30$ apps & $\ge 13$ clean sheets $\to$ raw 5, $\ge 25$ apps & $\ge 8$ clean sheets $\to$ raw 3, $\ge 18$ apps & $\ge 4$ clean sheets $\to$ raw 1.
  - **Rating Tier Resistance:**
    - *God-Level (92–100 OVR):* Hard bottleneck; max +1 only on extraordinary campaigns ($\ge 30$ G+A or $\ge 16$ CS).
    - *World-Class (85–91 OVR):* Max +1 growth per season.
    - *Elite (78–84 OVR):* Max +2 growth per season.
    - *Established (70–77 OVR):* Max +3 growth per season.
    - *Youth / Developing (< 70 OVR):* Up to +5 for explosive breakout seasons.
  - **Age Curve:** Wonderkid growth (17–23), prime refinement (24–27), peak plateau (28–30), physical decline (31–32), veteran decline (33+).
- **Rejected:** Flat linear growth (+5 jumps at 85+ OVR or granting defenders +5 merely for showing up to 30 games).
- **Rationale:**
  - **Challenging, Earned Stardom:** Prevents players from trivially skyrocketing to 95+ OVR in 5–6 seasons without generational superstar seasons.
  - **Realistic Developmental Pacing:** Matches real football development curves where top young talents break out quickly, but moving from very good (85) to world-class (90+) is a grueling multi-year effort.

### Decision: Authentic Positional Goal Distribution & Striker Weighting
- **Chosen:** Forward position goal share is calibrated to ~72% of total team goals, with an authentic power curve on attacking attributes (`(p.attacking / 70.0) ** 2.2`). Top starting forwards in a 38-game campaign realistically score 20–35 goals for world-class strikers, 14–22 for established starters, and 8–13 for young/backup forwards.
- **Rejected:** Flat linear rating influence or uniform goal distribution across 3-forward sets that artificially capped forwards at ~10 goals over 38 games.
- **Rationale:**
  - **Authentic Football Realism:** Mirrors real-world European and global top flight scoring tallies (e.g. Haaland, Kane, Salah, Lewandowski).
  - **Attribute Impact:** High attacking ratings visibly pay off in high goal totals and Golden Boot races.

### Decision: Coherent Backend-Driven Development Review Summary
- **Chosen:** The backend development engine computes both the exact rating delta and an authentic narrative summary (e.g. `Stellar Campaign (+5 OVR Jump)`, `Potential Ceiling Reached (+0 OVR)`, `Veteran Age Decline (-3 OVR)`, `Severe Injury Setback (-7 OVR)`). Stage 8 displays this unified backend assessment directly.
- **Rejected:** Calculating the review badge purely in frontend JavaScript using goal counts, which caused confusing mismatches (e.g. claiming a `+1 OVR Jump` during veteran age decline or potential caps).
- **Rationale:**
  - **Zero UI-Engine Divergence:** Ensures perfect coherence between the performance badge and the rating progression numbers (`79 -> 76 (-3)`).
  - **Age & Injury Context:** Correctly explains why ratings rise, plateau, or drop as players age through their 30s.

### Decision: Multi-Tier Hall of Fame with Tenure-Averaged Club Tier
- **Chosen:** A comprehensive 5-category Hall of Fame and Legend recognition architecture evaluated at player retirement:
  1. **Tier-Scaled Club Legend (Club Hall of Fame):** Evaluated against the **average tier across the player's tenure years at that club**, rounded to the nearest integer ($\le 1.50 \to \text{Tier 1}$, $1.51 - 2.50 \to \text{Tier 2}$, $2.51 - 3.50 \to \text{Tier 3}$, $> 3.50 \to \text{Tier 4}$), preventing both underdog inversion penalties and low-tier signing loopholes:
      - **Tier 1 Elite Domestic Heavyweights (★★★★★):** Centurion ($\ge 200$ apps, $\ge 6$ seasons), Silverware Dynasty ($\ge 4$ major trophies, $\ge 80$ apps), All-Time Giant Scorer ($\ge 120$ goals), Giant Playmaker ($\ge 70$ assists), Defensive Titan ($\ge 60$ clean sheets), or World Golden Ball winner ($\ge 60$ apps).
      - **Tier 2 Continental Challengers (★★★★):** Pillar ($\ge 150$ apps, $\ge 5$ seasons), Silverware Leader ($\ge 3$ trophies, $\ge 60$ apps), Goalscoring Icon ($\ge 85$ goals), Playmaker Icon ($\ge 55$ assists), Defensive Wall ($\ge 45$ clean sheets), or World Golden Ball winner ($\ge 40$ apps).
      - **Tier 3 Mid-Table Established (★★★):** Loyal Centurion ($\ge 120$ apps, $\ge 4$ seasons), Historic Silverware Leader ($\ge 2$ trophies, $\ge 40$ apps), Goal Hero ($\ge 60$ goals), Playmaker Hero ($\ge 40$ assists), Defensive Wall ($\ge 35$ clean sheets), or World Golden Ball winner.
      - **Tier 4 Top-Flight Underdogs (★★):** Savior Centurion ($\ge 100$ apps or $\ge 3$ seasons), Miracle Silverware Champion ($\ge 1$ historic trophy, $\ge 30$ apps), Cult Hero Striker ($\ge 40$ goals), Cult Hero Playmaker ($\ge 25$ assists), Cult Hero Defender ($\ge 20$ clean sheets).
  2. **Domestic League Legend (League Hall of Fame):** Inducted into domestic leagues based on: League Iron Man ($\ge 220$ league apps), Dynasty Titan ($\ge 4$ league titles), All-Time Centurion Scorer ($\ge 100$ league goals), Master Playmaker ($\ge 65$ assists), Defensive Titan ($\ge 60$ clean sheets), or $\ge 4$ League TOTS / Player of the Season accolades.
  3. **Continental Tournament Legend (Continental Cup Hall of Fame):** Inducted into continental tournament history based on: $\ge 2$ Continental Tournament Trophies ($\ge 4$ seasons), Continental Player of the Tournament MVP + $\ge 1$ cup, or Continental Golden Boot + $\ge 1$ cup.
  4. **International National Team Hall of Fame:** Conferred for national team distinction: International Centurion ($\ge 100$ caps), National Legend ($\ge 50$ caps), All-Time National Scorer ($\ge 30$ int'l goals), Major International Silverware winner ($\ge 1$ World Cup or Continental Nations Cup), or appointed National Team Captain.
  5. **World Immortal Legend (Global Football Hall of Fame):** Conferred for transcendent global impact: $\ge 2$ World Golden Ball titles, God-Level peak rating ($\ge 93$ OVR with $\ge 4$ major trophies and $\ge 3$ World Dream XIs), or $\ge 1$ World Golden Ball + $\ge 4$ trophies + $\ge 2$ World Dream XIs.
- **Rejected:** Evaluating against club tier at retirement (which penalized players who elevated underdog clubs to Tier 1) or evaluating solely at signing (which created loopholes for clubs in temporary one-season dips).

### Decision: Instant Career Restart & Clean State Reinitialization
- **Chosen:** Added a one-click Restart action in the header and the Saves Manager, allowing players to reset the world state and launch a new footballer career from age 17 at any time.
- **Rejected:** Requiring manual deletion of save files or server reboots to start a fresh playthrough.

### Decision: Graceful Veteran Aging & Exceptional Superstar Longevity (Ages 33+)
- **Chosen:** Replaced rapid random aging drops (`-1` to `-4` OVR per year) with a calibrated, graceful aging system:
  - **Ages 33–35:** Normal players experience slow, gradual decline of at most -1 OVR per year (or -0 OVR on strong seasons). Exceptional / Generational stars ($\ge 85$ OVR, World Golden Ball winners, or players with $\ge 15$ G+A / $\ge 8$ CS) experience **0 OVR decline** (Elite Veteran Longevity).
  - **Ages 36–41:** Normal players decline by -1 OVR (rarely -2 only on very quiet seasons at age 39+). Exceptional superstars drop at most 0 to 1 OVR (Legendary Longevity), preserving world-class quality like real-world longevity icons (Messi, Cristiano Ronaldo, Modric, Lewandowski).
- **Rejected:** Harsh, indiscriminate drops that made all 33+ players rapidly collapse to low 70s regardless of technical mastery or stellar match performances.

### Decision: Annual Operating Budget Distribution (No Carry-Over)
- **Chosen:** Club finances operate on a clean **Annual Operating Budget with Zero Carry-Over**:
  1. **Prize Distribution:**
     - **Domestic League:** 1st: €400M, 2–4th: €200M, 5–10th: €60M, 11–20th: €15M.
     - **Continental Champions Trophy:** Winner: €300M, Runner-up: €150M, Semi-Finals: €75M, Quarter-Finals: €40M, Round of 16: €30M, Round of 32: €20M.
     - Net payouts are subject to standard 15% infrastructure deduction.
  2. **Commercial Baseline & Operating Floor:** Every season, clubs receive a guaranteed commercial baseline based on canonical tier (Tier 1: +€90M, Tier 2: +€55M, Tier 3: +€35M, Tier 4: +€20M) with operating budget floors (Tier 1: €80M, Tier 2: €45M, Tier 3: €25M, Tier 4: €15M).
  3. **Zero Multi-Decade Hoarding:** Club transfer budgets reset annually to ensure balanced, dynamic transfer market cycles rather than infinite billionaire compounding.
- **Rejected:** Complex club payroll/tax accounting, club wage bills, or multi-decade budget compounding.

### Decision: 3-Season Form Trajectory & Performance Visibility
- **Chosen:** Track a rolling 3-to-5 season history of league finishes (`recent_ranks`) on every club and compute real-time trajectory badges:
  - Title Contender (Consistent top 1–3 finishes)
  - Sleeping Giant in Rebuild ($\ge 6$ historical league titles, currently in a rebuilding dip)
  - Rising Force (Multi-season upward surge, e.g. 12th -> 7th -> 3rd)
  - Continental Contender (Regular top 4–6 European/continental competitor)
  - Stable Mid-Table (Consistent mid-table security)
  - Battling Relegation (Struggling near the drop zone)
  - Visible on Transfer Bid offers (Stage 6), Club Modals, and the World Clubs Directory (Stage 7).
- **Rejected:** Relying on single static star ratings or single-season ranks that gave zero visibility into whether a prospective club was actually on the rise or in decline.
- **Rationale:**
  - **Informed Career Transfers:** Users can evaluate whether a club offering them a contract is an ascending contender or a rebuilding giant before putting pen to paper.

---

## 3. Frontend Architecture & Local Playability

### Decision: Zero-Build Vanilla Web Interface (HTML5 / Modern CSS / ES Modules)
- **Chosen:** Pure HTML5, modern CSS custom properties with responsive layouts and subtle micro-animations, and modular JavaScript (ES Modules).
- **Rejected:** React, Next.js, Vue, Webpack, Vite, or TailwindCSS.
- **Rationale:**
  - **Zero Dependency Overhead:** Runs instantly in any modern browser without `npm install`, Node.js runtimes, or compilation steps.
  - **Instant Local Playability:** The game can be executed immediately on a developer workstation using Python's built-in servers with zero configuration.
  - **Longevity & Portability:** Eliminates frontend dependency rot and security vulnerabilities in client-side packages.

### Decision: Card Design for Profiles
- **Chosen:** Card-based visual presentation for player and club profiles. Players feature tier gradients (Bronze, Silver, Gold, Elite, Best, God-Level), rating shields, position tags, and compact attribute grids (ATT, PLY, DEF, PHY). Clubs feature distinctive crest badges and primary/secondary color schemes.
- **Rejected:** Plain tabular-only text profiles or overly complex 3D player models.
- **Rationale:**
  - **High Visual Polish:** Delivers an engaging, recognizable sports gaming aesthetic that makes player progression and ratings instantly impactful.
  - **Zero Heavy Assets:** Built entirely with lightweight CSS gradients and standard font icons, requiring zero heavy bitmap downloads or 3D rendering libraries.

---

## 4. Cloud Infrastructure, Storage & Compute (Track B)

### Decision: DynamoDB Screen Cache Sizing & 400 KB Item Limit Safety
- **Chosen:** Stage screen projection documents cached in DynamoDB contain lightweight serialized player and club summary records rather than full world states. Full world states are persisted exclusively in S3 with Object Versioning.
- **Sizing Analysis:** Even the largest stage screen (Stage 4 Awards Gala across 10 leagues, 10 TOTS XIs, Continental Best XI, and World Dream XI containing ~200 player summary objects) produces an uncompressed JSON payload of **$\sim 65 - 90\text{ KB}$**, occupying only $\sim 20\%$ of DynamoDB's 400 KB item limit.
- **Rationale:** Guarantees O(1) single-read screen latency with zero DynamoDB item size overflow risk.

### Decision: AWS-managed EKS for the 100-World Factory
- **Chosen:** AWS-managed EKS runs an indexed Kubernetes Job with 100 completions. Each worker generates exactly one independent 100-season world using `base_seed + world_index`, validates it, and publishes its result metadata. Kubernetes jobs and supporting services provide the execution surface for observability and scaling experiments.
- **Rejected:** ECS/Fargate, Step Functions, and short-lived one-off batch tasks as the primary platform for the Kubernetes experiment.
- **Rationale:**
  - **Meaningful Kubernetes Workload:** One hundred independent burn-ins are long-running enough to justify cluster scheduling, workload metrics, worker pressure, and controlled scaling.
  - **Cloud Execution:** The laptop is not suitable for Kubernetes or heavy simulation workloads, so the cluster and observability stack run in AWS.
  - **Controlled Cost:** The cluster is created for bounded experiments, all 100 results are accounted for, evidence is exported, and unused resources are torn down.

### Decision: S3 Object Versioning for Point-in-Time World State Restores
- **Chosen:** The live world state is stored as a single JSON document (`world_state.json`) in an Amazon S3 bucket with Object Versioning enabled. Every simulated season creates a new immutable version.
- **Rejected:** Relational database row rollbacks or complex delta-patch event sourcing.
- **Rationale:**
  - **Instant, Reliable Recovery:** Restoring a player's world to a previous season or recovering from a bad release simply requires referencing a previous S3 Version ID.
  - **Zero Schema Migration Overhead:** Save files are immutable snapshots that cleanly enforce rule and schema version boundaries.

### Decision: Terraform and GitHub Actions for Infrastructure and Delivery
- **Chosen:** Terraform provisions AWS infrastructure across 4 isolated layers (`bootstrap`, `data`, `eks`, `webapp`), and GitHub Actions runs infrastructure operations and container image publishing through 4 decoupled manual workflows:
  - `data.yml`: Persistent data apply-only pipeline (fmt, validate, plan, approval-gated apply). No destroy path to guarantee persistent world templates are never wiped.
  - `image.yml`: Worker container build and publish to ECR with dual tagging (`sha-<commit>` for exact git traceability, `latest` for operational convenience).
  - `eks.yml`: EKS infrastructure apply/destroy with production environment approval gates and typed `DESTROY` confirmation.
  - `webapp.yml`: Web app runtime apply/destroy with identical approval and typed confirmation protection.
  - **Authentication:** Single shared IAM role (`secrets.AWS_OIDC_ROLE_ARN`) assumed via keyless GitHub Actions OIDC (`aws-actions/configure-aws-credentials@v6`) without long-lived credentials. All AWS ARNs (including `secrets.OWNER_IAM_USER_ARN`) are managed strictly as GitHub Secrets.
  - **Triggering:** Manual-only execution (`workflow_dispatch`); no unreviewed automated pushes.
- **Rejected:** Monolithic all-in-one deploy script, AWS CodeCommit/CodeBuild (quota constraints), AWS CDK as primary IaC, single-tag container deployments, and storing static AWS credentials in repository secrets.
- **Rationale:**
  - **State Separation & Fault Isolation:** Destroying experimental EKS clusters must never impact persistent S3 world templates or DynamoDB catalog state.
  - **Available Toolchain:** Terraform and GitHub Actions match existing portfolio workflows and provide transparent diff review via plan artifacts.
  - **Keyless Security:** OIDC avoids long-lived secret rotation overhead.
  - **Traceability:** Dual image tagging enables deterministic verification of the exact git commit used during any EKS batch generation run.
  - **Quota Compliance:** Node group scaling is capped at 4 instances (`t3.medium`, 8 vCPUs max) to strictly respect the account-level standard vCPU quota (`L-1216C47A`), preventing Auto Scaling `VcpuLimitExceeded` errors.


### Decision: Two-Tier Storage Architecture (Persistent Templates vs Local Session Cache)
- **Chosen:** A clean separation of data concerns into two specialized storage tiers:
  1. **Persistent Template Repository (`data/templates/`):** Houses the canonical 100-season burned-in world template files (`*.json`). In AWS deployment, this maps to the root immutable Amazon S3 bucket (`s3://.../templates/`). These templates allow instant Day-0 career cloning without re-computing 100 seasons on the fly.
  2. **Local Session Cache (`.local_data/`):** Houses transient local browser session states managed by `LocalStorageAdapter` (`.local_data/worlds/`, `.local_data/screens/`, `.local_data/saves/`). In AWS deployment, this maps to DynamoDB screen caches and user save points.
- **Rejected:** Mingling transient browser session snapshots directly inside the persistent template repository.
- **Rationale:**
  - **Storage Hygiene:** Prevents hundreds of transient session snapshots generated during interactive web play from cluttering canonical template definitions.
  - **Performance & Clear Lifecycle:** Makes it easy to clean up temporary browser caches without affecting pre-simulated world templates.

### Decision: DynamoDB Template Catalog Schema & Metadata Indexing
- **Chosen:** A dedicated DynamoDB table (`world_template_catalog`) storing metadata records for all generated 100-season world templates, decoupling template discovery from binary S3 state payload downloads:
  - **Partition Key (PK):** `template_id` (`String`, e.g. `tpl_s42_100y_prod`)
  - **Sort Key (SK):** `seed` (`Number`, e.g. `42`)
  - **Attributes:**
    - `content_hash` (`String` SHA-256 hex digest of raw S3 JSON payload)
    - `generation_duration_sec` (`Number` burn-in execution duration, typically $\sim 190 - 240\text{ s}$)
    - `quality_gate_results` (`Map` containing booleans and metrics for Gates 1–12)
    - `status` (`String`, enum: `APPROVED` | `REJECTED`)
    - `s3_uri` (`String`, e.g. `s3://football-sim-templates/world_template_seed42_100seasons.json`)
    - `created_at` (`String` ISO-8601 UTC timestamp)
- **Rationale:** Enables instant, indexed querying and filtering of approved equilibrium templates with verified cryptographic integrity hashes before loading state into user sessions.

### Decision: Automated Simulation Regression Gate in GitHub Actions
- **Chosen:** An automated regression test stage in GitHub Actions that validates statistical metrics on generated templates:
  - **Goal Distribution:** Nominal target $\mu_{\text{goals}} = 2.70$, operating target range $[2.50, 3.00]$, strict hard tolerance gate band $[2.30, 3.10]$ goals/match.
  - **Dynasty Longevity Audit:** Natural distribution of consecutive league titles (peak streaks 3–8 titles/century across 10 leagues without runaway dynasties).
  - **Rating Inflation Drift:** Average active player rating remains bounded within $\pm 1.5\%$ across 100 seasons.
- **Rejected:** Relying solely on standard unit tests, loose thresholds ($>3.5$), or manual playtesting.
- **Rationale:**
  - **Game Balance Protection:** Catches parameter drift, broken team hierarchies, and scoring anomalies automatically before deployment.

---

## 5. Explicitly Rejected Alternatives Summary

| Alternative | Reason Rejected | Selected Architecture |
|---|---|---|
| **Real-Time 3D / Match Simulation** | Unnecessary complexity; shifts focus away from cloud engineering and DevOps architecture. | **Deterministic Poisson Goal Engine** with seeded random generation. |
| **Shared Multi-User World** | High synchronization complexity and cross-user blast radius during rollbacks/resets. | **Per-User Isolated World Documents** instantiated from pre-simulated template pool. |
| **LLM-Driven Dynamic AI Decisions** | High inference costs, non-deterministic outcomes, and latency bottlenecks. | **Rule-Based Python Scoring Functions** with seeded noise. |
| **ECS/Fargate or short-lived batch services** | Do not provide the continuous Kubernetes workload needed for this project. | **AWS-managed EKS** for sustained generation and analysis. |
| **Database-Level Save Rollbacks** | Complex relational rollbacks, migration overhead, and high storage costs. | **S3 Object Versioning** on immutable single-world JSON states. |
| **Heavy Frontend Frameworks (React/Next)** | Node.js dependency bloat, compilation steps, and maintenance churn. | **Zero-Build Vanilla HTML5/CSS/JavaScript (ES Modules)**. |
| **Purely Procedural Faked History (Unsimulated)** | High variance, lack of statistical equilibrium, and cold-start anomalies (e.g. 20-title giants finishing last due to single unsimulated rolls). | **Pre-Simulated World Template Pool (100-Season Burn-In)** with S3 storage & DynamoDB metadata indexing. |
| **Mid-Season / Complex Transfers** | Creates messy split-season stats and tedious micro-management. | **Annual Single-Window Window** with 100% compensation fees to next year's budget. |
| **Club Payroll & Tax Bookkeeping** | High administrative friction without gameplay value. | **Player Career Roleplay Wealth & Lifestyle Hub** (annual wages, sponsorships & cryo-lab without bookkeeping chores). |

## 6. Current Combined Project Baseline

These decisions supersede earlier drafts and are the current source of truth:

- **Compute:** AWS-managed EKS is the single cloud environment for the indexed 100-world generation and analysis workload.
- **Infrastructure:** Terraform is the infrastructure-as-code tool, with separate bootstrap state where required.
- **Delivery:** GitHub Actions is the CI/CD system and uses repository-scoped AWS OIDC authentication.
- **Identity:** Login, Cognito, passwords, and user accounts are outside the project scope. Worlds are identified without authentication.
- **Kubernetes experiments:** Only project-supporting experiments remain, especially continuous workloads, observability, scaling, recovery, and cost-controlled teardown.
- **Region:** AWS Mumbai (`ap-south-1`) is used for project resources.
- **Execution order:** Local simulation and quality validation come first; cloud deployment follows after the local behavior is understood.
- **Local boundary:** The laptop runs one indexed worker only. It is not used to generate the complete 100-world batch.
