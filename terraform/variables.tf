variable "vps_host" {
  description = "VPS IP or hostname (e.g. 45.38.143.11)"
  type        = string
}

variable "ssh_user" {
  description = "SSH user on the VPS (e.g. root or ubuntu)"
  type        = string
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key file for key-based auth (e.g. ~/.ssh/id_ed25519_devops)"
  type        = string
  sensitive   = true
}

variable "ssh_port" {
  description = "SSH port on the VPS"
  type        = number
  default     = 22
}

variable "firewall_allow_ports" {
  description = "Ports to allow in firewall (for trigger only; actual rules in remote-exec)"
  type        = list(number)
  default     = [22, 80, 5000]
}

variable "project_name" {
  description = "Project name (for tagging/documentation)"
  type        = string
  default     = "devops-lab04"
}
