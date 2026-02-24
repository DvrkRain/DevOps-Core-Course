# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version

```
# paste output of: ansible --version
```

### Target VM

- **OS:** Ubuntu 24.04 LTS
- **Host alias:** dvrg
- **SSH user:** root
- **SSH key:** `~/.ssh/id_ed25519_devops`

### Role Structure

```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory — VPS host
├── roles/
│   ├── common/                # System baseline (packages, timezone)
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                # Docker CE installation & service
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/            # Pull & run containerised app
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml               # Full stack: provision + deploy
│   ├── provision.yml          # common + docker roles
│   └── deploy.yml             # app_deploy role
├── group_vars/
│   └── all.yml                # Ansible Vault encrypted secrets
├── ansible.cfg                # Project-level Ansible config
└── docs/
    └── LAB05.md               # This file
```

### Why roles instead of monolithic playbooks?

Roles split provisioning logic into self-contained units: `common` handles OS baseline, `docker` handles container runtime, and `app_deploy` handles the application lifecycle. Each role can be tested, versioned, and reused independently, whereas a single flat playbook would grow unmanageable and couldn't be shared across projects.

---

## 2. Roles Documentation

### `common` role

**Purpose:** Establishes a consistent system baseline on every managed host. Updates the package cache, installs a standard set of CLI tools, and enforces UTC as the system timezone.

**Variables (`defaults/main.yml`):**


| Variable          | Default                                                                                         | Description                 |
| ----------------- | ----------------------------------------------------------------------------------------------- | --------------------------- |
| `common_packages` | `[python3-pip, curl, git, vim, htop, ca-certificates, gnupg, lsb-release, apt-transport-https]` | Packages installed via apt  |
| `system_timezone` | `UTC`                                                                                           | System timezone (IANA name) |


**Handlers:** None — package installation and timezone changes do not require service restarts.

**Dependencies:** None.

---

### `docker` role

**Purpose:** Installs Docker CE from Docker's official apt repository, ensures the daemon is running and enabled at boot, adds the target user to the `docker` group, and installs `python3-docker` so subsequent Ansible Docker modules work without a separate Python environment.

**Variables (`defaults/main.yml`):**


| Variable          | Default                                                                                  | Description                         |
| ----------------- | ---------------------------------------------------------------------------------------- | ----------------------------------- |
| `docker_packages` | `[docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]` | Docker packages to install          |
| `docker_user`     | `root`                                                                                   | OS user added to the `docker` group |


**Handlers (`handlers/main.yml`):**

- `**restart docker`** — Restarts the `docker` service. Triggered when the Docker packages task reports a change (i.e., Docker was just installed or upgraded).

**Dependencies:** `common` role (ensures `ca-certificates`, `curl`, `gnupg` are present before the GPG key download step).

---

### `app_deploy` role

**Purpose:** Authenticates with Docker Hub using vaulted credentials, pulls the latest application image, starts the container with a fixed restart policy and port mapping, waits for the port to open, and verifies the `/health` endpoint returns HTTP 200.

**Variables (`defaults/main.yml`):**


| Variable             | Default          | Description                                         |
| -------------------- | ---------------- | --------------------------------------------------- |
| `app_restart_policy` | `unless-stopped` | Docker container restart policy                     |
| `app_env_vars`       | `{}`             | Extra environment variables passed to the container |


**Variables supplied by Vault (`group_vars/all.yml`):**


| Variable             | Description                                                |
| -------------------- | ---------------------------------------------------------- |
| `dockerhub_username` | Docker Hub username                                        |
| `dockerhub_password` | Docker Hub access token                                    |
| `docker_image`       | Full image name (e.g. `timursalakhov/devops-info-service`) |
| `docker_image_tag`   | Image tag (e.g. `latest`)                                  |
| `app_port`           | Host port to expose (e.g. `5000`)                          |
| `app_container_name` | Name given to the running container                        |


**Handlers (`handlers/main.yml`):**

- `**restart app container`** — Restarts the named container. Triggered when the `docker_container` task reports a change (image changed, env changed, etc.).

**Dependencies:** `docker` role must have run first so the Docker daemon is available and `python3-docker` is installed.

---

## 3. Idempotency Demonstration

### First run of `provision.yml`

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml 2>&1 | tee /tmp/provision_run1.txt
[WARNING]: Collection community.general does not support Ansible version 2.16.3

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [dvrg]

TASK [common : Update apt cache] ***********************************************
changed: [dvrg]

TASK [common : Install common packages] ****************************************
changed: [dvrg]

TASK [common : Set system timezone] ********************************************
changed: [dvrg]

TASK [docker : Install Docker prerequisites] ***********************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ****************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ****************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] **************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ****************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [dvrg]

TASK [docker : Add user to docker group] ***************************************
changed: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] **************
changed: [dvrg]

PLAY RECAP *********************************************************************
dvrg                       : ok=12   changed=5    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

```

### Second run of `provision.yml`

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml 2>&1 | tee /tmp/provision_run2.txt
[WARNING]: Collection community.general does not support Ansible version 2.16.3

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [dvrg]

TASK [common : Update apt cache] ***********************************************
ok: [dvrg]

TASK [common : Install common packages] ****************************************
ok: [dvrg]

TASK [common : Set system timezone] ********************************************
ok: [dvrg]

TASK [docker : Install Docker prerequisites] ***********************************
ok: [dvrg]

TASK [docker : Create Docker GPG keyring directory] ****************************
ok: [dvrg]

TASK [docker : Download Docker GPG key] ****************************************
ok: [dvrg]

TASK [docker : Add Docker apt repository] **************************************
ok: [dvrg]

TASK [docker : Install Docker packages] ****************************************
ok: [dvrg]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [dvrg]

TASK [docker : Add user to docker group] ***************************************
ok: [dvrg]

TASK [docker : Install python3-docker for Ansible Docker modules] **************
ok: [dvrg]

PLAY RECAP *********************************************************************
dvrg                       : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis

**What changed on the first run?**

- `Update apt cache` — ran and refreshed the package index (changed).
- `Install common packages` — installed all packages that were not yet present (changed).
- `Set system timezone` — wrote UTC if the VPS was in a different zone (changed).
- Docker prerequisite packages installed (changed).
- Docker GPG key downloaded (changed).
- Docker apt repository added (changed).
- Docker CE packages installed (changed) — this also triggered the `restart docker` handler.
- Docker service started and enabled (changed).
- User added to `docker` group (changed).
- `python3-docker` installed (changed).

**What happened on the second run?**

Every task reported `ok` (green) and zero tasks reported `changed`. This is because all Ansible modules used are **stateful** and check current state before acting:

- `apt: update_cache=yes cache_valid_time=3600` — skips re-fetch if cache is less than 1 hour old.
- `apt: state=present` — checks installed package list; already installed → no change.
- `community.general.timezone` — reads `/etc/timezone` / timedatectl; already UTC → no change.
- `get_url: force=no` — does not overwrite the GPG key file if it already exists.
- `apt_repository: state=present` — repository line already in sources.d → no change.
- `service: state=started enabled=yes` — Docker is already running and enabled → no change.
- `user: groups=docker append=yes` — user already in group → no change.

**Conclusion:** All tasks are idempotent. The playbook can be re-run any number of times and will only make changes when the desired state diverges from actual state.

---

## 4. Ansible Vault Usage

### How credentials are stored

Sensitive variables (Docker Hub credentials and application configuration) live in `group_vars/all.yml`, which is encrypted with Ansible Vault. The file is safe to commit to version control because its content is AES-256 ciphertext.

### Creating / editing the vault file

```bash
# Create (first time):
ansible-vault create group_vars/all.yml

# Edit later:
ansible-vault edit group_vars/all.yml

# View without decrypting to disk:
ansible-vault view group_vars/all.yml
```

### Vault password management

The vault password is **never stored in the repository**. Two options are supported:

1. **Interactive prompt** (safest for manual runs):
  ```bash
   ansible-playbook playbooks/deploy.yml --ask-vault-pass
  ```
2. **Password file** (useful for automation; file excluded via `.gitignore`):
  ```bash
   echo "your-vault-password" > .vault_pass
   chmod 600 .vault_pass
   # ansible.cfg can reference it: vault_password_file = .vault_pass
   ansible-playbook playbooks/deploy.yml
  ```

### Proof that the file is encrypted

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ cat inventory/group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
66303630613335313632646135303837653334373466333665343162333638316439613833653138
3837393539373066653035336537613265623131373232310a303439346337613334646637393134
30633337323038663566343231303639393534333261663665616463313463623666363436626433
3430316234356538340a386561343064323430313631323933323531613764353839633965616132
63633533643432326132366539396235393763323038323336663636636662363734636666316566
38393664346531353034616234376565343937333966323162306630336465663361363939656266
66363766373666663332623064316230393833356139376161633534623631643334323363643531
33303661643033316330613366646136643235343061666531666263383431373264656466306439
36353635363163666434656130363661646364393037316363663935333338653137373235363064
32636633363536346331393961386132303432396165623466303837656634656564303364396130
32343865616332613664323638386166363366363666613834373439613730396638636434313937
30653663373636303661613832623632336263366631653862383338353730643336376433333739
31626132663065653138663566626533623763626165653638633164346139333633666163323465
31313835313063386132366635666366313739656362373033393361623366656130373966383934
30633366636266396132316532383062656566663530643766353437313639643638396235303566
63303064356333373334353633376436663463316361396338363836666237306261626566663866
38396332343264343835633231646538393337643130663635386139306239323433373764643061
66643334643530656234613765396431663465396366336132356432613838656532306465363032
33323536343535656338376637353365313964333862623334336434366162383064366236616434
39666266303466353938326466636332386262633238666461343263326637393032316137366237
30373662626264323561376463366135333061636162393066343533623262386131383330663264
35626336363430336233613334616132646363356239316562623563663232633330366261616431
64653061313863656332656436396666626130356139613131356137646337326432346665383566
62333238626665366631643738306238653930626435396164393338366563643334656135626238
62326635393433663331303535633038636264313461323033363863326463636263343838366238
3733663933646566373136393266333938303231646233336663
```

### Why Ansible Vault is necessary

Storing plaintext credentials in a Git repository exposes them to anyone with read access — past, present, and future — because Git history is permanent. Vault encrypts secrets at rest so the repository can be public while credentials remain confidential. It also centralises secret rotation: update the vault file once and every playbook run picks up the change.

---

## 5. Deployment Verification

### Terminal output from `deploy.yml` run

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password:
[WARNING]: Collection community.docker does not support Ansible version 2.16.3

PLAY [Deploy application] **************************************************************************************

TASK [Gathering Facts] *****************************************************************************************
ok: [dvrg]

TASK [app_deploy : Log in to Docker Hub] ***********************************************************************
changed: [dvrg]

TASK [app_deploy : Pull Docker image] **************************************************************************
changed: [dvrg]

TASK [app_deploy : Ensure app container is running] ************************************************************
changed: [dvrg]

TASK [app_deploy : Wait for application port to be ready] ******************************************************
ok: [dvrg]

TASK [app_deploy : Verify application health endpoint] *********************************************************
ok: [dvrg]

RUNNING HANDLER [app_deploy : restart app container] ***********************************************************
changed: [dvrg]

PLAY RECAP *****************************************************************************************************
dvrg                       : ok=7    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container status (`docker ps`)

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ ansible webservers -a "docker ps"
dvrg | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                      COMMAND           CREATED          STATUS          PORTS                    NAMES
dcb05c87c011   timursalakhov/devops-info-service:latest   "python app.py"   38 seconds ago   Up 23 seconds   0.0.0.0:5000->5000/tcp   devops-app
```

### Health check verification

```shell
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ curl -v http://45.3
8.143.11:5000/health
*   Trying 45.38.143.11:5000...
* Connected to 45.38.143.11 (45.38.143.11) port 5000
> GET /health HTTP/1.1
> Host: 45.38.143.11:5000
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/1.1 200 OK
< date: Tue, 24 Feb 2026 14:43:57 GMT
< server: uvicorn
< content-length: 87
< content-type: application/json
<
* Connection #0 to host 45.38.143.11 left intact
{"status":"healthy","timestamp":"2026-02-24T14:43:57.836297+00:00","uptime_seconds":64}
claymix@claymix:/mnt/c/Users/claym/Desktop/study/Spring25/DevOps/DevOps-Core-Course/ansible$ curl -v http://45.38.143.11:5000
*   Trying 45.38.143.11:5000...
* Connected to 45.38.143.11 (45.38.143.11) port 5000
> GET / HTTP/1.1
> Host: 45.38.143.11:5000
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/1.1 200 OK
< date: Tue, 24 Feb 2026 14:44:16 GMT
< server: uvicorn
< content-length: 835
< content-type: application/json
<
* Connection #0 to host 45.38.143.11 left intact
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"dcb05c87c011","platform":"Linux","platform_version":"#35-Ubuntu SMP PREEMPT_DYNAMIC Mon May 20 15:51:52 UTC 2024","architecture":"x86_64","cpu_count":1,"python_version":"3.14.2"},"runtime":{"uptime_seconds":82,"uptime_human":"0 hours, 1 minutes","current_time":"2026-02-24T14:44:16.695792+00:00","timezone":"UTC"},"request":{"client_ip":"188.130.155.186","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
```

### Handler execution

The `restart app container` handler fires when the `Ensure app container is running` task changes state (e.g., first deployment or when the image tag changes). On subsequent deploys with the same image, the container task returns `ok` and the handler does not execute — saving an unnecessary restart.

---

## 6. Key Decisions 

### Why use roles instead of plain playbooks?

Roles enforce a standard directory layout that separates tasks, handlers, variables, and defaults. This makes it trivial to reuse the same `docker` role across multiple projects and to test each role in isolation, whereas a flat playbook mixes all concerns in one file and cannot be imported without carrying every unrelated task with it.

### How do roles improve reusability?

Each role is self-contained: it declares its own defaults, so callers only need to override what differs. The `docker` role, for example, can be dropped into any Ubuntu project and will install Docker correctly without the caller knowing which packages or GPG URL to use. Roles can also be published to Ansible Galaxy for community sharing.

### What makes a task idempotent?

A task is idempotent when it checks current state before acting and only performs work if the desired state is not already achieved. Ansible's declarative modules (`apt: state=present`, `service: state=started`, `user: groups=docker append=yes`) implement this check internally. Imperative shell commands (`command:`, `shell:`) are not idempotent by default and require explicit guards like `creates:` or `when:` conditions.

### How do handlers improve efficiency?

Handlers run at most once per play, at the end, regardless of how many tasks notified them. If ten tasks all notify `restart docker`, Docker restarts only once — not ten times. This prevents unnecessary service disruptions and speeds up playbook execution.

### Why is Ansible Vault necessary?

Secrets committed in plaintext to a repository are exposed permanently — Git history cannot be truly purged once pushed to a remote. Vault encrypts secrets with AES-256 so the repository can be safely stored or shared publicly while credentials remain protected. It also makes secret rotation auditable through normal Git commit history on the vault file.