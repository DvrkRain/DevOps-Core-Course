output "repo_name" {
  description = "Repository name"
  value       = github_repository.course_repo.name
}

output "repo_url" {
  description = "Repository URL"
  value       = github_repository.course_repo.html_url
}
