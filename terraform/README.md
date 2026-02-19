# Terraform — Lab 4 VPS provisioning (SSH)

Configures your **existing VPS** via SSH: connects and applies firewall rules (allow SSH 22, HTTP 80, app port 5000) using UFW. No cloud provider.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) 1.9+
- **SSH key-based access** to the VPS (see repo plan or `docs/LAB04.md` for how to switch from password to key). Terraform needs to connect without a password prompt.

## Setup

0. **Provider mirror (if registry.terraform.io is blocked):** Before `terraform init`, set the CLI config to use the Yandex mirror so providers are downloaded from `https://terraform-mirror.yandexcloud.net/`:
   ```powershell
   $env:TF_CLI_CONFIG_FILE = (Join-Path $PWD '.terraformrc')
   ```

1. **Ensure key-based SSH works** from your machine:
   ```powershell
   ssh -i "C:\Users\YOU\.ssh\id_ed25519_devops" your_user@45.38.143.11
   ```
   If this asks for a password, add your public key to the VPS `~/.ssh/authorized_keys` first.

2. **Copy and edit variables:**
   ```powershell
   copy terraform.tfvars.example terraform.tfvars
   ```
   Set `vps_host`, `ssh_user`, and `ssh_private_key_path` (full path to your private key). Do not commit `terraform.tfvars`.

## Commands

If **registry.terraform.io** is unreachable (e.g. "Invalid provider registry host"), use the Yandex mirror. From the `terraform/` directory:

```powershell
$env:TF_CLI_CONFIG_FILE = (Join-Path $PWD '.terraformrc')
terraform init
```

Then run the rest as usual (you can leave `TF_CLI_CONFIG_FILE` set for the session):

```powershell
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

After apply, Terraform will have run remote commands on the VPS (UFW rules). Connect with:

```powershell
ssh -i "C:\path\to\your\private_key" your_user@45.38.143.11
```

## Cleanup

`terraform destroy` removes the `null_resource` from state only; it does not revert UFW rules on the VPS. To undo firewall changes, SSH in and run `sudo ufw disable` or adjust rules manually.
