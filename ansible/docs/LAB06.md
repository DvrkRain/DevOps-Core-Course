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
---
- name: Install system packages
  become: true
  tags:
    - packages
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

- name: Configure system settings
  become: true
  tags:
    - users
  block:
    - name: Set system timezone
      community.general.timezone:
        name: "{{ common_timezone }}"
```

**Tag strategy for `common` role:**
- `packages` — apt cache update + package installation block
- `users` — timezone / system-level settings block
- `common` — entire role (applied at role level in `provision.yml`)

#### `roles/docker/tasks/main.yml`

```yaml
---
- name: Install Docker
  become: true
  tags:
    - docker_install
  block:
    - name: Install Docker prerequisites
      ansible.builtin.apt:
        name:
          - ca-certificates
          - curl
          - gnupg
        state: present

    - name: Create Docker GPG keyring directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"

    - name: Download Docker GPG key
      ...

    - name: Add Docker apt repository
      ...

    - name: Install Docker packages
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
        update_cache: true
      notify: Restart docker

  rescue:
    - name: Wait before retrying after GPG key failure
      ansible.builtin.wait_for:
        timeout: 10

    - name: Retry Docker GPG key download
      ...

    - name: Retry Docker package installation
      ...

  always:
    - name: Ensure Docker service is started and enabled
      ansible.builtin.service:
        name: docker
        state: started
        enabled: true
      ignore_errors: true

- name: Configure Docker
  become: true
  tags:
    - docker_config
  block:
    - name: Add user to docker group
      ansible.builtin.user:
        name: "{{ docker_user }}"
        groups: docker
        append: true

    - name: Install python3-docker for Ansible Docker modules
      ansible.builtin.apt:
        name: python3-docker
        state: present

```

**Tag strategy for `docker` role:**
- `docker_install` — installation block (GPG key, repo, packages)
- `docker_config` — configuration block (group, python library)
- `docker` — entire role (applied at role level in `provision.yml`)

### Selective Execution Evidence

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml --list-tags
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: No inventory was parsed, only implicit localhost is available
[WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'
[WARNING]: Collection community.general does not support Ansible version 2.16.3
[WARNING]: Could not match supplied host pattern, ignoring: webservers

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 --tags "docker"
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.general does not support Ansible version 2.16.3

PLAY [Provision web servers] *******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install Docker prerequisites] ******************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Create Docker GPG keyring directory] ***********************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Download Docker GPG key] ***********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Add Docker apt repository] *********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install Docker packages] ***********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Ensure Docker service is started and enabled] **************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Add user to docker group] **********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install python3-docker for Ansible Docker modules] *********************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 --skip-tags "common"
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.general does not support Ansible version 2.16.3

PLAY [Provision web servers] *******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install Docker prerequisites] ******************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Create Docker GPG keyring directory] ***********************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Download Docker GPG key] ***********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Add Docker apt repository] *********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install Docker packages] ***********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Ensure Docker service is started and enabled] **************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Add user to docker group] **********************************************************************************************************
ok: [dvrg]

TASK [../roles/docker : Install python3-docker for Ansible Docker modules] *********************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 --tags "packages"
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.general does not support Ansible version 2.16.3

PLAY [Provision web servers] *******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [../roles/common : Update apt cache] ******************************************************************************************************************
ok: [dvrg]

TASK [../roles/common : Install common packages] ***********************************************************************************************************
ok: [dvrg]

TASK [../roles/common : Log packages block completion] *****************************************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Rescue Block Triggered Evidence

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***************************************************************************************************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ********************************************************************************************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] ******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] ***********************************************************************************************
ok: [dvrg]

TASK [docker : Add user to docker group] *******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] ******************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log in to Docker Hub] *************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Create application directory] *****************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Template docker-compose file] *****************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Deploy with Docker Compose] *******************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
fatal: [dvrg]: FAILED! => {"actions": [{"id": "timursalakhov/devops-info-service:latest", "status": "Pulling", "what": "image"}, {"id": "devops-app_default", "status": "Creating", "what": "network"}, {"id": "devops-app", "status": "Creating", "what": "container"}, {"id": "devops-app", "status": "Starting", "what": "container"}], "changed": true, "cmd": "/usr/bin/docker compose --ansi never --progress json --project-directory /opt/devops-app up --detach --no-color --quiet-pull --pull always --", "containers": [{"Command": "\"python app.py\"", "CreatedAt": "2026-03-03 15:59:53 +0000 UTC", "ExitCode": 0, "Health": "", "ID": "a77efc401269bb8fad66e0ed36620b790ef97041d0390195f434c818c6774cd6", "Image": "timursalakhov/devops-info-service:latest", "Labels": {" Ansible": "", " CI/CD": "", " GitOps (ArgoCD)": "", " Helm": "", " Kubernetes": "", " Terraform": "", " and cloud-native deployments.": "", " and more. Build real-world skills with progressive delivery": "", " monitoring (Prometheus/Grafana)": "", " secrets management": "", "com.docker.compose.config-hash": "f9d61ca1a975e7780d6f62f544629b1a70cce3ccbbc678a198e519143bd74908", "com.docker.compose.container-number": "1", "com.docker.compose.depends_on": "", "com.docker.compose.image": "sha256:694c0cc7fdd909fb2bd0035abcb3ac2d51062e8a4f2509d1fecd918ee302b56a", "com.docker.compose.oneoff": "False", "com.docker.compose.project": "devops-app", "com.docker.compose.project.config_files": "/opt/devops-app/docker-compose.yml", "com.docker.compose.project.working_dir": "/opt/devops-app", "com.docker.compose.service": "devops-app", "com.docker.compose.version": "5.0.2", "description": "DevOps Info Service", "maintainer": "t.salakhov@innopolis.university", "org.opencontainers.image.created": "2026-02-11T17:30:09.007Z", "org.opencontainers.image.description": "🚀Production-grade DevOps course: 18 hands-on labs covering Docker", "org.opencontainers.image.licenses": "", "org.opencontainers.image.revision": "4d4852e18b6961e788843135e0c436c6010a0b3e", "org.opencontainers.image.source": "https://github.com/DvrkRain/DevOps-Core-Course", "org.opencontainers.image.title": "DevOps-Core-Course", "org.opencontainers.image.url": "https://github.com/DvrkRain/DevOps-Core-Course", "org.opencontainers.image.version": "2026.02.11-4", "version": "1.0.0"}, "LocalVolumes": "0", "Mounts": "", "Name": "devops-app", "Names": ["devops-app"], "Networks": [""], "Ports": "", "Project": "devops-app", "Publishers": [], "RunningFor": "1 second ago", "Service": "devops-app", "Size": "0B", "State": "created", "Status": "Created"}], "images": [{"ContainerName": "devops-app", "Created": "2026-02-11T17:17:15.29267436Z", "ID": "sha256:694c0cc7fdd909fb2bd0035abcb3ac2d51062e8a4f2509d1fecd918ee302b56a", "LastTagTime": "2026-03-03T15:59:53.226501039Z", "Platform": "linux/amd64", "Repository": "timursalakhov/devops-info-service", "Size": 83741873, "Tag": "latest"}], "msg": "General error: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (ab87aee7daec9f58021297ccb514b4114d24b6be5b1e3e870356319eeb69d8d9): Bind for 0.0.0.0:5000 failed: port is already allocated", "rc": 1, "stderr": "{\"level\":\"warning\",\"msg\":\"/opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion\",\"time\":\"2026-03-03T15:59:51Z\"}\n{\"id\":\"Image timursalakhov/devops-info-service:latest\",\"status\":\"Working\",\"text\":\"Pulling\"}\n{\"id\":\"Image timursalakhov/devops-info-service:latest\",\"status\":\"Done\",\"text\":\"Pulled\"}\n{\"id\":\"Network devops-app_default\",\"status\":\"Working\",\"text\":\"Creating\"}\n{\"id\":\"Network devops-app_default\",\"status\":\"Done\",\"text\":\"Created\"}\n{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Creating\"}\n{\"id\":\"Container devops-app\",\"status\":\"Done\",\"text\":\"Created\"}\n{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Starting\"}\n{\"error\":true,\"message\":\"Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (ab87aee7daec9f58021297ccb514b4114d24b6be5b1e3e870356319eeb69d8d9): Bind for 0.0.0.0:5000 failed: port is already allocated\"}\n", "stderr_lines": ["{\"level\":\"warning\",\"msg\":\"/opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion\",\"time\":\"2026-03-03T15:59:51Z\"}", "{\"id\":\"Image timursalakhov/devops-info-service:latest\",\"status\":\"Working\",\"text\":\"Pulling\"}", "{\"id\":\"Image timursalakhov/devops-info-service:latest\",\"status\":\"Done\",\"text\":\"Pulled\"}", "{\"id\":\"Network devops-app_default\",\"status\":\"Working\",\"text\":\"Creating\"}", "{\"id\":\"Network devops-app_default\",\"status\":\"Done\",\"text\":\"Created\"}", "{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Creating\"}", "{\"id\":\"Container devops-app\",\"status\":\"Done\",\"text\":\"Created\"}", "{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Starting\"}", "{\"error\":true,\"message\":\"Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (ab87aee7daec9f58021297ccb514b4114d24b6be5b1e3e870356319eeb69d8d9): Bind for 0.0.0.0:5000 failed: port is already allocated\"}"], "stdout": "", "stdout_lines": []}

TASK [../roles/web_app : Log deployment failure] ***********************************************************************************************************
ok: [dvrg] => {
    "msg": "Deployment of devops-app failed — check container logs below."
}

TASK [../roles/web_app : Show container logs on failure] ***************************************************************************************************
ok: [dvrg]

RUNNING HANDLER [../roles/web_app : Restart web app] *******************************************************************************************************
fatal: [dvrg]: FAILED! => {"actions": [{"id": "devops-app", "status": "Recreate", "what": "container"}, {"id": "devops-app", "status": "Starting", "what": "container"}], "changed": true, "cmd": "/usr/bin/docker compose --ansi never --progress json --project-directory /opt/devops-app up --detach --no-color --quiet-pull --force-recreate --", "containers": [{"Command": "\"python app.py\"", "CreatedAt": "2026-03-03 15:59:59 +0000 UTC", "ExitCode": 0, "Health": "", "ID": "b278acd4a3ceed2078ad20d67d1e34f4d050f38585cb30f8d0c83036f052c17d", "Image": "timursalakhov/devops-info-service:latest", "Labels": {" Ansible": "", " CI/CD": "", " GitOps (ArgoCD)": "", " Helm": "", " Kubernetes": "", " Terraform": "", " and cloud-native deployments.": "", " and more. Build real-world skills with progressive delivery": "", " monitoring (Prometheus/Grafana)": "", " secrets management": "", "com.docker.compose.config-hash": "f9d61ca1a975e7780d6f62f544629b1a70cce3ccbbc678a198e519143bd74908", "com.docker.compose.container-number": "1", "com.docker.compose.depends_on": "", "com.docker.compose.image": "sha256:694c0cc7fdd909fb2bd0035abcb3ac2d51062e8a4f2509d1fecd918ee302b56a", "com.docker.compose.oneoff": "False", "com.docker.compose.project": "devops-app", "com.docker.compose.project.config_files": "/opt/devops-app/docker-compose.yml", "com.docker.compose.project.working_dir": "/opt/devops-app", "com.docker.compose.replace": "devops-app", "com.docker.compose.service": "devops-app", "com.docker.compose.version": "5.0.2", "description": "DevOps Info Service", "maintainer": "t.salakhov@innopolis.university", "org.opencontainers.image.created": "2026-02-11T17:30:09.007Z", "org.opencontainers.image.description": "🚀Production-grade DevOps course: 18 hands-on labs covering Docker", "org.opencontainers.image.licenses": "", "org.opencontainers.image.revision": "4d4852e18b6961e788843135e0c436c6010a0b3e", "org.opencontainers.image.source": "https://github.com/DvrkRain/DevOps-Core-Course", "org.opencontainers.image.title": "DevOps-Core-Course", "org.opencontainers.image.url": "https://github.com/DvrkRain/DevOps-Core-Course", "org.opencontainers.image.version": "2026.02.11-4", "version": "1.0.0"}, "LocalVolumes": "0", "Mounts": "", "Name": "devops-app", "Names": ["devops-app"], "Networks": [""], "Ports": "", "Project": "devops-app", "Publishers": [], "RunningFor": "1 second ago", "Service": "devops-app", "Size": "0B", "State": "created", "Status": "Created"}], "images": [{"ContainerName": "devops-app", "Created": "2026-02-11T17:17:15.29267436Z", "ID": "sha256:694c0cc7fdd909fb2bd0035abcb3ac2d51062e8a4f2509d1fecd918ee302b56a", "LastTagTime": "2026-03-03T15:59:53.226501039Z", "Platform": "linux/amd64", "Repository": "timursalakhov/devops-info-service", "Size": 83741873, "Tag": "latest"}], "msg": "General error: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (55936ca0ae0e5117ee91585a0d7052cfd8f5ba8b1530a1a9541d72f878e54c8e): Bind for 0.0.0.0:5000 failed: port is already allocated", "rc": 1, "stderr": "{\"level\":\"warning\",\"msg\":\"/opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion\",\"time\":\"2026-03-03T15:59:59Z\"}\n{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Recreate\"}\n{\"id\":\"Container devops-app\",\"status\":\"Done\",\"text\":\"Recreated\"}\n{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Starting\"}\n{\"error\":true,\"message\":\"Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (55936ca0ae0e5117ee91585a0d7052cfd8f5ba8b1530a1a9541d72f878e54c8e): Bind for 0.0.0.0:5000 failed: port is already allocated\"}\n", "stderr_lines": ["{\"level\":\"warning\",\"msg\":\"/opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion\",\"time\":\"2026-03-03T15:59:59Z\"}", "{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Recreate\"}", "{\"id\":\"Container devops-app\",\"status\":\"Done\",\"text\":\"Recreated\"}", "{\"id\":\"Container devops-app\",\"status\":\"Working\",\"text\":\"Starting\"}", "{\"error\":true,\"message\":\"Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devops-app (55936ca0ae0e5117ee91585a0d7052cfd8f5ba8b1530a1a9541d72f878e54c8e): Bind for 0.0.0.0:5000 failed: port is already allocated\"}"], "stdout": "", "stdout_lines": []}

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=15   changed=2    unreachable=0    failed=1    skipped=4    rescued=1    ignored=0
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
  {{ web_app_name }}:
    image: {{ docker_image }}:{{ docker_image_tag }}
    container_name: {{ web_app_name }}
    ports:
      - "{{ app_port }}:{{ web_app_internal_port }}"
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

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***************************************************************************************************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ********************************************************************************************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] ******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] ***********************************************************************************************
ok: [dvrg]

TASK [docker : Add user to docker group] *******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] ******************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log in to Docker Hub] *************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Create application directory] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Template docker-compose file] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Deploy with Docker Compose] *******************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
changed: [dvrg]

TASK [../roles/web_app : Wait for application port to be ready] ********************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Verify application health endpoint] ***********************************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=16   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### Idempotency Proof (second run)

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***************************************************************************************************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ********************************************************************************************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] ******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] ***********************************************************************************************
ok: [dvrg]

TASK [docker : Add user to docker group] *******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] ******************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log in to Docker Hub] *************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Create application directory] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Template docker-compose file] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Deploy with Docker Compose] *******************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
ok: [dvrg]

TASK [../roles/web_app : Wait for application port to be ready] ********************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Verify application health endpoint] ***********************************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=16   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### Application Running

```shell
PS C:\Users\claym> ssh -i C:\Users\claym\.ssh\id_ed25519_devops root@45.38.143.11 "docker ps && docker compose -f /opt/devops-app/docker-compose.yml ps"
CONTAINER ID   IMAGE                                      COMMAND                  CREATED         STATUS         PORTS                                               NAMES
bd0493a0bf3a   timursalakhov/devops-info-service:latest   "python app.py"          3 minutes ago   Up 3 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp         devops-app
d1f412a1d6d0   whn0thacked/telemt-docker:latest           "/usr/local/bin/tele…"   7 days ago      Up 7 days      0.0.0.0:443->443/tcp, [::]:443->443/tcp, 9090/tcp   telemt
time="2026-03-03T16:07:53Z" level=warning msg="/opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
NAME         IMAGE                                      COMMAND           SERVICE      CREATED         STATUS         PORTS
devops-app   timursalakhov/devops-info-service:latest   "python app.py"   devops-app   3 minutes ago   Up 3 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
PS C:\Users\claym> curl http://45.38.143.11:5000/health

Предупреждение безопасности: риск выполнения сценария
Invoke-WebRequest анализирует содержимое веб-страницы. При анализе страницы может выполняться код сценария на веб-странице.
      РЕКОМЕНДУЕМОЕ ДЕЙСТВИЕ:
      Используйте параметр -UseBasicParsing, чтобы предотвратить выполнение кода сценария.

      Продолжить?

[Y] Да - Y  [A] Да для всех - A  [N] Нет - N  [L] Нет для всех - L  [S] Приостановить - S  [?] Справка (значением по умолчанию является "N"): A


StatusCode        : 200
StatusDescription : OK
Content           : {"status":"healthy","timestamp":"2026-03-03T16:08:16.743469+00:00","uptime_seconds":235}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 88
                    Content-Type: application/json
                    Date: Tue, 03 Mar 2026 16:08:16 GMT
                    Server: uvicorn

                    {"status":"healthy","timestamp":"2026-03-03T16:08:16.743469+00:00","uptime_...
Forms             : {}
Headers           : {[Content-Length, 88], [Content-Type, application/json], [Date, Tue, 03 Mar 2026 16:08:16 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 88
```

### Templated docker-compose.yml Contents

```shell
PS C:\Users\claym> ssh -i C:\Users\claym\.ssh\id_ed25519_devops root@45.38.143.11 "cat /opt/devops-app/docker-compose.yml"
version: '3.8'

services:
  devops-app:
    image: timursalakhov/devops-info-service:latest
    container_name: devops-app
    ports:
      - "5000:5000"
    environment:
      TZ: UTC
    restart: unless-stopped
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
  when: web_app_wipe | bool
  tags:
    - web_app_wipe
  block:
    - name: Stop and remove containers via Docker Compose
      community.docker.docker_compose_v2:
        project_src: "{{ web_app_compose_dir }}"
        state: absent
      ignore_errors: true

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}"
        state: absent

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ web_app_name }} wiped successfully from {{ web_app_compose_dir }}"
```

The include in `tasks/main.yml` is placed **before** the deployment block so a clean reinstall (`-e web_app_wipe=true` with no `--tags`) runs wipe first, then deploy.

### Test Scenario 1: Normal deploy (wipe must NOT run)

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***************************************************************************************************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ********************************************************************************************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] ******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] ***********************************************************************************************
ok: [dvrg]

TASK [docker : Add user to docker group] *******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] ******************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log in to Docker Hub] *************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Create application directory] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Template docker-compose file] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Deploy with Docker Compose] *******************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
ok: [dvrg]

TASK [../roles/web_app : Wait for application port to be ready] ********************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Verify application health endpoint] ***********************************************************************************************
ok: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=16   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### Test Scenario 2: Wipe only

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 -e "web_app_wipe=true" --tags web_app_wipe
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
changed: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
ok: [dvrg] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Test Scenario 3: Clean reinstall (wipe → deploy)

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 -e "web_app_wipe=true"
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***************************************************************************************************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ********************************************************************************************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] ******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ********************************************************************************************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] ***********************************************************************************************
ok: [dvrg]

TASK [docker : Add user to docker group] *******************************************************************************************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] ******************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
fatal: [dvrg]: FAILED! => {"changed": false, "msg": "\"/opt/devops-app\" is not a directory"}
...ignoring

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
ok: [dvrg] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

TASK [../roles/web_app : Log in to Docker Hub] *************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Create application directory] *****************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Template docker-compose file] *****************************************************************************************************
changed: [dvrg]

TASK [../roles/web_app : Deploy with Docker Compose] *******************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to
avoid potential confusion
changed: [dvrg]

TASK [../roles/web_app : Wait for application port to be ready] ********************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Verify application health endpoint] ***********************************************************************************************
ok: [dvrg]

RUNNING HANDLER [../roles/web_app : Restart web app] *******************************************************************************************************
changed: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=21   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1

claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ curl http://45.38.143.11:5000/health
{"status":"healthy","timestamp":"2026-03-03T16:28:17.295820+00:00","uptime_seconds":19}
```

### Test Scenario 4: Tag specified but variable false (wipe blocked)

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ~/.vault_pass_lab05 --tags web_app_wipe
[WARNING]: Ansible is being run in a world writable directory (/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible), ignoring it as
an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy web application] ******************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************
ok: [dvrg]

TASK [../roles/web_app : Include wipe tasks] ***************************************************************************************************************
included: /mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for dvrg

TASK [../roles/web_app : Stop and remove containers via Docker Compose] ************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove docker-compose file] *******************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Remove application directory] *****************************************************************************************************
skipping: [dvrg]

TASK [../roles/web_app : Log wipe completion] **************************************************************************************************************
skipping: [dvrg]

PLAY RECAP *************************************************************************************************************************************************
dvrg                       : ok=2    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
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
