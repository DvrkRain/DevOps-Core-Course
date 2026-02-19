terraform {
  required_version = ">= 1.9.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
}

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false
  has_discussions = false

  # Align these with your existing repo after import; run terraform plan and adjust until no changes
  allow_auto_merge            = false
  allow_merge_commit           = true
  allow_rebase_merge           = true
  allow_squash_merge          = true
  delete_branch_on_merge      = false
}
