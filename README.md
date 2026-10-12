# football-life-simulation

A dual-track cloud engineering and data-driven football simulation platform. Features a pure Python deterministic simulation engine, a zero-build browser interface, multi-layer infrastructure-as-code with **Terraform**, keyless **GitHub Actions OIDC**, **Amazon EKS** batch workloads, and a serverless **AWS Lambda / Amazon S3** web application.

> 📖 **Documentation Links:**
> - 🚀 **[DEPLOYMENT.md](DEPLOYMENT.md)** — Production cloud runbook, 4-layer Terraform architecture, OIDC IAM policies, and engineering failure analysis.
> - 💻 **[DEVELOPMENT.md](DEVELOPMENT.md)** — Track A technical guide: local setup (zero cloud dependencies), Poisson match mechanics, and statistical quality gates.
> - 🏛️ **[DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)** — Architecture Decision Records (ADRs): trade-offs, rejected alternatives, and game mechanics design.

---

## 1. Architecture at a Glance

The platform strictly decouples high-throughput batch simulation (Amazon EKS) from interactive single-player gameplay (AWS Lambda & Amazon S3):

* **Track A — Interactive Career Game (Serverless Web App):**
  - **Frontend:** Zero-build single-page application (HTML5, modern CSS custom properties, native ES Modules) hosted on Amazon S3.
  - **API Runtime:** Stateless FastAPI service running on AWS Lambda Function URL via Mangum ASGI adapter, persisting player saves to S3.
  - **Fallback Mechanics:** Instant Day-0 world generator (<0.1s) ensures players can start careers immediately without waiting for offline batch runs.

* **Track B — World Factory Batch Processing (Amazon EKS):**
  - **Batch Compute:** Amazon EKS cluster (`v1.34`) executing Kubernetes Indexed Jobs (`completionMode: Indexed`) across managed `t3.medium` worker nodes.
  - **Workload Output:** Simulates 100 seasons (383,100 matches across 10 global leagues) in memory (~4 min/world), validates 12 statistical quality gates, and uploads approved templates to S3 and DynamoDB.
  - **Cost Discipline:** EKS compute and NAT Gateways are provisioned on-demand and safely destroyed post-run, keeping ongoing cloud costs at ~$0/month.

---

## 2. CI/CD Delivery Pipelines

Infrastructure and workloads are managed through 6 manual GitHub Actions workflows (`workflow_dispatch`), authenticated keylessly via AWS OIDC (no static access keys):

| Workflow | Layer | Purpose | Action |
| :--- | :--- | :--- | :--- |
| [bootstrap.yml](.github/workflows/bootstrap.yml) | Layer 1 | Remote S3 Terraform state bucket & DynamoDB lock table. | One-time Apply |
| [data.yml](.github/workflows/data.yml) | Layer 2 | Persistent S3 template bucket, DynamoDB catalog, ECR worker repo. | Apply-Only (Preserves Data) |
| [image.yml](.github/workflows/image.yml) | Container | Builds worker container and pushes to Amazon ECR (`latest` + `sha-*`). | On-Demand Build |
| [eks.yml](.github/workflows/eks.yml) | Layer 3 | VPC, subnets, NAT Gateway, EKS cluster (`v1.34`), and managed node group. | Apply / Destroy (Guard: `DESTROY`) |
| [webapp.yml](.github/workflows/webapp.yml) | Layer 4 | Deploys FastAPI Lambda Function URL and syncs frontend to S3 website bucket. | Apply / Destroy (Guard: `DESTROY`) |
| [workload.yml](.github/workflows/workload.yml) | Workload | Deploys Coordinator NLB and executes Stage 1 batch simulation jobs on EKS. | Apply / Status / Logs / Delete |

---

## 3. Key DevOps & Cloud Engineering Takeaways

Building and running this dual-track platform produced several valuable cloud engineering solutions (detailed in [DEPLOYMENT.md](DEPLOYMENT.md) and [MAJOR_ERRORS.md](MAJOR_ERRORS.md)):

* **Keyless OIDC Identity Federation:** Eliminated static credentials using `sts:AssumeRoleWithWebIdentity`, properly handling `sts:TagSession` and GitHub's numeric repository subject IDs (`repo:...@id/...@*:ref:...`).
* **Multi-Layer State Isolation:** Split Terraform into 4 decoupled state files (`bootstrap`, `data`, `eks`, `webapp`) so destroying experimental EKS compute never impacts persistent templates or career saves.
* **Worker Pod Resource Sizing:** Sized Kubernetes pod limits (`600m–1800m CPU`, `768Mi–2500Mi RAM`) to avoid system daemon memory starvation on `t3.medium` nodes and guarantee 1 dedicated pod per node.
* **Subnet Dependency Handling:** Implemented automated pre-destroy draining hooks in CI/CD to delete Kubernetes NLB services before `terraform destroy`, preventing VPC subnet `DependencyViolation` errors.
* **Serverless CORS Edge Delegation:** Delegated CORS handling natively to AWS Lambda Function URL in production to prevent duplicate origin header conflicts (`<origin>, *`) with FastAPI middleware.
* **Stateless Session Hydration:** Configured automatic re-hydration from S3 save objects, allowing stateless Lambda instances to scale down to zero without losing player state.

---

## 4. Local Quickstart (Zero Cloud Dependencies)

You can run the complete single-player career simulation locally on your laptop in 30 seconds:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start local FastAPI service
python -m uvicorn src.api.main:app --port 8000

# 3. Open the game client - Open frontend/index.html in any modern browser
```

---

## 5. Core Simulation Highlights

* **10 Global Leagues & 200 Clubs:** England, Spain, Italy, Germany, France, Brazil, Argentina, USA, Japan, and India.
* **Continental & International Silverware:** 32-team Continental Champions Trophy and quadrennial 16-nation summer tournament cycles.
* **Deterministic Poisson Engine:** Pure Python goal distribution model executing ~1,500 matches/sec with seeded reproducibility.
* **8-Stop Season State Machine:** Structured progression covering league fixtures, cup knockouts, awards galas (Golden Ball & TOTS Best XIs), lifestyle choices, and transfer windows.
* **12 Statistical Quality Gates:** Rigorous mathematical validation during template generation (Spearman rank correlation $\ge 0.50$, dynasty caps $\le 8$, scoring bands $[2.30, 3.10]$).

---

## 6. Project Structure

```text
football-life-simulation/
├── .github/workflows/             # 6 decoupled CI/CD pipelines (bootstrap, data, image, eks, webapp, workload)
├── terraform/
│   ├── bootstrap/                 # Layer 1: S3 state backend & DynamoDB locks
│   ├── data/                      # Layer 2: Persistent S3 template bucket, DynamoDB catalog, ECR repo
│   ├── eks/                       # Layer 3: VPC, EKS cluster (v1.34), managed node groups, Pod Identity
│   └── webapp/                    # Layer 4: FastAPI Lambda Function URL & S3 static website hosting
├── k8s/worldgen/                  # Kubernetes manifests (stage1.yaml, stage2.yaml, coordinator.yaml)
├── worker/                        # Dockerfile and entrypoint script for EKS worker container
├── frontend/                      # Zero-build vanilla web interface (HTML5, modern CSS, ES Modules)
├── screenshots/                   # 38 visual artifacts: AWS infrastructure, EKS metrics, CI/CD runs, and gameplay
├── scripts/
│   ├── run_100_season_burnin.py   # 100-season offline template generator & quality gates audit runner
│   └── package_lambda.py          # Serverless Lambda deployment packager
├── src/
│   ├── api/                       # FastAPI routes, storage adapters, serverless Mangum handler
│   ├── engine/                    # Pure Python simulation engine (match, progression, awards, storylines)
│   └── world_factory/             # World generator, template pool manager, and integrity validators
├── DESIGN_DECISIONS.md            # Comprehensive Architecture Decision Records (ADRs)
├── DEVELOPMENT.md                 # Track A local setup guide, Poisson mechanics, and quality gates
├── DEPLOYMENT.md                  # Track B cloud infrastructure runbook and failure analysis
├── MAJOR_ERRORS.md                # 8 most common CI/CD, Terraform, K8s, and Serverless errors & fixes
└── README.md                      # Primary project overview
```
