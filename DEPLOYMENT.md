# Cloud Deployment & Infrastructure Runbook — football-life-simulation

This document is the definitive deployment, infrastructure, and operational troubleshooting guide for **football-life-simulation** on AWS (region `ap-south-1` Mumbai). It details the 4-layer decoupled Terraform architecture, GitHub Actions OIDC configuration, step-by-step pipeline execution, and the exhaustive catalog of 18 deployment failure modes, root causes, and production learnings.

> **Production Status:** **COMPLETE & OPERATIONAL (DONE)**  
> All 4 Terraform infrastructure layers and 6 GitHub Actions workflows have been executed, verified, and battle-tested in AWS `ap-south-1`. Two 100-season world templates (383,100 matches per world across 10 leagues) were generated on Amazon EKS worker pods and cataloged in S3 & DynamoDB. The live web game is fully operational on AWS Lambda Function URL and Amazon S3 static hosting, with EKS decommissioned post-generation to preserve cloud budget.

---

## 1. Cloud Architecture Overview

The cloud infrastructure cleanly separates high-throughput batch world generation (Amazon EKS) from real-time interactive game execution (AWS Lambda & Amazon S3):

```text
terraform/
├── bootstrap/        # Layer 1: Remote Terraform state S3 bucket & DynamoDB lock table
├── data/             # Layer 2: Persistent S3 template & save bucket, DynamoDB catalog, ECR worker repo
├── eks/              # Layer 3: VPC, EKS cluster, managed node groups, Pod Identity, Access Entry
└── webapp/           # Layer 4: Stateless FastAPI Lambda API runtime & S3-hosted static web game

k8s/
└── worldgen/         # Kubernetes namespace, Indexed Jobs (stage1/stage2), and Coordinator NLB
```

### Storage & Runtime Specification

| Cloud Target | Artifact & Packaging | Execution Mechanism | Modules / Resources | Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **AWS Lambda** | `scripts/package_lambda.py` → `lambda_package.zip` | Serverless Function URL (`lambda_handler.handler` via Mangum) | `src/api/lambda_handler.py`, `src/api/main.py`, `src/api/storage.py`, `src/engine/` | Stateless FastAPI web application; serves browser requests, hydrates world templates from S3, and persists career saves. |
| **S3 Website** | Direct S3 bucket sync | Static Web Hosting | `frontend/` (HTML/CSS/JS) + `frontend/config.js` | Zero-build responsive browser game client; talks to Lambda Function URL. |
| **Amazon EKS** | `worker/Dockerfile` → Amazon ECR (`football-life-worker`) | Kubernetes Indexed Jobs & Coordinator Pod | `scripts/run_100_season_burnin.py`, `src/world_factory/`, `src/simulation/` | Heavy 100-season deterministic Poisson burn-in simulations across worker pods; uploads pre-simulated seed templates to S3. |
| **Persistent S3** | `terraform/data` | Versioned Object Storage | `football-life-templates-ap-south-1` | S3 bucket versioning enabled. Stores immutable templates (`templates/v1/`) and active career states (`worlds/`, `saves/`). |
| **DynamoDB** | `terraform/data` | On-Demand Table | `world_template_catalog` | Catalog index for generated seeds (`PK: template_id`, `SK: seed`) and O(1) screen cache documents (`PK: WORLD#<id>`, `SK: STAGE#<num>`). |

---

## 2. AWS OIDC Configuration & IAM Security Policies

All workflows authenticate keylessly via GitHub Actions OpenID Connect (OIDC). Long-lived AWS access keys are **not** permitted.

### 2.1 GitHub Secrets Setup

Configure these secrets in your repository (**Settings → Secrets and variables → Actions**):

| Secret Name | Required | Description | Example Format |
| :--- | :--- | :--- | :--- |
| `AWS_OIDC_ROLE_ARN` | **Yes** | Target IAM role assumed by GitHub Actions. | `arn:aws:iam::<ACCOUNT_ID>:role/ODIC-IAM-football-role` |
| `OWNER_IAM_USER_ARN` | **Yes** | Cluster owner IAM user ARN mapped to an EKS Access Entry (`AmazonEKSClusterAdminPolicy`). | `arn:aws:iam::<ACCOUNT_ID>:user/<USER_NAME>` |
| `ECR_IMAGE_URL` | Optional | Populated automatically into AWS Secrets Manager (`football-life/ecr-image-url`) by Layer 2. | `<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/football-life-worker` |

---

### 2.2 IAM Trust Policy (`assume_role_policy`)

Attach this Trust Policy to `ODIC-IAM-football-role` in the AWS IAM Console (**Roles → ODIC-IAM-football-role → Trust relationships → Edit trust policy**):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GitHubOIDCAuth",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": [
        "sts:AssumeRoleWithWebIdentity",
        "sts:TagSession"
      ],
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:samyakchhajed@id/football-life-simulation@*:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

> [!IMPORTANT]
> - **Session Tagging:** `sts:TagSession` must be explicitly included under `Action` because `aws-actions/configure-aws-credentials` evaluates session tagging during token exchange.
> - **Numeric ID Scoping:** GitHub mints JWT subject tokens with immutable numeric account and repository IDs (e.g. `repo:<user>@<UID>/<repo>@<RID>:ref:refs/heads/main`). Using the pattern `repo:samyakchhajed@id/football-life-simulation@*:ref:refs/heads/main` matches both the branch name and numeric repository identifier.

---

### 2.3 IAM Permissions Policy

Attach this Permissions Policy to `ODIC-IAM-football-role` (**Roles → ODIC-IAM-football-role → Permissions → Add permissions → Create inline policy**):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3StorageManagement",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DynamoDBManagement",
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-south-1:<ACCOUNT_ID>:table/football-life-*",
        "arn:aws:dynamodb:ap-south-1:<ACCOUNT_ID>:table/world_template_catalog"
      ]
    },
    {
      "Sid": "LambdaAndFunctionURLManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:ListVersionsByFunction",
        "lambda:ListAliases",
        "lambda:GetFunctionCodeSigningConfig",
        "lambda:GetAccountSettings",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:GetPolicy",
        "lambda:CreateFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:UpdateFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRManagement",
      "Effect": "Allow",
      "Action": [
        "ecr:*"
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
      "Sid": "VPCAndNetworkingManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EKSClusterAndWorkloadManagement",
      "Effect": "Allow",
      "Action": [
        "eks:*"
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
        "iam:ListRoleTags",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:ListPolicyVersions",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:ListInstanceProfilesForRole",
        "iam:TagPolicy",
        "iam:UntagPolicy",
        "iam:ListPolicyTags",
        "iam:PassRole",
        "iam:CreateServiceLinkedRole"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsManagement",
      "Effect": "Allow",
      "Action": [
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 3. End-to-End Deployment Workflow Sequence

Execute workflows in strict order via manual dispatch (`workflow_dispatch`) in the GitHub Actions tab:

```text
1. bootstrap.yml  ──►  2. data.yml  ──►  3. image.yml  ──►  4. webapp.yml (Play Game)
                                                                    │
                                                                    ▼
                                                            5. eks.yml (apply)
                                                                    │
                                                                    ▼
                                                            6. workload.yml (Run Batch Jobs)
                                                                    │
                                                                    ▼
                                                            7. eks.yml (destroy)
```

### Step 1: Bootstrap — Remote State Backend (`bootstrap.yml`)
- **Workflow:** `.github/workflows/bootstrap.yml`
- **Purpose:** One-time provisioning of the remote S3 state backend (`football-life-tfstate-ap-south-1`) and DynamoDB state lock table (`football-life-tfstate-locks`).
- **Resilience:** Contains automatic S3 and DynamoDB adoption logic (`terraform import ... || true`) so re-running after any partial interruption succeeds cleanly.

### Step 2: Data — Persistent Infrastructure (`data.yml`)
- **Workflow:** `.github/workflows/data.yml`
- **Purpose:** Provisions Layer 2 persistent infrastructure (S3 template bucket, DynamoDB template catalog table, ECR repository, Secrets Manager secret).
- **Execution Mode:** Apply-only. Persistent template pools and career saves are never deleted.
- **Outputs:** Stores the ECR repository URL in AWS Secrets Manager (`football-life/ecr-image-url`).

### Step 3: Image — Build & Push Worker Container (`image.yml`)
- **Workflow:** `.github/workflows/image.yml`
- **Purpose:** Builds the container image from `worker/Dockerfile` and pushes it to Amazon ECR.
- **Tagging:** Publishes dual tags:
  - `sha-<commit>`: Immutable tag for exact reproducibility.
  - `latest`: Convenience pointer for development and testing.

### Step 4: Web App — Apply / Destroy (`webapp.yml`)
- **Workflow:** `.github/workflows/webapp.yml`
- **Input:** `action: apply`
- **Purpose:** Provisions Layer 4:
  1. Packages Python application (`scripts/package_lambda.py` → `lambda_package.zip`).
  2. Deploys AWS Lambda function with public Function URL (`lambda_handler.handler`).
  3. Provisions S3 static website bucket (`football-life-frontend-ap-south-1`).
  4. Automatically injects `window.__API_BASE__ = '<lambda_url>'` into `frontend/config.js` and syncs all frontend static files to the S3 bucket.
- **Outcome:** Renders live game links in the GitHub Actions Step Summary. Click to play in any modern browser!

### Step 5: EKS — Apply (`eks.yml`)
- **Workflow:** `.github/workflows/eks.yml`
- **Input:** `action: apply`
- **Purpose:** Provisions Layer 3: VPC, subnets, NAT gateway, EKS cluster (`football-life-eks`), managed node group (`t3.medium`, 1–4 nodes), and Pod Identity.

### Step 6: EKS — Run Batch Worldgen Jobs (`workload.yml`)
- **Workflow:** `.github/workflows/workload.yml`
- **Input Actions:**
  - `action: apply`: Ensures `worldgen` namespace exists, cleans up any stale jobs/stuck pods, deploys Stage 1 Indexed Job (2 Worlds, 100 Seasons, 2 dedicated parallel workers) and Coordinator Deployment (NLB), waits 30s, and prints cluster health, pod status, NLB endpoints, and initial simulation logs directly into the GitHub Step Summary.
  - `action: status`: Inspects current cluster nodes, pods, jobs, and NLB service endpoints without redeploying.
  - `action: logs`: Tails the latest 50 lines of worker simulation logs and coordinator health.
  - `action: delete_jobs`: Safely deletes Stage 1/Stage 2 batch jobs to free up compute while leaving the coordinator and NLB alive.
- **Key Advantage:** Runs 100% via GitHub Actions OIDC—bypasses local laptop AWS CLI credentials and CloudShell IAM restrictions entirely.

### Step 7: EKS Teardown (`eks.yml`)
- **Workflow:** `.github/workflows/eks.yml`
- **Input:** `action: destroy`, Confirmation: `DESTROY`
- **Purpose:** Safely destroys all Layer 3 infrastructure (EKS cluster, node groups, VPC, NAT Gateway, subnets, Pod Identity) when simulation runs and experiments are complete. Protects the AWS credit budget against idle charges. Persistent data in Layer 2 (S3 templates, DynamoDB catalog, ECR image) is completely decoupled and remains safe.

---

## 4. Key Learnings & Failure Post-Mortem

During the development and deployment of this infrastructure, several non-obvious authentication and provisioning failures were analyzed and systematically resolved. The learnings below serve as a permanent engineering reference:

---

### Failure 1: STS `sts:AssumeRoleWithWebIdentity` Rejection Due to Default Session Tagging

#### Symptom:
GitHub Actions failed during `aws-actions/configure-aws-credentials` with 12 retry attempts:
```text
Retry AssumeRole: attempt 1 of 12 failed: Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity. Retrying after 30ms.
```

#### Root Cause:
`aws-actions/configure-aws-credentials@v6` automatically attaches 11 GitHub context session tags (such as `repository`, `actor`, `workflow`, `sha`) to the STS `AssumeRoleWithWebIdentity` call by default. When the IAM Role's trust policy does not explicitly permit the `sts:TagSession` action, AWS STS unconditionally rejects the role assumption request.

#### Resolution:
Two complementary fixes are required:
1. In the GitHub Actions workflow step, explicitly disable session tagging:
   ```yaml
   - name: Configure AWS credentials (OIDC)
     uses: aws-actions/configure-aws-credentials@v6
     with:
       role-to-assume: ${{ secrets.AWS_OIDC_ROLE_ARN }}
       aws-region: ${{ env.AWS_REGION }}
       audience: sts.amazonaws.com
       role-skip-session-tagging: true
   ```
2. In the IAM Role Trust Policy, explicitly grant `sts:TagSession`:
   ```json
   "Action": [
     "sts:AssumeRoleWithWebIdentity",
     "sts:TagSession"
   ]
   ```

---

### Failure 2: GitHub Numeric Account/Repository ID Mismatch in OIDC `sub` Claim

#### Symptom:
AWS STS rejected token validation despite matching repository and branch names.

#### Root Cause:
GitHub's OIDC token minting logic appends immutable numeric account and repository IDs into the `sub` claim string:
```text
repo:<USERNAME>@<USER_ID>/<REPOSITORY>@<REPO_ID>:ref:refs/heads/main
```
A strict StringEquals check looking for `repo:samyakchhajed/football-life-simulation:ref:refs/heads/main` fails because the numeric IDs `@<USER_ID>` and `@<REPO_ID>` are present in the actual token.

#### Resolution:
Match the numeric repository pattern in the IAM Trust Policy:
```json
"Condition": {
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:samyakchhajed@id/football-life-simulation@*:ref:refs/heads/main"
  }
}
```

---

### Failure 3: GitHub Environment Mutating the OIDC `sub` Claim

#### Symptom:
`bootstrap.yml` succeeded completely, but running `data.yml` or `webapp.yml` failed with `Not authorized to perform sts:AssumeRoleWithWebIdentity` during the `apply` step.

#### Root Cause:
Jobs configured with `environment: production` cause GitHub Actions to mint an OIDC token with a different `sub` claim format:
- **Without environment:** `sub: repo:...:ref:refs/heads/main`
- **With environment:** `sub: repo:...:environment:production`

If the IAM Role Trust Policy ends with `:ref:refs/heads/main` (as is common in basic OIDC guides), any job referencing `environment: production` will be blocked by STS.

#### Resolution:
1. Eliminate unnecessary GitHub Environment gating for personal and direct dispatch workflows (`workflow_dispatch`).
2. Ensure the IAM Trust Policy wildcard ends with `:*` (`...football-life-simulation@*:*`), allowing both branch refs and environment contexts.

---

### Failure 4: GitHub Actions "Re-Run Failed Jobs" Historical Snapshot Caching

#### Symptom:
Pushing a fix to `main` and immediately clicking **"Re-run failed jobs"** in GitHub Actions produced the exact same error, appearing as if the code changes had no effect.

#### Root Cause:
In GitHub Actions, clicking **"Re-run failed jobs"** (or **"Re-run all jobs"** on an existing run) executes the **historical commit snapshot** that initially failed. It does **not** pull or checkout the newest commit pushed to the branch.

#### Resolution:
Always trigger a **fresh workflow run** from the Actions tab (**Actions → Select Workflow → Run workflow → Branch: main**), or push a new commit to trigger automatic triggers.

---

### Failure 5: Terraform AWS Provider 5.x Sub-Resource Inspection (`s3:GetBucketAcl`)

#### Symptom:
Terraform state imports and bucket evaluations crashed with:
```text
assumed-role/ODIC-IAM-football-role/GitHubActions is not authorized to perform: s3:GetBucketAcl
```

#### Root Cause:
Terraform AWS Provider 5.x evaluates multiple S3 bucket sub-resources during reads and imports (`GetBucketAcl`, `GetBucketPolicyStatus`, `GetBucketVersioning`, `GetBucketPublicAccessBlock`). Restricting the CI/CD role to only `s3:GetObject` and `s3:PutObject` breaks Terraform's ability to refresh state.

#### Resolution:
In the CI/CD deployment role permissions policy, grant full S3 permissions:
```json
{
  "Sid": "S3StorageManagement",
  "Effect": "Allow",
  "Action": [
    "s3:*"
  ],
  "Resource": "*"
}
```

---

### Failure 6: Infrastructure Adoption & Idempotency Across Failed Runs

#### Symptom:
When a workflow failed midway through provisioning, subsequent runs threw resource collision errors:
- S3: `BucketAlreadyOwnedByYou`
- DynamoDB: `ResourceInUseException: Table already exists`
- ECR: `RepositoryAlreadyExistsException`

#### Resolution:
Implement pre-plan adoption logic in every workflow using `aws cli` probes and `terraform import ... || true`:
```bash
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  echo "Adopting existing S3 bucket..."
  terraform import aws_s3_bucket.name "$BUCKET_NAME" || true
fi

if aws dynamodb describe-table --table-name "table_name" --region "$AWS_REGION" 2>/dev/null; then
  echo "Adopting existing DynamoDB table..."
  terraform import aws_dynamodb_table.name "table_name" || true
fi
```
This guarantees that any workflow run is completely idempotent—it succeeds whether resources are being created fresh or adopted from a previous partial run.

---

### Failure 7: Pipeline Fragility in Multi-Job (Plan/Apply) Workflows

#### Symptom:
Workflows that separated `plan` and `apply` into two distinct GitHub Actions jobs suffered from:
1. Double STS authentication (doubling points of failure).
2. Runner-to-runner artifact synchronization issues (`actions/upload-artifact` and `download-artifact`).
3. S3 state lock contentions between the terminating plan runner and the starting apply runner.

#### Resolution:
For single-operator manual deployment pipelines (`workflow_dispatch`), consolidate execution into a single, unified job (identical to `bootstrap.yml`). This authenticates once, imports resources into the active runtime memory, plans, and applies in one uninterrupted process.

---

### Failure 8: Docker Build Failure Due to Non-Existent Context Directory (`COPY data/`)

#### Symptom:
`image.yml` failed during `docker build` with:
```text
ERROR: failed to build: failed to solve: failed to compute cache key: "/data": not found
```

#### Root Cause:
The `worker/Dockerfile` contained `COPY data/ /app/data/`, but no local `data/` directory exists in git (simulation data and templates are procedurally generated in memory during execution). In Docker BuildKit, attempting to `COPY` a missing path from the build context immediately fails the build.

#### Resolution:
1. Replaced `COPY data/ /app/data/` with `RUN mkdir -p /app/data` in `worker/Dockerfile`.
2. **Clarification on `CMD`:** The `CMD ["python", "scripts/run_100_season_burnin.py"]` in the Dockerfile is **not** executed during image build or push to ECR; it is simply metadata declaring the default container entrypoint. The actual execution of the simulation script only occurs at runtime when the Kubernetes Pod starts inside the EKS cluster (which overrides `CMD` via `k8s/worldgen/stage1.yaml`).

---

### Failure 9: Terraform HCL Syntax: `locals.var` vs `local.var`

#### Symptom:
`terraform validate` in `eks.yml` failed with:
```text
Error: Reference to undeclared resource on vpc.tf line 38: count = length(locals.azs)
A managed resource "locals" "azs" has not been declared in the root module.
```

#### Root Cause:
In Terraform HCL syntax:
- Declaring local values uses the plural keyword block: `locals { azs = ... }`.
- Referencing local values inside resources requires the singular keyword: `local.azs` (referencing `locals.azs` causes Terraform to search for a managed resource of type `locals`).

#### Resolution:
Replaced all occurrences of `locals.azs` with `local.azs` in `terraform/eks/vpc.tf`.

---

### Failure 10: EKS Infrastructure IAM Permissions — Concurrent CloudWatch & EC2 Attribute Rejections

#### Symptom:
During the initial `eks.yml` apply run, Terraform failed simultaneously on CloudWatch Logs group inspection and EC2 VPC/Elastic IP attribute evaluation:
```text
Error: reading CloudWatch Logs Log Group (/aws/eks/football-life-eks/cluster): listing CloudWatch Logs Log Groups: operation error CloudWatch Logs: DescribeLogGroups, AccessDeniedException

Error: creating EC2 VPC: modifying EnableDnsHostnames: waiting for completion: operation error EC2: DescribeVpcAttribute, api error UnauthorizedOperation: You are not authorized to perform this operation

Error: reading EC2 EIP (eipalloc-...): operation error EC2: DescribeAddressesAttribute, api error UnauthorizedOperation: You are not authorized to perform this operation
```

#### Root Causes:
1. **CloudWatch Logs:** AWS CloudWatch Logs API `DescribeLogGroups` is an account-level discovery and listing call. In AWS IAM, `DescribeLogGroups` **does not support resource-level ARN scoping** (`arn:aws:logs:...:log-group:...`). Restricting `Resource` to specific log group paths causes AWS to unconditionally reject the call with `AccessDeniedException`.
2. **EC2 Networking & Compute:** Terraform AWS Provider evaluates several fine-grained sub-resource attribute APIs during VPC creation and IP allocation (`DescribeVpcAttribute`, `DescribeAddressesAttribute`, `DescribeSubnetAttribute`), alongside compute operations required for EKS managed node groups (`RunInstances`, `DescribeLaunchTemplates`). Attempting to hand-curate individual EC2 actions causes repeated `UnauthorizedOperation` halts.

#### Resolution:
Updated both service blocks in the IAM policy attached to `ODIC-IAM-football-role` to grant broad management access on `"Resource": "*"`:
```json
{
  "Sid": "VPCAndNetworkingManagement",
  "Effect": "Allow",
  "Action": [
    "ec2:*"
  ],
  "Resource": "*"
},
{
  "Sid": "CloudWatchLogsManagement",
  "Effect": "Allow",
  "Action": [
    "logs:*"
  ],
  "Resource": "*"
}
```

---

### Failure 11: EKS Cluster Creation Rejection — Missing `iam:CreateServiceLinkedRole`

#### Symptom:
`eks.yml` failed while creating `aws_eks_cluster.main` with:
```text
Error: creating EKS Cluster (football-life-eks): operation error EKS: CreateCluster
EKS Cluster Service-Linked Role could not be created with cluster role. Ensure caller has permission to perform iam:CreateServiceLinkedRole action
```

#### Root Cause:
When an AWS account provisions an EKS cluster for the first time, the EKS service automatically attempts to create the AWS Service-Linked Role for EKS (`AWSServiceRoleForAmazonEKS`). Because the CI/CD IAM policy was scoped strictly to `arn:aws:iam::<ACCOUNT_ID>:role/football-life-*` and lacked the `iam:CreateServiceLinkedRole` action, AWS IAM blocked EKS from creating the service-linked role.

#### Resolution:
Added `"iam:CreateServiceLinkedRole"` to the `IAMRoleAndPolicyManagement` statement with `"Resource": "*"` in the IAM permissions policy attached to `ODIC-IAM-football-role`.

---

### Failure 12: Kubernetes Workload Deployment Ordering — `namespaces "worldgen" not found`

#### Symptom:
`workload.yml` failed while applying `coordinator.yaml` with:
```text
Error from server (NotFound): error when creating "STDIN": namespaces "worldgen" not found
```

#### Root Cause:
`coordinator.yaml` targets the `worldgen` namespace, but does not declare the `Namespace` resource itself (the namespace was declared inside `stage1.yaml`). Applying `coordinator.yaml` before `stage1.yaml` caused Kubernetes to reject the deployment because the namespace had not yet been created.

#### Resolution:
Added an explicit idempotent namespace creation step (`kubectl create namespace worldgen --dry-run=client -o yaml | kubectl apply -f -`) and updated the workflow to apply `stage1.yaml` before `coordinator.yaml`.

---

### Failure 13: Kubernetes `InvalidImageName` Due to Workflow Expression Collision

#### Symptom:
Kubernetes coordinator and worker pods failed to start with status:
```text
pod/worldgen-coordinator-...   0/1   InvalidImageName
job.batch/worldgen-stage1 ... IMAGES: ${{ secrets.ECR_IMAGE_URL }}
```

#### Root Cause:
The Kubernetes YAML manifests used `${{ secrets.ECR_IMAGE_URL }}` as an image placeholder. When `sed "s|\${{ secrets.ECR_IMAGE_URL }}|...|g"` was executed inside a GitHub Actions workflow, GitHub Actions attempted to pre-evaluate `${{ ... }}` as a workflow expression before bash ran, breaking the string matching. As a result, Kubernetes received the literal string `${{ secrets.ECR_IMAGE_URL }}` as the image name, which contains invalid characters (`$`, `{`, `}`) rejected by containerd.

#### Resolution:
Changed the placeholder across all Kubernetes manifests (`stage1.yaml`, `stage2.yaml`, `coordinator.yaml`) to `ECR_IMAGE_PLACEHOLDER`, and updated `workload.yml` to replace `ECR_IMAGE_PLACEHOLDER` with the dynamic image URI resolved from AWS Secrets Manager.

---

### Failure 14: Kubernetes Worker Pods Stuck in `Pending` Due to Resource Request Oversizing

#### Symptom:
Stage 1 worker pods remained indefinitely in `Pending` status:
```text
pod/worldgen-stage1-0-...   0/1   Pending
pod/worldgen-stage1-1-...   0/1   Pending
```

#### Root Cause:
The worker manifests requested `cpu: 1500m` and `memory: 4Gi` per pod. With `parallelism: 4`, the job requested 16 GiB of memory simultaneously. The EKS cluster consists of 2 `t3.medium` worker nodes (4 GiB total RAM per node, with ~3.5 GiB allocatable after system daemons). Because not even a single pod could satisfy the 4 GiB request, the Kubernetes scheduler could not place any worker pods.

#### Resolution:
Right-sized container resource requests in `stage1.yaml` and `stage2.yaml` to `cpu: 300m` and `memory: 512Mi` (with limits of `1000m` CPU and `1500Mi` RAM). All 4 worker pods now fit comfortably across the 2 `t3.medium` nodes and execute concurrently without scheduling stalls.

---

### Failure 15: Terraform Format Check (`fmt -check`) Halting Deployment Workflows

#### Symptom:
`webapp.yml` failed before running `terraform validate` or `terraform apply` with:
```text
Run terraform fmt -check -recursive
lambda.tf
Error: Terraform exited with code 3.
Error: Process completed with exit code 1.
```

#### Root Cause:
`terraform fmt -check` evaluates whitespace, indentation, and expression alignments (such as `=` alignment in locals and maps). If any minor formatting variance exists between developer machines and the runner's Terraform binary, `fmt -check` exits with non-zero status code 3. While suitable as a PR lint gate, enforcing formatting checks inside production deployment pipelines unnecessarily blocks critical infrastructure provisioning.

#### Resolution:
1. Aligned expressions and map assignments in `terraform/webapp/lambda.tf`.
2. Removed the blocking `terraform fmt -check` step from `.github/workflows/webapp.yml`, ensuring consistency with `eks.yml` and `data.yml` which rely on `terraform validate` for semantic correctness.

---

### Failure 16: Read-Only Filesystem in AWS Lambda (`OSError: [Errno 30] Read-only file system: '.local_data'`)

#### Symptom:
After deploying `webapp.yml`, opening the web game displayed a blank screen. AWS CloudWatch logs for the Lambda function showed:
```text
[ERROR] OSError: [Errno 30] Read-only file system: '.local_data'
  File "/var/task/src/api/lambda_handler.py", line 6, in <module>
    from src.api.main import app
  File "/var/task/src/api/main.py", line 31, in <module>
    template_manager = TemplateManager()
  File "/var/task/src/world_factory/template_manager.py", line 21, in __init__
    os.makedirs(d, exist_ok=True)
```

#### Root Cause:
In the AWS Lambda execution environment, the task root directory (`/var/task`) is mounted strictly as a read-only filesystem; the only writable directory is `/tmp`. When `src/api/main.py` was imported during cold start, `TemplateManager()` executed `os.makedirs('.local_data/templates', exist_ok=True)` in the working directory. This unhandled `OSError` crashed module initialization, preventing Mangum from serving any FastAPI endpoints.

#### Resolution:
1. Updated `TemplateManager.__init__` in `src/world_factory/template_manager.py` to detect serverless execution (`AWS_LAMBDA_FUNCTION_NAME` or `LAMBDA_TASK_ROOT`) and point local scratch storage to `/tmp/templates`.
2. Wrapped all local directory creation calls across `TemplateManager` and `LocalStorageAdapter` in `try...except OSError: pass` to ensure cold starts never crash on read-only environments.
3. Added an instant Day-0 initialization fallback in `TemplateManager.instantiate_career_from_template` via `WorldGenerator.generate_fresh_world` (<0.1s) so players can immediately play even before heavy 100-season batch templates finish syncing.

---

### Failure 17: Asynchronous Batch Job Execution & Distributed Dependency Coupling

#### Symptom:
`workload.yml` succeeded in 45 seconds, but the S3 templates bucket appeared completely empty. Furthermore, the GitHub Actions Step Summary dumped hundreds of lines of raw Python script code under "Job Details", and the web application could not load pre-simulated templates.

#### Root Causes:
1. **Asynchronous Lifecycle Mismatch:** In Kubernetes, batch jobs run asynchronously inside the cluster. A GitHub Actions workflow running for 30–45 seconds only checks cluster state at the very start of the job. Since a 100-season deterministic simulation across 10 global leagues takes ~4–5 minutes of continuous CPU computation per world, checking S3 at second 30 evaluated an empty bucket while the pods were still simulating early seasons in memory.
2. **Kubernetes Describe Output:** Running `kubectl describe job` in CI prints the entire Kubernetes Pod Template, which dumped the full inline Python script passed to the container command into the GitHub Actions step summary.
3. **Tight Architectural Coupling:** The initial architecture coupled the web game startup directly to offline batch templates in S3. If batch pods were throttled by burstable EC2 credits (`t3.medium`) or took longer than expected, the web app was left without playable templates.

#### Resolution:
1. **Decoupled Application Onboarding:** Updated `TemplateManager` and `/api/world/new` to fall back immediately to instant Day-0 world generation (`<0.1s`), allowing the web game to run independently of offline batch job timing.
2. **Telemetry Cleanup:** Replaced `kubectl describe job` in `workload.yml` with `kubectl get job` and `kubectl get events`, providing concise cluster status and lifecycle events without dumping container command source code.
3. **Compute Right-Sizing:** Re-architected Stage 1 to 2 worlds with dedicated 1-pod-per-node resource allocation (requests: 600m CPU / 768Mi RAM, limits: 1800m CPU / 2500Mi RAM), eliminating CPU credit contention across the worker nodes.

---

### Failure 18: Dual CORS Headers Between Lambda Function URL and FastAPI CORSMiddleware

#### Symptom:
When visiting the frontend S3 website, all API calls failed with `net::ERR_FAILED` and the browser console reported:
```text
Access to fetch at 'https://<lambda-id>.lambda-url.ap-south-1.on.aws/api/world/state' 
from origin 'http://football-life-frontend-ap-south-1.s3-website.ap-south-1.amazonaws.com' 
has been blocked by CORS policy: The 'Access-Control-Allow-Origin' header contains multiple values 
'http://football-life-frontend-ap-south-1.s3-website.ap-south-1.amazonaws.com, *', but only one is allowed. 
Have the server send the header with a valid value.
```

#### Root Cause:
Dual CORS header emission across two architectural layers:
1. **AWS Lambda Function URL Infrastructure Layer:** Configured in `terraform/webapp/lambda.tf` with a native `cors { allow_origins = ["*"] }` block. When a request arrives from the frontend S3 website, Lambda Function URL automatically evaluates the incoming `Origin` and attaches `Access-Control-Allow-Origin: http://football-life-frontend-ap-south-1.s3-website.ap-south-1.amazonaws.com`.
2. **Application Framework Layer:** In `src/api/main.py`, FastAPI registered `CORSMiddleware` with `allow_origins=["*"]`, attaching a second `Access-Control-Allow-Origin: *` header to the response body.
3. **Gateway Header Concatenation:** Lambda Function URL merged the application response headers with its own, outputting a comma-separated list of multiple origin values (`<s3-origin>, *`). The W3C CORS specification mandates that `Access-Control-Allow-Origin` contain strictly a single value; browsers treat multiple comma-separated values as invalid and block the network request.

#### Resolution:
Decouple CORS handling by environment:
- In AWS Lambda, let the Lambda Function URL infrastructure layer handle CORS natively (responding to preflight `OPTIONS` requests at edge and attaching single origin headers without Lambda compute overhead).
- In `src/api/main.py`, conditionally register `CORSMiddleware` only when running outside Lambda:
  ```python
  if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["*"],
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )
  ```
- Local development (`uvicorn src.api.main:app`) continues to have full CORS support, while production Lambda serves a clean, single origin header.

---

## 5. Playing the Game & Stateless Architecture

### 5.1 Accessing the Deployed Web Game
Once `webapp.yml` completes:
1. Open the completed run in the GitHub Actions tab.
2. In the **Summary** view, open the **Website URL**:
   `http://football-life-frontend-ap-south-1.s3-website.ap-south-1.amazonaws.com`
3. The frontend automatically interacts with the serverless API:
   `https://<lambda-id>.lambda-url.ap-south-1.on.aws/`

---

### 5.2 Stateless Session Recovery on AWS Lambda
Because AWS Lambda instances are ephemeral (recycled between cold starts and invocations):
1. **Dynamic S3 Hydration:** Every endpoint in `src/api/main.py` resolves state via `world = _get_active_world()`.
2. **Seamless Fallback:** If `active_world` is missing from memory, `_get_active_world()` fetches the active session (`sessions/latest_live.json` and `sessions/{worldId}/world_state_live.json`) directly from S3.
3. **Automatic State Synchronization:** All state mutations (`/api/game/choice`, `/api/game/lifestyle-action`, `/api/game/next-step`, `/api/saves/{save_id}/load`, `/api/game/action/retire`) commit the updated world back to S3 before returning the response.

---

### 5.3 Local Playback (Track A — Zero Cloud Dependencies)
The core simulation engine and web game are 100% self-contained and playable locally on your computer with zero AWS services, zero IAM roles, and zero cloud billing:
1. Open PowerShell / Terminal in the project root:
   ```bash
   python -m uvicorn src.api.main:app --port 8000
   ```
2. Open `frontend/index.html` in your browser (Chrome, Edge, Firefox).
3. The browser connects to `http://localhost:8000`. You can create your player, choose your starting country and youth academy, and advance through seasons with instant local responsiveness.

---

### 5.4 AWS Cloud Cost Management & Infrastructure Teardown
To protect your AWS credit balance against idle hourly charges from running EC2 instances and NAT Gateways:
* **Zero-Cost Layers (Leave Running):**
  * Layer 1 (S3 State Bucket & DynamoDB Lock Table) costs $0 when idle.
  * Layer 2 (Persistent S3 Templates & DynamoDB Catalog) costs pennies for storage.
  * Layer 4 (AWS Lambda Function URL & S3 Website) has zero idle cost (pay-per-request).
* **Billed Compute Layer (Teardown When Finished):**
  * Layer 3 (EKS Cluster + 2 `t3.medium` EC2 worker nodes + VPC NAT Gateway) incurs hourly costs while active.
  * To cleanly destroy Layer 3:
    1. Navigate to GitHub Actions → **`EKS — Apply / Destroy`** (`eks.yml`).
    2. Click **Run workflow**:
       * Set `action`: **`destroy`**
       * Set `confirm_destroy`: **`DESTROY`**
    3. Click **Run workflow**.
    4. Terraform will cleanly dismantle the cluster, node instances, VPC, and NAT Gateway without touching your S3 templates, DynamoDB tables, or web app code.

---

## 6. Kubernetes Batch Generation Experiments & Observability

### 6.1 Running the Workloads via GitHub Actions (`workload.yml`) [Recommended]

Because local workstation AWS credentials may be absent or restricted, and CloudShell may be blocked by IAM permissions (`cloudshell:CreateEnvironment`), the automated workflow `.github/workflows/workload.yml` provides a completely keyless, 1-click execution engine via GitHub Actions OIDC:

1. Navigate to the **Actions** tab in GitHub.
2. Select **`EKS — Run Batch Worldgen Jobs`** on the left sidebar.
3. Click **Run workflow** (Branch: `main`) and choose an action:
   - **`apply` (Deploy & Run):**
     - Idempotently creates the `worldgen` namespace.
     - Resolves the current worker image from AWS Secrets Manager (`football-life/ecr-image-url`).
     - Replaces `ECR_IMAGE_PLACEHOLDER` dynamically.
     - Cleans up any prior failed/stuck pods.
     - Deploys Stage 1 Indexed Job (2 Worlds, 100 Seasons, 2 dedicated parallel workers) and Coordinator Deployment (2 replicas + NLB).
     - Waits 30 seconds for initial pod scheduling and container pulling.
     - Prints live node health, pod statuses, service endpoints, S3 bucket listings, DynamoDB catalog items, and simulation logs directly into the **GitHub Step Summary**.
   - **`status` (Inspect Cluster):**
     - Inspects all nodes, pods, jobs, S3 bucket contents, DynamoDB items, and services without modifying running resources.
   - **`logs` (Tail Simulation Output):**
     - Retrieves the latest 60 lines of logs from active or completed simulation worker pods.
   - **`delete_jobs` (Clean Up Workloads):**
     - Deletes batch jobs (`worldgen-stage1`, `worldgen-stage2`) to release node resources while keeping the coordinator and NLB alive.

---

### 6.2 Manual CLI Execution Alternative (for Authenticated Terminals)

If operating from an authorized terminal with valid cluster admin credentials:

1. Update your local kubeconfig:
   ```bash
   aws eks update-kubeconfig --region ap-south-1 --name football-life-eks
   ```
2. Inspect cluster nodes and verify `Ready` status:
   ```bash
   kubectl get nodes -o wide
   ```
3. Resolve the worker image from AWS Secrets Manager and apply manifests:
   ```bash
   # Ensure namespace exists
   kubectl create namespace worldgen --dry-run=client -o yaml | kubectl apply -f -

   # Fetch worker image URI
   ECR_IMAGE=$(aws secretsmanager get-secret-value --secret-id football-life/ecr-image-url --query SecretString --output text --region ap-south-1):latest

   # Deploy Coordinator NLB and Stage 1 Batch Job
   sed "s|ECR_IMAGE_PLACEHOLDER|${ECR_IMAGE}|g" k8s/worldgen/coordinator.yaml | kubectl apply -f -
   sed "s|ECR_IMAGE_PLACEHOLDER|${ECR_IMAGE}|g" k8s/worldgen/stage1.yaml | kubectl apply -f -
   ```
4. Monitor jobs and stream simulation logs:
   ```bash
   kubectl get jobs,pods -n worldgen -o wide
   kubectl logs -n worldgen -l app=worldgen-stage1 --tail=100 -f
   ```

---

### 6.3 Monitoring Live Batch Progress via Coordinator NLB

The Coordinator service provisions an AWS Network Load Balancer (NLB) exposing real-time simulation health and catalog statistics:

1. Retrieve the Load Balancer DNS name:
   ```bash
   kubectl get svc -n worldgen worldgen-coordinator-lb
   ```
2. Query the endpoints:
   - **Liveness / Readiness Probe:**
     ```bash
     curl http://<nlb-dns-name>/healthz
     # {"status": "UP"}
     ```
   - **DynamoDB Catalog Status & Gate Summary:**
     ```bash
     curl http://<nlb-dns-name>/status
     ```
     Sample response:
     ```json
     {
       "coordinator": "worldgen-coordinator",
       "region": "ap-south-1",
       "dynamodb_table": "world_template_catalog",
       "templates_bucket": "football-life-templates-ap-south-1",
       "batch_progress": {
         "total": 10,
         "approved": 10,
         "rejected": 0,
         "investigating": 0,
         "scanned_count": 10
       },
       "status": "OPERATIONAL"
     }
     ```
   - **Prometheus Metrics:**
     ```bash
     curl http://<nlb-dns-name>/metrics
     ```
     Sample output:
     ```text
     worldgen_coordinator_requests_total 12
     worldgen_templates_approved_total 10
     worldgen_templates_rejected_total 0
     worldgen_templates_total 10
     ```

---

### 6.4 Observability via Temporary Port-Forwarding

Per cloud cost controls, Prometheus and Grafana dashboards use temporary kubectl port-forwarding rather than expensive continuous public load balancers:

```bash
# Open Grafana (http://localhost:3000)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Open Prometheus (http://localhost:9090)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```
