# Lab 6: Advanced Ansible & CI/CD — Submission

**Name:** Timur Salakhov
**Date:** 2026-03-03
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

Both `common` and `docker` roles were refactored to use `block`/`rescue`/`always` sections. Tags enable selective execution without running unrelated parts of the playbook.

#### `roles/common/tasks/main.yml`

```yaml
- name: Install system packages
  block:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
    - name: Install common packages
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present
  rescue:
    - name: Fix apt cache and retry installation
      ansible.builtin.apt:
        update_cache: true
        fix_missing: true
    - name: Retry common package installation after fix
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present
  always:
    - name: Log packages block completion
      ansible.builtin.copy:
        content: "common role packages block completed\n"
        dest: /tmp/ansible_common_packages.log
        mode: "0644"
      changed_when: false
  become: true
  tags:
    - packages

- name: Configure system settings
  block:
    - name: Set system timezone
      community.general.timezone:
        name: "{{ system_timezone }}"
  become: true
  tags:
    - users
```

**Tag strategy for `common` role:**
- `packages` — apt cache update + package installation block
- `users` — timezone / system-level settings block
- `common` — entire role (applied at role level in `provision.yml`)

#### `roles/docker/tasks/main.yml`

```yaml
- name: Install Docker
  block:
    # GPG key + repo + package install
  rescue:
    # Waits 10 s, retries GPG download and package install
  always:
    # Ensures Docker service is started and enabled
  become: true
  tags:
    - docker_install

- name: Configure Docker
  block:
    # Adds user to docker group, installs python3-docker
  become: true
  tags:
    - docker_config
```

**Tag strategy for `docker` role:**
- `docker_install` — installation block (GPG key, repo, packages)
- `docker_config` — configuration block (group, python library)
- `docker` — entire role (applied at role level in `provision.yml`)

### Selective Execution Evidence

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/provision.yml --list-tags
# ansible-playbook playbooks/provision.yml --tags "docker"
# ansible-playbook playbooks/provision.yml --skip-tags "common"
# ansible-playbook playbooks/provision.yml --tags "packages"
```

### Rescue Block Triggered Evidence

```
[PASTE OUTPUT HERE — simulate a failure or document the rescue path]
```

### Research Answers

**Q: What happens if rescue block also fails?**
If the rescue block itself raises an error, Ansible marks the host as failed and the play aborts for that host. The `always` section still runs regardless.

**Q: Can you have nested blocks?**
Yes. A `block` can contain another `block` (with its own `rescue`/`always`). Inner blocks are handled first; unhandled errors propagate to the outer rescue.

**Q: How do tags inherit to tasks within blocks?**
Tags on a block are inherited by all tasks inside it. A task can also carry additional tags of its own; tag filtering is a union — a task runs if *any* of its tags (own or inherited) matches the filter.

---

## Task 2: Docker Compose (3 pts)

### Role Rename

`roles/app_deploy` was renamed to `roles/web_app`. All playbook references were updated. The new name is more descriptive and aligns with the `web_app_wipe` variable naming used in Task 3.

### Docker Compose Template

**`roles/web_app/templates/docker-compose.yml.j2`:**

```yaml
version: '3.8'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_image_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      TZ: UTC
    restart: unless-stopped
```

Variables `docker_image`, `docker_image_tag`, and `app_port` come from the Ansible Vault. `app_name` and `app_internal_port` have defaults in `roles/web_app/defaults/main.yml`, so no vault changes were required.

### Role Dependencies

**`roles/web_app/meta/main.yml`:**

```yaml
dependencies:
  - role: docker
```

This ensures Docker is installed automatically whenever `deploy.yml` is run alone, without needing to run `provision.yml` first.

### Deployment Tasks

`roles/web_app/tasks/main.yml` uses `community.docker.docker_compose_v2` (requires `community.docker >= 3.6.0` and `docker-compose-plugin`, which is already installed). The deployment is wrapped in a `block`/`rescue` so container logs are printed on failure.

### Before / After Comparison

| Aspect | Lab 5 (`app_deploy`) | Lab 6 (`web_app`) |
|---|---|---|
| Deployment method | `docker_container` module | `docker_compose_v2` module |
| Config file | None (inline task params) | `docker-compose.yml` (Jinja2 template) |
| Role dependency | Manual (run provision first) | Automatic via `meta/main.yml` |
| Wipe logic | None | `wipe.yml` (double-gated) |
| Tags | None | `app_deploy`, `compose`, `web_app_wipe` |

### Deployment Evidence

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

### Idempotency Proof (second run)

```
[PASTE OUTPUT HERE — second run should show ok=N changed=0]
```

### Application Running

```
[PASTE OUTPUT HERE]
# ssh root@45.38.143.11 "docker ps && docker compose -f /opt/devops-app/docker-compose.yml ps"
# curl http://45.38.143.11:5000/health
```

### Templated docker-compose.yml Contents

```
[PASTE OUTPUT HERE]
# ssh root@45.38.143.11 "cat /opt/devops-app/docker-compose.yml"
```

### Research Answers

**Q: What is the difference between `restart: always` and `restart: unless-stopped`?**
`restart: always` restarts the container on every failure **and** when the Docker daemon starts (e.g., after a reboot), even if the container was manually stopped. `restart: unless-stopped` behaves the same except it will *not* restart a container that was explicitly stopped by the user before the daemon restarted. `unless-stopped` is the correct default for application containers because it respects intentional `docker stop` commands.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
`docker network create` creates a plain bridge network shared across all containers globally. Docker Compose creates a project-scoped bridge network automatically, isolating containers to that project by default. Containers in the same Compose project can reach each other by service name (DNS); containers in different projects (or plain `docker run` containers) cannot unless explicitly connected.

**Q: Can you reference Ansible Vault variables in the template?**
Yes. Vault variables are decrypted in memory at playbook runtime and injected into the Ansible variable namespace. Jinja2 templates rendered by the `template` module have access to all variables, including vault-decrypted ones, just like tasks do. The plaintext values are written into the rendered file on the target host but never appear in logs (as long as `no_log: true` is set on the login task).

---

## Task 3: Wipe Logic (1 pt)

### Implementation

**Double-gating mechanism:**
1. **Tag gate** — wipe tasks are tagged `web_app_wipe`. Without `--tags web_app_wipe`, the `include_tasks` directive is skipped entirely during normal runs.
2. **Variable gate** — inside `wipe.yml`, every task has `when: web_app_wipe | bool`. The default is `false`. Without `-e "web_app_wipe=true"`, the tasks are evaluated but not executed.

Both gates must pass simultaneously for wipe to occur. This prevents accidental deletion.

**`roles/web_app/tasks/wipe.yml`:**

```yaml
- name: Wipe web application
  block:
    - name: Stop and remove containers via Docker Compose
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: true
    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent
    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent
    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ app_name }} wiped successfully"
  when: web_app_wipe | bool
  tags:
    - web_app_wipe
```

The include in `tasks/main.yml` is placed **before** the deployment block so a clean reinstall (`-e web_app_wipe=true` with no `--tags`) runs wipe first, then deploy.

### Test Scenario 1: Normal deploy (wipe must NOT run)

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/deploy.yml --ask-vault-pass
# Expected: wipe tasks skipped, app deployed normally
```

### Test Scenario 2: Wipe only

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/deploy.yml --ask-vault-pass -e "web_app_wipe=true" --tags web_app_wipe
# Expected: containers stopped, directory removed, no deployment
# Verify: ssh root@45.38.143.11 "docker ps && ls /opt"
```

### Test Scenario 3: Clean reinstall (wipe → deploy)

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/deploy.yml --ask-vault-pass -e "web_app_wipe=true"
# Expected: wipe runs first, then deploy runs fresh
# Verify: curl http://45.38.143.11:5000/health
```

### Test Scenario 4: Tag specified but variable false (wipe blocked)

```
[PASTE OUTPUT HERE]
# ansible-playbook playbooks/deploy.yml --ask-vault-pass --tags web_app_wipe
# Expected: include runs but 'when: false' skips all wipe tasks
```

### Research Answers

**Q: Why use both variable AND tag? (Double safety mechanism)**
Each gate protects against a different mistake. The tag gate prevents wipe from running during a routine `ansible-playbook deploy.yml` because no tag filter is needed — the user must consciously write `--tags web_app_wipe`. The variable gate prevents wipe from running if someone runs `--tags web_app_wipe` without realising what it does. Together they require *explicit intent* expressed in two independent places.

**Q: What is the difference between the `never` tag and this approach?**
The special Ansible `never` tag means a task only runs when explicitly included with `--tags never` or its own tag. It provides a single gate (tag only). This approach provides a double gate (tag + variable). The variable gate also allows programmatic control (e.g., CI pipelines can pass `-e web_app_wipe=true` conditionally), whereas the `never` tag cannot be toggled without changing the `--tags` argument.

**Q: Why must wipe logic come BEFORE deployment in `main.yml`?**
For the clean-reinstall scenario (`-e "web_app_wipe=true"` with no `--tags`), Ansible runs all tasks in order. If wipe came after deploy, the deployment would succeed and then be immediately destroyed. Placing wipe first produces the intended sequence: remove old → install fresh.

**Q: When would you want clean reinstallation vs. rolling update?**
Rolling update is preferable when you need zero downtime and the old and new versions are compatible. Clean reinstallation is appropriate when state from the previous deployment may interfere (corrupted volumes, changed port mappings, schema changes), or when performing a major version upgrade where backward compatibility is not guaranteed.

**Q: How would you extend this to wipe Docker images and volumes too?**
Add tasks using `community.docker.docker_image` with `state: absent` and `community.docker.docker_volume` with `state: absent`, gated by additional role variables (e.g., `web_app_wipe_images: false`, `web_app_wipe_volumes: false`) for granular control.

---

## Task 4: CI/CD (3 pts)

### Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

```
Push to main/master (paths: ansible/**, !ansible/docs/**)
  │
  ├── lint job (ubuntu-latest)
  │     Install ansible + ansible-lint
  │     Install collections (requirements.yml)
  │     ansible-lint playbooks/provision.yml playbooks/deploy.yml
  │
  └── deploy job (ubuntu-latest, needs: lint, push only)
        Install ansible + collections
        Setup SSH from GitHub Secret (SSH_PRIVATE_KEY)
        Write vault password from secret (ANSIBLE_VAULT_PASSWORD)
        ansible-playbook playbooks/deploy.yml
        curl http://VM_HOST:5000/health  ← verification
```

**Path filters** prevent the workflow from running on documentation-only commits:
```yaml
paths:
  - 'ansible/**'
  - '!ansible/docs/**'
  - '.github/workflows/ansible-deploy.yml'
```

### GitHub Secrets Required

| Secret | Value |
|---|---|
| `ANSIBLE_VAULT_PASSWORD` | Contents of `~/.vault_pass_lab05` |
| `SSH_PRIVATE_KEY` | Contents of `~/.ssh/id_ed25519_devops` |
| `VM_HOST` | `45.38.143.11` |
| `VM_USER` | `root` |

### CI/CD Workflow Evidence

```
[PASTE SCREENSHOT OR WORKFLOW LOG HERE]
# GitHub Actions tab → ansible-deploy.yml run
```

### ansible-lint Passing Evidence

```
[PASTE WORKFLOW LOG OUTPUT HERE]
# lint job log showing 0 errors
```

### Deployment Verification Step Output

```
[PASTE OUTPUT HERE]
# deploy job log showing curl -f http://45.38.143.11:5000/health succeeding
```

### Status Badge

[![Ansible Deployment](https://github.com/DvrkRain/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/DvrkRain/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

### Research Answers

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**
GitHub Secrets are encrypted at rest and only exposed to workflow runs on the repository. They are never shown in logs and are unavailable to fork PRs by default. However, any contributor with write access who can modify workflow files could add a step to exfiltrate secrets. Mitigations include protecting the main branch with required reviews, restricting which branches/events can access environment-level secrets, and using short-lived credentials (e.g., OIDC tokens) where possible.

**Q: How would you implement a staging → production deployment pipeline?**
Define two GitHub Environments (`staging` and `production`). The `staging` deploy job runs automatically on every push; the `production` job requires a manual approval gate configured in the environment settings. Each environment holds its own secrets (separate VMs, vault passwords). The workflow checks `github.environment` to select the correct inventory file.

**Q: What would you add to make rollbacks possible?**
Tag every Docker image with the Git commit SHA at build time (in `python-ci.yml`). Store the last-known-good tag in a variable file or SSM parameter. Add a `rollback.yml` playbook that accepts a `rollback_tag` variable and re-deploys the specified image version. In CI, save the previous tag before deploying so a subsequent workflow step can trigger rollback on failure.

**Q: How does a self-hosted runner improve security compared to a GitHub-hosted runner?**
A self-hosted runner runs on your own infrastructure, so SSH keys and vault passwords never leave your network — the runner connects outward to GitHub rather than GitHub connecting inward to your server. It also removes the need to expose the target server's SSH port to GitHub's IP ranges. The trade-off is that the runner machine itself must be hardened and kept up to date.

---

## Task 5: Documentation

This file serves as the required documentation. All implementation details, code snippets, test results, and research answers are included in the sections above.

---

## Summary

**Technologies used:** Ansible 2.16+, community.docker 3.6+, community.general, Docker Compose v2 (plugin), GitHub Actions, Jinja2, Ansible Vault (AES-256)

**Key improvements over Lab 5:**
- Roles now use blocks for logical grouping, error handling, and guaranteed cleanup
- Tags enable partial execution without editing playbooks
- Docker Compose replaces raw `docker_container` calls, making deployment declarative and file-backed
- Role dependency in `meta/main.yml` removes the two-playbook dependency
- Wipe logic with double-gating makes destructive operations safe to automate
- GitHub Actions automates lint + deploy on every relevant push

**Total time spent:** [FILL IN]

**Key learnings:**
- Ansible blocks/rescue/always mirror try/except/finally patterns from general programming
- `include_tasks` with tags enables conditional file inclusion without the `never` tag anti-pattern
- `docker_compose_v2` requires the Docker Compose v2 plugin (installed as `docker-compose-plugin`) rather than the standalone Python library
- Path filters in GitHub Actions are essential to prevent unrelated commits from triggering expensive workflows
