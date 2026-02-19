"""
Lab 4 — Pulumi: Provision existing VPS via SSH (same as Terraform).
Connects to VPS and configures firewall: allow SSH 22, HTTP 80, app port 5000.
"""
import pulumi
import paramiko

config = pulumi.Config()
vps_host = config.require("vps_host")
ssh_user = config.require("ssh_user")
ssh_private_key_path = config.require("ssh_private_key_path")
ssh_port = config.get_int("ssh_port") or 22
project_name = config.get("project_name") or "devops-lab04"

# Commands equivalent to Terraform remote-exec (UFW: allow 22, 80, 5000; enable)
commands = [
    "set -e",
    f"sudo ufw allow {ssh_port}/tcp",
    "sudo ufw allow 80/tcp",
    "sudo ufw allow 5000/tcp",
    "sudo ufw --force enable",
    "echo 'VPS provisioned: SSH, HTTP 80, TCP 5000 allowed'",
]

# Run provisioning via SSH (executes on first 'pulumi up')
def run_ssh_provisioning():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=vps_host,
        username=ssh_user,
        key_filename=ssh_private_key_path,
        port=ssh_port,
    )
    try:
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                err = stderr.read().decode()
                raise RuntimeError(f"Command failed: {cmd}: {err}")
    finally:
        client.close()

# Run during preview/up (Pulumi doesn't have a direct "provisioner" — we run once and export)
run_ssh_provisioning()

pulumi.export("vps_host", vps_host)
pulumi.export("ssh_command", f"ssh -i {ssh_private_key_path} {ssh_user}@{vps_host}")
