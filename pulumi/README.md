# Pulumi — Lab 4 VPS provisioning (SSH)

Same as Terraform: connects to your **existing VPS** via SSH and configures the firewall (allow SSH 22, HTTP 80, app port 5000) using UFW. No cloud provider.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- Python 3.8+
- **SSH key-based access** to the VPS (see repo plan or `docs/LAB04.md`). Pulumi runs SSH from your machine and needs a private key (no password prompt).

## Setup

1. **Ensure key-based SSH works** (e.g. `ssh -i path/to/key user@45.38.143.11`).

2. **Create a stack** (if needed):
   ```powershell
   pulumi stack init dev
   ```

3. **Configure** (required):
   ```powershell
   pulumi config set vps_host 45.38.143.11
   pulumi config set ssh_user root
   pulumi config set ssh_private_key_path "C:/Users/YOU/.ssh/id_ed25519_devops"
   ```
   Optional: `pulumi config set ssh_port 22`, `pulumi config set project_name devops-lab04`. Do not commit stack files with secrets.

4. **Install dependencies:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Commands

```powershell
pulumi preview
pulumi up
```

Pulumi will SSH to the VPS and run the UFW commands. Connect with:

```powershell
ssh -i "C:\path\to\your\private_key" your_user@45.38.143.11
```

View outputs:

```powershell
pulumi stack output vps_host
pulumi stack output ssh_command
```

## Cleanup

`pulumi destroy` only removes stack state; it does not revert UFW on the VPS. To undo firewall changes, SSH in and adjust UFW manually.
