# Terraform — GitHub Repository (Lab 4 Bonus)

Manages the existing **DevOps-Core-Course** repository via Terraform (import existing repo, then manage settings in code).

## Prerequisites

- Terraform 1.9+
- GitHub Personal Access Token with `repo` scope (create under GitHub → Settings → Developer settings → Personal access tokens)

## Setup

1. **Set the token** (do not commit):
   - Option A: `export GITHUB_TOKEN="your-token"` and add `github_token = os.getenv("GITHUB_TOKEN")` or use a `terraform.tfvars` (gitignored) with:
     ```hcl
     github_token = "your-token"
     ```
   - Option B: `terraform apply -var="github_token=your-token"` (avoid storing in files)

2. **Initialize:**
   ```bash
   cd terraform-github
   terraform init
   ```

## Import existing repository

The repo already exists; bring it under Terraform management:

```bash
terraform import github_repository.course_repo DevOps-Core-Course
```

Then run:

```bash
terraform plan
```

Adjust `main.tf` (description, has_issues, has_wiki, etc.) so that the plan shows **no changes** — then Terraform and the live repo are in sync. After that, any future change to repo settings should go through Terraform (edit code → plan → apply).

## Apply (after import)

When you want to change repo settings via code:

```bash
terraform plan
terraform apply
```

## Why import?

- Version control for repo configuration
- Consistency and audit trail
- Changes via code review and CI
- See lab docs (e.g. `docs/LAB04.md`) for more on why importing existing resources matters.
