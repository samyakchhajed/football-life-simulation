# Development & Deployment Guide — The Football Life Engine

This document provides a comprehensive technical guide for building, running locally, deploying to AWS, and validating **The Football Life Engine**. It details the phased engineering roadmap, Track A simulation mechanics, Track B cloud infrastructure, and operational DevOps drills.

---

## 1. Project Evolution & Engineering Roadmap

The project is structured across six sequential phases to guarantee clean domain boundaries, instant local playability, and progressive cloud delivery:

```text
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Local Simulation Core (Track A)                   │
│  • Pure Python Poisson engine & seeded determinism          │
│  • Player development curves, traits, injuries & awards     │
│  • Hard integrity checker & statistical validation suite    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 2: Zero-Build Web UI & Local Playability (Track A)   │
│  • Vanilla HTML5, modern CSS custom properties & ES Modules │
│  • 8-stop season flow, career reports, timeline & lifestyle │
│  • Local FastAPI backend with JSON file storage adapter     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 3: World Factory & 100-Season Template Pool (Track A) │
│  • 10 global leagues, 200 clubs & 4,000 players             │
│  • 100-season burn-in runner & template manager pool        │
│  • Automated validation gate & invariant verification       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 4: EKS Infrastructure with Terraform (Track B)       │
│  • Terraform resources targeting Mumbai (ap-south-1)        │
│  • EKS cluster, node capacity, storage, and observability   │
│  • Kubernetes workloads for continuous world analysis      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 5: CI/CD and Quality Gates (Track B)                 │
│  • GitHub Actions with repository-scoped AWS OIDC           │
│  • Simulation regression and determinism gates              │
│  • Terraform plan/apply with explicit teardown              │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Phase 6: Kubernetes Experiments & Evidence                 │
│  • Continuous workload execution and resource observation  │
│  • Prometheus/Grafana metrics through temporary port-forward│
│  • Export evidence, then destroy unused AWS resources       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Local Setup & Running Guide (Zero Cloud Dependency)

The application is fully functional on a local development workstation without requiring AWS credentials, cloud connections, or external database installations.

### 2.1 Directory Layout & Prerequisites
- Python 3.11+
- Modern Web Browser (Chrome, Firefox, Edge, Safari)

```text
football-life-simulation/
├── requirements.txt            # Python dependencies (FastAPI, Uvicorn, Pydantic)
├── data/
│   └── templates/              # Persistent 100-season pre-simulated world templates
├── scripts/
│   └── run_100_season_burnin.py # CLI 100-season burn-in & Quality Gates audit runner
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

### 2.2 Running the Backend Service
The local API utilizes a filesystem-backed storage adapter (`LOCAL_STORAGE=true`) that simulates S3 versioned saves and DynamoDB screen caches using local JSON files in `.local_data/`:

```bash
# Start local API with auto-reload
python -m uvicorn src.api.main:app --reload --port 8000
```
- API Swagger Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/healthz`

### 2.3 Running the Web Game Frontend
```bash
# Serve the static frontend
cd frontend
python -m http.server 3000
```
Open **`http://localhost:3000`** in your browser. The frontend automatically connects to `http://localhost:8000` for game API interactions.

---

## 3. Track A: Core Simulation Architecture

### 3.1 Match Simulation (Poisson Distribution & Playstyles)
Matches are simulated without minute-by-minute loops using a Poisson goal distribution:
1. **Team Strength Computation:**
   $$\text{Attack Strength} = \sum_{\text{starting FWD/MID}} \text{Player Attack Score} + \text{Home Advantage}$$
   $$\text{Defense Strength} = \sum_{\text{starting GK/DEF}} \text{Player Defense Score}$$
2. **Expected Goals ($\lambda$):**
   $$\lambda_{\text{home}} = f(\text{Attack}_{\text{home}}, \text{Defense}_{\text{away}})$$
   $$\lambda_{\text{away}} = f(\text{Attack}_{\text{away}}, \text{Defense}_{\text{home}})$$
3. **Goal & Assist Assignment:**
   - Scorer probability allocates ~72% of total team goals to forwards, using a non-linear power curve on attacking attributes (`(p.attacking / 70.0) ** 2.2`) modulated by playstyle traits (Clinical Finisher $+35\%$, Rapid Counter-Poacher $+25\%$, Big-Game Clutch DNA $+25\%$ in deciders). This ensures world-class starting forwards score 20–35 goals across a 38-game season, established forwards score 14–22 goals, and rotational forwards score 8–13 goals.
   - Assists are allocated (~58% MID, ~28% FWD, ~13% DEF) using playmaking power curves (`(p.playmaking / 70.0) ** 2.0`) amplified by playstyles (Midfield Maestro $+45\%$, Dead-Ball Specialist $+30\%$).
4. **Defensive Credits:**
   - Goalkeepers and defenders on the starting lineup receive clean sheet credits and goals-conceded tracking. Goalkeepers accumulate saves and save percentage derived from opponent shot volume, enhanced by Acrobatic Wall and Sweeper Keeper.

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
  - **Summer International Championship:** Concurrently simulates the international football cycle for 16 national teams based on the 4-year quadrennial rotation:
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

### 3.3 Domestic Home Country Youth Academy Rule & Transfer Gating
- **Academy Graduation:** Every created footballer strictly starts their career at age 17 graduating from a domestic youth academy within their selected home country.
- **Development Gating:** During their initial 2–3 development seasons ($\text{age} \le 19, \text{OVR} < 76$), transfer offers for both user and AI prospects are restricted to domestic clubs until players prove their quality ($\ge 76$ OVR or age 20+) to unlock international moves.

### 3.4 Performance-Driven Player Progression
Attribute growth is calculated strictly from on-pitch match contributions:
- **Forwards (FWD):** $\ge 26$ G+A $\to$ raw +5; $16-25 \to$ raw +3; $8-15 \to$ raw +1; $<8 \to 0$.
- **Midfielders (MID):** $\ge 20$ G+A (or $\ge 14$ with $\ge 30$ matches) $\to$ raw +5; $12-19 \to$ raw +3; $6-11 \to$ raw +1.
- **Defenders & Goalkeepers (DEF / GK):** $\ge 30$ matches & $\ge 13$ clean sheets $\to$ raw +5; $\ge 25$ matches & $\ge 8$ clean sheets $\to$ raw +3; $\ge 18$ matches & $\ge 4$ clean sheets $\to$ raw +1.
- **Rating Tier Resistance & Aging:** Diminishing returns above 78 OVR (max +1 at 85+ OVR). Graceful veteran aging (ages 33+) with 0 OVR decline for exceptional superstars (Elite Veteran Longevity) and cryo-lab mitigation.

### 3.5 Living World Storylines Engine
Procedurally generates narrative events from simulation data:
- **Dynasty Declines:** Identifies multi-year championship clubs falling outside the top 4.
- **Wonderkid Breakthroughs:** Highlights teenage players breaking into starting lineups with top-scorer or top-assister performances.
- **Rebuilding Turnarounds:** Highlights low-ranked clubs making major transfer acquisitions and surging up league tables.
- **All-Time Records:** Triggers headlines when career goal, assist, or trophy records are broken.

### 3.6 Integrity & Statistical Quality Gates (Gates 1–9)
Executed automatically during the 100-season offline burn-in runner (`scripts/run_100_season_burnin.py`):
```bash
python scripts/run_100_season_burnin.py --seed 77
```
- **Hard Invariants (Gates 1–4):** Squad size 18–22; minimum 2 GK, 6 DEF, 6 MID, 4 FWD; zero negative club balances; **single-club registration invariant** (every player belongs to at most one club's `player_ids`).
- **Statistical Quality Gates (Gates 5–9):**
  - **Gate 5 (Strength vs Results):** Spearman rank correlation ($\overline{\rho} \ge 0.50$) between pre-season squad strength and final league standings.
  - **Gate 6 (Club Stability):** Mean position change ($\le 3.5$ spots) and wild swings ($\ge 8$ spots $\le 10\%$).
  - **Gate 7 (No Out-of-Nowhere Champions):** Champions from outside top 6 pre-season ranked squads capped at $\le 5\%$.
  - **Gate 8 (Dynasty Cap Audit):** Longest consecutive title runs tracked and audited across all 10 leagues.
  - **Gate 9 (Player Stat Stability & Monotonicity):** Extreme G+A swings ($\ge 20$ delta with $\le 1$ OVR change) capped at $\le 8\%$, and strict rating bracket monotonicity ($\overline{\text{GA}}_{85+} > \overline{\text{GA}}_{78-84} > \overline{\text{GA}}_{70-77} > \overline{\text{GA}}_{<70}$).

---

## 4. Track B: Cloud Infrastructure & Delivery Pipeline

### 4.1 Terraform and EKS Architecture
The planned cloud infrastructure in `ap-south-1` is organized across 4 decoupled Terraform layers and EKS workloads:

```text
terraform/
├── bootstrap/        # Layer 1: Terraform state S3 bucket & DynamoDB lock table
├── data/             # Layer 2: Persistent S3 world bucket, DynamoDB catalog, ECR repo
├── eks/              # Layer 3: VPC, EKS cluster, node groups, access entry, Pod Identity
└── webapp/           # Layer 4: Lambda runtime & S3-hosted frontend website

k8s/
└── worldgen/         # Namespace, stage1.yaml, stage2.yaml, and coordinator.yaml
```

#### Storage Layer Details:
- **Amazon S3 Bucket Layout (Layer 2 — Persistent Data):**
  - `s3://<world-bucket>/templates/v1/world_<index>_seed_<seed>_<hash>.json` — Immutable pool of 100-season pre-simulated world templates. S3 bucket versioning is enabled with no expiration or lifecycle deletion rules (generated worlds are never deleted or overwritten).
  - `s3://<world-bucket>/worlds/<worldId>/world_state.json` — Versioned active career world documents.
  - `s3://<world-bucket>/saves/<saveId>.json` — Explicit manual save snapshots.
- **Frontend S3 Bucket (Layer 4 — Web App Stack):**
  - `s3://<frontend-bucket>/` — Static zero-build web client assets, owned and managed strictly by Layer 4 (destroyable independently from persistent Layer 2 data).
- **Amazon DynamoDB Template Catalog (`world_template_catalog`):**
  - `PK: template_id` (`String`, e.g. `tpl_s42_100y_prod`), `SK: seed` (`Number`, e.g. `42`) — Dedicated catalog index (`content_hash`, `generation_duration_sec`, `quality_gate_results`, `status`, `s3_uri`, `created_at`). No user accounts or login records.
  - `PK: WORLD#<worldId>`, `SK: STAGE#<stageNum>` — Precomputed O(1) screen cache documents (65–90 KB) for active play sessions.

#### Document Sizing & Latency Profile:
- **Full 100-Season World State (`world_state.json`):** $\sim 4.5 - 6.2\text{ MB}$ uncompressed ($\sim 850\text{ KB}$ gzipped). Contains 200 clubs, 4,000 players, championship rolls, all-time record holders, and retired club legends. Persisted in S3 with $<15\text{ ms}$ regional transfer latency.
- **Stage Screen Projection Document:** $\sim 65 - 90\text{ KB}$ cached in DynamoDB (well under the 400 KB limit), enabling $<30\text{ ms}$ O(1) browser render latency.

#### EKS Workloads:
1. **Indexed world generation:** Manifests `k8s/worldgen/stage1.yaml` (10 completions, seeds 1–10) and `k8s/worldgen/stage2.yaml` (90 completions, seeds 11–100) run with `completionMode: Indexed`, `backoffLimitPerIndex: 2`, and `maxFailedIndexes`. Worker `i` uses seed `base_seed + i`. S3 upload uses conditional writes and registers metadata into DynamoDB.
2. **Coordinator & Metrics:** `k8s/worldgen/coordinator.yaml` provides real-time DynamoDB batch status (`/status`) and Prometheus metrics (`/metrics`) exposed via an in-tree AWS Network Load Balancer (NLB).
3. **Observability:** Exposes worker and node metrics through the project monitoring stack and temporary port-forwarding.
4. **Quota-Aware Compute Topology:** Account On-Demand Standard vCPU limit is 8 vCPUs (`L-1216C47A`). The managed node group scales between `min_size = 1`, `desired_size = 2`, and `max_size = 4` on `t3.medium` instances (4 nodes $\times$ 2 vCPUs = 8 vCPUs max) to prevent `VcpuLimitExceeded`. Batch Jobs execute with `parallelism: 4` to match available capacity.


### 4.2 GitHub Secrets Configuration & AWS OIDC Setup

All cloud workflows authenticate with AWS keylessly via OpenID Connect (OIDC). No long-lived AWS Access Keys are stored in the repository.

#### GitHub Secrets

| Secret Name | Required | Description | Value / Format |
|---|---|---|---|
| `AWS_OIDC_ROLE_ARN` | Yes | Target AWS IAM role assumed by GitHub Actions via OpenID Connect. | `arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>` |
| `OWNER_IAM_USER_ARN` | Yes | Cluster owner IAM user ARN mapped to an EKS Access Entry (`AmazonEKSClusterAdminPolicy`). | `arn:aws:iam::<ACCOUNT_ID>:user/<USER_NAME>` |

Deployment workflows targeting `production` require manual environment approval before executing `apply` or `destroy` operations.

---

#### AWS OIDC IAM Role Specification

The repository uses keyless OpenID Connect authentication to assume an IAM role with the following trust and permissions definitions:

- **Identity Provider:** `token.actions.githubusercontent.com` (Audience: `sts.amazonaws.com`)
- **Trust Policy (`assume_role_policy`):**
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
          },
          "StringLike": {
            "token.actions.githubusercontent.com:sub": "repo:<GITHUB_ID>/football-life-simulation@:ref:refs/heads/main"
          }
        }
      }
    ]
  }
  ```
- **Permissions Policy:** Scoped policy granting Terraform least-privilege access over the project's resources:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "S3BackendAndStorageManagement",
        "Effect": "Allow",
        "Action": [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:GetBucketPolicy",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy",
          "s3:GetBucketPublicAccessBlock",
          "s3:PutBucketPublicAccessBlock",
          "s3:GetEncryptionConfiguration",
          "s3:PutEncryptionConfiguration",
          "s3:GetBucketTagging",
          "s3:PutBucketTagging",
          "s3:GetBucketWebsite",
          "s3:PutBucketWebsite",
          "s3:DeleteBucketWebsite",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        "Resource": [
          "arn:aws:s3:::football-life-*",
          "arn:aws:s3:::football-life-*/*"
        ]
      },
      {
        "Sid": "DynamoDBTableManagement",
        "Effect": "Allow",
        "Action": [
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
          "dynamodb:DescribeTable",
          "dynamodb:DescribeContinuousBackups",
          "dynamodb:UpdateContinuousBackups",
          "dynamodb:DescribeTimeToLive",
          "dynamodb:UpdateTimeToLive",
          "dynamodb:TagResource",
          "dynamodb:UntagResource",
          "dynamodb:ListTagsOfResource",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ],
        "Resource": [
          "arn:aws:dynamodb:ap-south-1:<ACCOUNT_ID>:table/football-life-tfstate-locks",
          "arn:aws:dynamodb:ap-south-1:<ACCOUNT_ID>:table/world_template_catalog"
        ]
      },
      {
        "Sid": "ECRRepositoryManagement",
        "Effect": "Allow",
        "Action": [
          "ecr:GetAuthorizationToken",
          "ecr:CreateRepository",
          "ecr:DeleteRepository",
          "ecr:DescribeRepositories",
          "ecr:GetRepositoryPolicy",
          "ecr:SetRepositoryPolicy",
          "ecr:DeleteRepositoryPolicy",
          "ecr:PutLifecyclePolicy",
          "ecr:GetLifecyclePolicy",
          "ecr:DeleteLifecyclePolicy",
          "ecr:ListTagsForResource",
          "ecr:TagResource",
          "ecr:UntagResource",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ],
        "Resource": "*"
      },
      {
        "Sid": "SecretsManagerManagement",
        "Effect": "Allow",
        "Action": [
          "secretsmanager:CreateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:TagResource",
          "secretsmanager:UntagResource"
        ],
        "Resource": "arn:aws:secretsmanager:ap-south-1:<ACCOUNT_ID>:secret:football-life/*"
      },
      {
        "Sid": "NetworkingAndVPCManagement",
        "Effect": "Allow",
        "Action": [
          "ec2:CreateVpc",
          "ec2:DeleteVpc",
          "ec2:DescribeVpcs",
          "ec2:ModifyVpcAttribute",
          "ec2:CreateSubnet",
          "ec2:DeleteSubnet",
          "ec2:DescribeSubnets",
          "ec2:ModifySubnetAttribute",
          "ec2:CreateInternetGateway",
          "ec2:DeleteInternetGateway",
          "ec2:AttachInternetGateway",
          "ec2:DetachInternetGateway",
          "ec2:DescribeInternetGateways",
          "ec2:CreateRouteTable",
          "ec2:DeleteRouteTable",
          "ec2:DescribeRouteTables",
          "ec2:CreateRoute",
          "ec2:DeleteRoute",
          "ec2:AssociateRouteTable",
          "ec2:DisassociateRouteTable",
          "ec2:AllocateAddress",
          "ec2:ReleaseAddress",
          "ec2:DescribeAddresses",
          "ec2:CreateNatGateway",
          "ec2:DeleteNatGateway",
          "ec2:DescribeNatGateways",
          "ec2:DescribeAvailabilityZones",
          "ec2:CreateTags",
          "ec2:DeleteTags",
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeNetworkInterfaces",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress"
        ],
        "Resource": "*"
      },
      {
        "Sid": "EKSClusterAndWorkloadManagement",
        "Effect": "Allow",
        "Action": [
          "eks:CreateCluster",
          "eks:DeleteCluster",
          "eks:DescribeCluster",
          "eks:UpdateClusterConfig",
          "eks:UpdateClusterVersion",
          "eks:CreateNodegroup",
          "eks:DeleteNodegroup",
          "eks:DescribeNodegroup",
          "eks:UpdateNodegroupConfig",
          "eks:CreateAddon",
          "eks:DeleteAddon",
          "eks:DescribeAddon",
          "eks:UpdateAddon",
          "eks:CreateAccessEntry",
          "eks:DeleteAccessEntry",
          "eks:DescribeAccessEntry",
          "eks:AssociateAccessPolicy",
          "eks:DisassociateAccessPolicy",
          "eks:ListAssociatedAccessPolicies",
          "eks:CreatePodIdentityAssociation",
          "eks:DeletePodIdentityAssociation",
          "eks:DescribePodIdentityAssociation",
          "eks:TagResource",
          "eks:UntagResource",
          "eks:ListTagsForResource"
        ],
        "Resource": "*"
      },
      {
        "Sid": "IAMRoleAndPolicyManagement",
        "Effect": "Allow",
        "Action": [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:UpdateAssumeRolePolicy",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:ListRolePolicies",
          "iam:ListInstanceProfilesForRole",
          "iam:PassRole"
        ],
        "Resource": [
          "arn:aws:iam::<ACCOUNT_ID>:role/football-life-*",
          "arn:aws:iam::<ACCOUNT_ID>:policy/football-life-*"
        ]
      },
      {
        "Sid": "CloudWatchLogsManagement",
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:PutRetentionPolicy",
          "logs:DeleteRetentionPolicy",
          "logs:ListTagsForResource",
          "logs:TagResource",
          "logs:UntagResource"
        ],
        "Resource": "arn:aws:logs:ap-south-1:<ACCOUNT_ID>:log-group:/aws/eks/football-life-*:*"
      }
    ]
  }
  ```


---


#### Workflow Decoupling & Execution Sequence

All workflows execute on-demand via manual trigger (`workflow_dispatch`).

```text
1. bootstrap.yml  ──►  2. data.yml  ──►  3. image.yml  ──►  4. eks.yml (apply)
                                                                    │
                                                                    ▼
                                                            5. kubectl batch jobs
                                                                    │
                                                                    ▼
                                                            6. eks.yml (destroy)
```

1. **`bootstrap.yml`**: One-time setup of Layer 1 S3 remote state bucket (`football-life-tfstate-ap-south-1`) and DynamoDB lock table (`football-life-tfstate-locks`) with idempotent state import handling.
2. **`data.yml`**: Provisions Layer 2 persistent infrastructure (S3 template buckets, DynamoDB catalog, ECR). Apply-only with no destroy path to guarantee persistent world state is never deleted. Outputs ECR Image URL and stores it in AWS Secrets Manager (`football-life/ecr-image-url`).
3. **`image.yml`**: Builds the worker container from `worker/Dockerfile` and publishes it to ECR with dual tags: commit SHA (`sha-<commit>`) for exact reproducibility and `latest` for convenience.
4. **`eks.yml`**: Provisions or tears down Layer 3 EKS cluster, node groups, and Pod Identity. Passes `owner_iam_user_arn` via `secrets.OWNER_IAM_USER_ARN`. Teardown requires typing `DESTROY` to prevent accidental resource loss.
5. **`webapp.yml`**: Provisions or destroys Layer 4 web app runtime (Lambda + S3 frontend) with the same gated apply/destroy protection.



### 4.3 Simulation Statistical Regression Gate
During the GitHub Actions quality-gate stage:
1. The build spins up isolated test world simulations across previous and new rule versions.
2. It measures statistical distributions:
   - **Goals per Match:** Nominal target $\mu = 2.70$, operating target range $[2.50, 3.00]$, strict hard tolerance acceptance band $[2.30, 3.10]$ goals/match (build fails outside this band).
   - **Dynasty Longevity:** No more than 8 consecutive league titles per club.
   - **Rating Inflation Drift:** Average player rating within $\pm 1.5\%$ of baseline.
3. If statistical drift exceeds tolerances, the build fails and deployment is blocked.
4. **Evidence export:** Successful runs publish metrics, hashes, and generated template metadata before the EKS resources are removed.

### 4.4 Point-in-Time World Restoration (Versioned Storage)
Because world states are stored as immutable versioned S3 documents (`world_state.json`), restoring a corrupted or previous season state requires no database rollbacks:
```python
# Restore world state to previous season snapshot
s3_client.copy_object(
   Bucket=WORLD_BUCKET_NAME,
    CopySource={'Bucket': WORLD_BUCKET_NAME, 'Key': world_key, 'VersionId': target_version_id},
    Key=world_key
)
```

### 4.5 Accessing the Deployed Web App to Play the Game
When deploying Layer 4 via the `Web App — Apply / Destroy` (`webapp.yml`) GitHub Actions workflow with `action: apply`:

1. **GitHub Actions Step Summary (Primary):**
   - Navigate to the completed workflow run in the GitHub repository **Actions** tab.
   - The job summary automatically displays the live links:
     - **Website URL:** `http://football-life-frontend-ap-south-1.s3-website.ap-south-1.amazonaws.com` (Click to open directly in your browser to play)
     - **API Function URL:** `https://<unique-id>.lambda-url.ap-south-1.on.aws/`
2. **Terraform CLI Output (Alternative):**
   - Query the endpoints locally or via CLI:
     ```bash
     cd terraform/webapp
     terraform output website_endpoint
     terraform output api_endpoint_url
     ```
3. **Automated Frontend Wiring:**
   - The deployment workflow automatically captures `api_endpoint_url`, writes `window.__API_BASE__ = '<api_endpoint_url>';` into `frontend/config.js`, and syncs all frontend files to the S3 website bucket. When you open the Website URL in your browser, the frontend automatically routes all simulation calls to the Lambda Function URL.

### 4.6 Cloud Workload Distribution & Stateless Serverless Architecture

The cloud architecture cleanly segregates batch generation workloads from real-time interactive game execution:

| Cloud Target | Artifact & Packaging | Execution Mechanism | Scripts & Modules Deployed | Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Amazon EKS** | `worker/Dockerfile` → Amazon ECR (`${{ secrets.ECR_IMAGE_URL }}`) | Kubernetes Indexed Jobs & Coordinator Pod | `scripts/run_100_season_burnin.py`, `src/world_factory/`, `src/simulation/` | Heavy 100-season deterministic Poisson burn-in simulations across worker pods; uploads pre-simulated seed templates to S3. |
| **AWS Lambda** | `scripts/package_lambda.py` → `lambda_package.zip` | Serverless Function URL (`lambda_handler.handler` via Mangum) | `src/api/lambda_handler.py`, `src/api/main.py`, `src/api/storage.py`, `src/engine/`, `src/models/` | Stateless FastAPI web application; serves browser requests, reads world templates from S3, and persists career saves. |
| **S3 Website** | Direct S3 bucket sync | Static Web Hosting | `frontend/` (HTML/CSS/JS) + `frontend/config.js` | Zero-build responsive browser game client; talks to Lambda Function URL. |

#### Stateless Session Recovery on AWS Lambda:
1. **Dynamic S3 Hydration:** AWS Lambda instances spin up and shut down on demand (cold starts and recycled containers). To guarantee 100% session persistence without sticky sessions or expensive cache clusters, every endpoint in `src/api/main.py` resolves the active session via `world = _get_active_world()`.
2. **Seamless Fallback:** If `active_world` is not present in container memory, `_get_active_world()` calls `storage.get_active_world()` (`S3StorageAdapter`), fetching the user's active session state (`sessions/latest_live.json` and `sessions/{world_id}/world_state_live.json`) directly from S3.
3. **Automatic State Synchronization:** All mutating endpoints (`/api/game/choice`, `/api/game/lifestyle-action`, `/api/game/next-step`, `/api/saves/{save_id}/load`, `/api/game/action/retire`) call `storage.save_world(world)`, guaranteeing that state updates are persistently committed back to S3 for subsequent invocations.


---

## 5. Kubernetes Experiments and Evidence

### Experiment 1 — 100-World Indexed Workload
1. **Objective:** Run 100 independent world-generation workers and measure Kubernetes scheduling, parallelism, and resource pressure.
2. **Execution:**
   - Configure local credentials:
     ```bash
     aws eks update-kubeconfig --region ap-south-1 --name football-life-cluster
     ```
   - Resolve the ECR worker image URL from Secrets Manager and apply Stage 1 / Coordinator:
     ```bash
     ECR_IMAGE=$(aws secretsmanager get-secret-value --secret-id football-life/ecr-image-url --query SecretString --output text):latest

     # Deploy Coordinator Service & Stage 1 (Seeds 1–10)
     sed "s|\${{ secrets.ECR_IMAGE_URL }}|${ECR_IMAGE}|g" k8s/worldgen/coordinator.yaml | kubectl apply -f -
     sed "s|\${{ secrets.ECR_IMAGE_URL }}|${ECR_IMAGE}|g" k8s/worldgen/stage1.yaml | kubectl apply -f -
     ```
   - Observe pod status, CPU, memory, throughput, and failures during the run:
     ```bash
     kubectl get jobs,pods -n worldgen
     kubectl logs -n worldgen -l app=worldgen-stage1 --tail=100 -f
     ```
3. **Artifact:** Workload logs, generated metrics, and a reproducible run summary.


### Experiment 2 — Observability and Statistical Quality
1. **Objective:** Connect Kubernetes resource behavior to simulation quality and performance.
2. **Execution:**
   - Inspect Prometheus/Grafana through temporary `kubectl port-forward` access.
   - Compare throughput, resource usage, scoring averages, determinism, and integrity results.
   - Export metrics before cluster teardown.
3. **Artifact:** Metrics export and quality-gate report.

### Experiment 3 — Scaling, Recovery, and Teardown
1. **Objective:** Demonstrate controlled scaling and cost-aware cleanup.
2. **Execution:**
   - Change workload parallelism or resource requests through Terraform.
   - Observe scheduling, recovery after a failed pod, and completion behavior.
   - Destroy unused AWS resources after evidence is retained.
3. **Artifact:** Terraform plan/apply output, scaling observations, and teardown confirmation.

---

### 5.4 Operational Runbook: Batch Status & Observability Access

#### A. Checking Live Batch Progress via Coordinator NLB
While the EKS cluster is running, the long-running coordinator service (`k8s/worldgen/coordinator.yaml`) queries DynamoDB in real-time and serves status over an AWS Network Load Balancer (NLB):

1. **Retrieve the Load Balancer DNS Name:**
   ```bash
   kubectl get svc -n worldgen worldgen-coordinator-lb
   ```
2. **Inspect Live Status Endpoints:**
   * **Batch Progress (`/status`):**
     ```bash
     curl http://<nlb-dns-name>/status
     ```
     Returns JSON containing batch execution health:
     ```json
     {
       "coordinator": "worldgen-coordinator",
       "region": "ap-south-1",
       "dynamodb_table": "world_template_catalog",
       "templates_bucket": "football-life-templates-ap-south-1",
       "batch_progress": {
         "total": 100,
         "approved": 98,
         "rejected": 2,
         "investigating": 0,
         "scanned_count": 100
       },
       "status": "OPERATIONAL"
     }
     ```
   * **Prometheus Metrics (`/metrics`):**
     ```bash
     curl http://<nlb-dns-name>/metrics
     ```
     Exposes raw Prometheus counters (`coordinator_requests_total`, `worldgen_templates_registered_total`).
   * **Health Check (`/healthz`):**
     ```bash
     curl http://<nlb-dns-name>/healthz
     ```

#### B. Accessing Prometheus & Grafana Dashboards
Per project cost rules, Prometheus and Grafana use ephemeral storage and are accessed through port-forwarding rather than expensive public load balancers:

1. **Configure Local Kubeconfig:**
   ```bash
   aws eks update-kubeconfig --region ap-south-1 --name football-life-cluster
   ```
2. **Open Grafana Dashboard:**
   ```bash
   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
   ```
   * Open **`http://localhost:3000`** in your browser.
   * View dashboards for node CPU/memory saturation, pod scheduling throughput, and Karpenter autoscaling events.
3. **Open Prometheus Server (Optional):**
   ```bash
   kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
   ```
   * Open **`http://localhost:9090`** to run PromQL queries or inspect active targets.

