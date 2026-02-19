terraform {
  required_version = ">= 1.9.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Provision existing VPS via SSH: firewall rules for SSH (22), HTTP (80), app (5000)
resource "null_resource" "vps_provision" {
  triggers = {
    vps_host = var.vps_host
    rules    = join(",", [for p in var.firewall_allow_ports : tostring(p)])
  }

  connection {
    type        = "ssh"
    host        = var.vps_host
    user        = var.ssh_user
    private_key = file(var.ssh_private_key_path)
    port        = var.ssh_port
  }

  provisioner "remote-exec" {
    inline = [
      "set -e",
      "# Install ufw if missing (e.g. minimal image)",
      "command -v ufw >/dev/null 2>&1 || { sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ufw; }",
      "# Allow SSH first so we never lock ourselves out",
      "sudo ufw allow ${var.ssh_port}/tcp",
      "sudo ufw allow 80/tcp",
      "sudo ufw allow 5000/tcp",
      "sudo ufw --force enable",
      "echo 'VPS provisioned: SSH, HTTP 80, TCP 5000 allowed'",
    ]
  }
}
