output "vps_host" {
  description = "VPS host (IP or hostname)"
  value       = var.vps_host
}

output "ssh_connection" {
  description = "Example SSH command to connect to the VPS"
  value       = "ssh -i ${var.ssh_private_key_path} ${var.ssh_user}@${var.vps_host}"
  sensitive   = true
}
