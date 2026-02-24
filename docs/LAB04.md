# Lab 4 — Infrastructure as Code (VPS-only, Terraform & Pulumi)

This lab uses **only your existing VPS** (no cloud provider). Terraform and Pulumi connect to the VPS via SSH and configure it (firewall: SSH 22, HTTP 80, app port 5000). See the plan in the repo for **SSH key setup** (switch from password to key-based login).

---

## 1. VPS & Infrastructure

- **Target:** Single VPS, Ubuntu 24.04 LTS, 1 CPU, 2GB RAM, 20GB storage.
- **No cloud provider:** Using only my VPS; no AWS or other cloud. All provisioning is done via SSH to this host.
- **Cost:** Existing VPS cost only; no extra cloud charges.
- **Resources configured (list):**
  - [x] Firewall (UFW): allow SSH (22), HTTP (80), TCP (5000)
  - [x] Provisioning via SSH (Terraform: null_resource + remote-exec; Pulumi: paramiko SSH)

---

## 2. Terraform Implementation

- **Terraform version used:** (See terminal output above; e.g. run `terraform version` to paste.)
- **Project structure:** `terraform/` contains `main.tf` (null_resource + SSH connection + remote-exec), `variables.tf`, `outputs.tf`, `terraform.tfvars.example`, `.gitignore`, `README.md`, `.tflint.hcl`.
- **Key configuration decisions:** VPS host and SSH user/key path set via variables (terraform.tfvars, not committed). UFW rules: allow SSH port first, then 80 and 5000, then enable. Provisioner installs UFW if missing so it works on minimal images.
- **Challenges encountered:** Registry unreachable — used Yandex mirror (TF_CLI_CONFIG_FILE + .terraformrc). Output referred to sensitive variable — marked ssh_connection output as sensitive. UFW not installed on VPS — added apt-get install ufw in remote-exec.

### Terminal output (sanitized — no secrets)

**terraform init:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\terraform> terraform init
Initializing the backend...
Initializing provider plugins...
- Reusing previous version of hashicorp/null from the dependency lock file
- Using previously-installed hashicorp/null v3.2.4

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

**terraform plan (sanitized):**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\terraform> terraform plan

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with
the following symbols:
  + create

Terraform will perform the following actions:

  # null_resource.vps_provision will be created
  + resource "null_resource" "vps_provision" {
      + id       = (known after apply)
      + triggers = {
          + "rules"    = "22,80,5000"
          + "vps_host" = "**.**.**.**"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (sensitive value)
  + vps_host       = "**.**.**.**"

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if 
you run "terraform apply" now.
```

**terraform apply:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\terraform> terraform apply

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with   
the following symbols:
  + create

Terraform will perform the following actions:

  # null_resource.vps_provision will be created
  + resource "null_resource" "vps_provision" {
      + id       = (known after apply)
      + triggers = {
          + "rules"    = "22,80,5000"
          + "vps_host" = "**.**.**.**"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ssh_connection = (sensitive value)
  + vps_host       = "**.**.**.**"

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

null_resource.vps_provision: Creating...
null_resource.vps_provision: Provisioning with 'remote-exec'...
null_resource.vps_provision (remote-exec): Connecting to remote host via SSH...
null_resource.vps_provision (remote-exec):   Host: **.**.**.**
null_resource.vps_provision (remote-exec):   User: root
null_resource.vps_provision (remote-exec):   Password: false
null_resource.vps_provision (remote-exec):   Private key: true
null_resource.vps_provision (remote-exec):   Certificate: false
null_resource.vps_provision (remote-exec):   SSH Agent: false
null_resource.vps_provision (remote-exec):   Checking Host Key: false
null_resource.vps_provision (remote-exec):   Target Platform: unix
null_resource.vps_provision (remote-exec): Connected!
null_resource.vps_provision (remote-exec): Skipping adding existing rule
null_resource.vps_provision (remote-exec): Skipping adding existing rule (v6)
null_resource.vps_provision (remote-exec): Skipping adding existing rule
null_resource.vps_provision (remote-exec): Skipping adding existing rule (v6)
null_resource.vps_provision (remote-exec): Skipping adding existing rule
null_resource.vps_provision (remote-exec): Skipping adding existing rule (v6)
null_resource.vps_provision (remote-exec): Firewall is active and enabled on system startup
null_resource.vps_provision (remote-exec): VPS provisioned: SSH, HTTP 80, TCP 5000 allowed
null_resource.vps_provision: Creation complete after 2s [id=1579046701816394]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

ssh_connection = <sensitive>
vps_host = "**.**.**.**"
```

**SSH connection to VPS:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\terraform> ssh -i "$env:USERPROFILE\.ssh\id_ed25519_devops" root@**.**.**.**         
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro
Last login: Thu Feb 19 17:17:53 2026 from **.**.**.**
root@dvrg:~# 
```

---

## 3. Pulumi Implementation

- **Pulumi version and language used:** v3.221.0; language: Python.
- **How code differs from Terraform:** Python + paramiko for SSH vs HCL remote-exec; same UFW commands run on the VPS. Config via pulumi config set instead of tfvars. No persistent resource for “provisioning” — code runs at stack create/update and exports outputs.
- **Advantages you discovered:** Familiar language (Python), easy to add logic or libraries. Config and secrets (passphrase) built in. Same outcome as Terraform for this task.
- **Challenges encountered:** Must set required config (vps_host, ssh_user, ssh_private_key_path) before first run. Passphrase prompt unless PULUMI_CONFIG_PASSPHRASE is set. No native “provisioner” — SSH runs on every up; idempotent UFW commands are safe.

### Terminal output (sanitized)

**pulumi preview:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\pulumi> pulumi preview
Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):
Enter your passphrase to unlock config/secrets
Previewing update (stack):
     Type                 Name                Plan
 +   pulumi:pulumi:Stack  devops-lab04-stack  create
Outputs:
    ssh_command: "ssh -i C:/Users/claym/.ssh/id_ed25519_devops root@**.**.**.**"
    vps_host   : "**.**.**.**"

Resources:
    + 1 to create
```

**pulumi up:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\pulumi> pulumi up
Enter your passphrase to unlock config/secrets
    (set PULUMI_CONFIG_PASSPHRASE or PULUMI_CONFIG_PASSPHRASE_FILE to remember):
Enter your passphrase to unlock config/secrets
Previewing update (stack):
     Type                 Name                Plan
 +   pulumi:pulumi:Stack  devops-lab04-stack  create
Outputs:
    ssh_command: "ssh -i C:/Users/claym/.ssh/id_ed25519_devops root@**.**.**.**"
    vps_host   : "**.**.**.**"

Resources:
    + 1 to create

info: There are no resources in your stack (other than the stack resource).

Do you want to perform this update? yes
Updating (stack):
     Type                 Name                Status
 +   pulumi:pulumi:Stack  devops-lab04-stack  created (0.03s)
Outputs:
    ssh_command: "ssh -i C:/Users/claym/.ssh/id_ed25519_devops root@**.**.**.**"
    vps_host   : "**.**.**.**"

Resources:
    + 1 created

Duration: 4s
```

**SSH connection to VPS:**
```
(venv) PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\pulumi> ssh -i C:/Users/claym/.ssh/id_ed25519_devops root@**.**.**.**
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro
Last login: Thu Feb 19 17:20:05 2026 from **.**.**.**
root@dvrg:~# 
```

---

## 4. Terraform vs Pulumi Comparison

- **Ease of Learning:** Terraform was easier for this lab: HCL is small and the workflow (init, plan, apply) is standard. Pulumi required Python and Pulumi config; the “run SSH on up” pattern is less obvious than a provisioner. Both are learnable; Terraform has more IaC-specific docs.
- **Code Readability:** Terraform is short and declarative (one null_resource, connection, remote-exec). Pulumi is imperative Python; you see exactly what runs (paramiko connect, exec_command). Readability depends on preference: HCL for infra-only, Python if you like code and reuse.
- **Debugging:** Terraform: plan shows what will run; failed remote-exec shows the last command and exit code. Pulumi: stack trace and Python errors; SSH failures surface as exceptions. Both are debuggable; Terraform’s plan step gives a clear preview.
- **Documentation:** Terraform has strong docs and examples for provisioners, connection, and providers. Pulumi docs cover config and Python SDK; for “SSH and run commands” you rely on paramiko or custom code. Terraform’s model (provisioners) is better documented for this use case.
- **Use Case:** Use Terraform when you want declarative IaC, large ecosystem, and team familiarity with HCL; good for cloud and mixed environments. Use Pulumi when you want a real language, reuse, tests, or to mix infra with app logic; good when the team prefers Python/TypeScript/Go.

---

## 5. Lab 5 Preparation & Cleanup

**VPS for Lab 5:**
- Same VPS is used for Lab 4 and Lab 5: Yes, using this VPS for Ansible in Lab 5

**Cleanup Status:**
- Terraform/Pulumi do not “destroy” the VPS; they only remove their state. Firewall rules remain. Ran terraform destroy and/or pulumi destroy as needed; UFW stays configured on the VPS. Same VPS is kept for Lab 5 (Ansible).
- Optional: Paste terminal output of `terraform destroy` and/or `pulumi destroy` here if you ran them.

---

## Bonus: IaC CI/CD (Terraform workflow)

- **Workflow file:** `.github/workflows/terraform-ci.yml` — runs on changes to `terraform/**`; steps: `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`, `tflint`.
- **Proof:** Push a commit that touches `terraform/**` (or the workflow file) and open a PR; the Terraform CI job runs. All steps (fmt -check, init, validate, tflint) should pass. Link the PR or workflow run here.

---

## Bonus: GitHub Repository Import

- **Why importing existing resources matters:** Brings existing infra under IaC: version control for settings, consistency, change via code review and CI, and living documentation. Avoids recreating resources and lets you manage repos/settings in code.
- **Import command run:** `terraform import github_repository.course_repo DevOps-Core-Course` (from `terraform-github/` after `terraform init`).
- **Terminal output of import:** Paste the output of the import command here after running it (e.g. "github_repository.course_repo: Import prepared..." and "Import successful!").
- **Verification:** After aligning `github_repository` config with the real repo (description, has_issues, has_wiki, etc.), run `terraform plan` in terraform-github/; it should show "No changes." so state matches the live repo.
