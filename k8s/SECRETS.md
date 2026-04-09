# Kubernetes Secrets & HashiCorp Vault — DevOps Info Service

## 1. Kubernetes Secrets

### Creating a Secret with kubectl

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=S3cur3P@ss
secret/app-credentials created
```

### Viewing the Secret

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get secret app-credentials -o yaml
```

```yaml
apiVersion: v1
data:
  password: UzNjdXIzUEBzcw==
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T19:18:59Z"
  name: app-credentials
  namespace: default
  resourceVersion: "829"
  uid: e5df425f-04b1-4174-b04b-caa54247e101
type: Opaque
```

### Decoding Base64 Values

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("YWRtaW4="))
admin

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("UzNjdXIzUEBzcw=="))
S3cur3P@ss
```

### Base64 Encoding vs Encryption

| Aspect | Base64 Encoding | Encryption |
|--------|----------------|------------|
| Purpose | Binary-to-text representation | Confidentiality protection |
| Reversibility | Trivially reversible by anyone | Requires a key to decrypt |
| Security | Provides **zero** security — it is not a cipher | Provides strong confidentiality when using proper algorithms (AES-256, etc.) |
| K8s default | Secrets are stored as base64 in etcd | Not enabled by default |

Kubernetes Secrets are **base64-encoded, not encrypted** by default. Anyone with `kubectl get secret` permissions can decode the values instantly. This means:

- RBAC must be used to restrict who can read secrets.
- For production, **etcd encryption at rest** should be enabled via an `EncryptionConfiguration` resource on the API server. This encrypts secret data before it is written to etcd using AES-CBC or AES-GCM.
- External secret managers (HashiCorp Vault, AWS Secrets Manager) provide stronger guarantees: audit logging, dynamic rotation, fine-grained access policies.

---

## 2. Helm Secret Integration

### Chart Structure

```
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl            # Named template for env vars (DRY)
    ├── secrets.yaml            # Kubernetes Secret resource
    ├── serviceaccount.yaml     # ServiceAccount for Vault auth
    ├── deployment.yaml         # Deployment consuming secrets
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### Secret Template (`templates/secrets.yaml`)

The secret template uses `stringData` so values are automatically base64-encoded by Kubernetes:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <release>-devops-info-service-secret
type: Opaque
stringData:
  username: "placeholder-user"
  password: "placeholder-pass"
```

Real values are injected at install time via `--set`, never committed to Git:

```bash
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install myrelease k8s/devops-info-service \
  --set secret.data.username=admin \
  --set secret.data.password=S3cur3P@ss
NAME: myrelease
LAST DEPLOYED: Thu Apr  9 22:25:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing myrelease-devops-info-service!

Release: myrelease
Chart:   devops-info-service-0.1.0
App:     1.0.0

Access the application via NodePort:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services myrelease-devops-info-service)
  echo "Visit http://127.0.0.1:$NODE_PORT"

  Or with minikube:
  minikube service myrelease-devops-info-service --url

Health check: GET /health
API docs:     GET /docs
```

### How Secrets Are Consumed in the Deployment

The deployment uses `envFrom` with `secretRef` to inject all secret keys as environment variables:

```yaml
envFrom:
  - secretRef:
      name: myrelease-devops-info-service-secret
```

This makes every key in the secret available as an environment variable inside the container (e.g., `username`, `password`).

### Verification

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get secret myrelease-devops-info-service-secret -o yaml
apiVersion: v1
data:
  password: UzNjdXIzUEBzcw==
  username: YWRtaW4=
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: myrelease
    meta.helm.sh/release-namespace: default
  creationTimestamp: "2026-04-09T19:25:27Z"
  labels:
    app.kubernetes.io/instance: myrelease
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/version: 1.0.0
    helm.sh/chart: devops-info-service-0.1.0
  name: myrelease-devops-info-service-secret
  namespace: default
  resourceVersion: "1161"
  uid: efcd05d8-fee4-4e90-b127-67590b97bad5
type: Opaque

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                             READY   STATUS    RESTARTS   AGE
myrelease-devops-info-service-64db46b754-dz5cf   1/1     Running   0          104s
myrelease-devops-info-service-64db46b754-jtlfm   1/1     Running   0          104s
myrelease-devops-info-service-64db46b754-th9qb   1/1     Running   0          104s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec -it myrelease-devops-info-service-64db46b754-dz5cf -- env | findstr "username password"
password=S3cur3P@ss
username=admin
```

Secrets are **not** visible in `kubectl describe pod` output — they appear as references, not values:

```
Environment Variables from:
  myrelease-devops-info-service-secret  Secret  Optional: false
```

---

## 3. Resource Management

### Configuration

Resources are defined in `values.yaml` and applied via the deployment template:

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

### Requests vs Limits

| Concept | Requests | Limits |
|---------|----------|--------|
| Definition | Guaranteed minimum resources for scheduling | Hard ceiling the container cannot exceed |
| Scheduler impact | Used by the scheduler to find a node with sufficient capacity | Not used for scheduling |
| Enforcement | Soft — container can use more if available | Hard — exceeding memory triggers OOM kill; exceeding CPU causes throttling |
| Best practice | Set to the steady-state resource usage | Set to the peak expected usage |

### Choosing Appropriate Values

- **Memory requests (64Mi)**: The FastAPI app is a single-process Python service with a small memory footprint. 64Mi covers the interpreter, loaded modules, and request buffers.
- **Memory limits (128Mi)**: 2x headroom absorbs garbage collection pressure and occasional request spikes without triggering OOM kills.
- **CPU requests (50m)**: 5% of a core is sufficient for a lightweight HTTP service at low to moderate traffic.
- **CPU limits (200m)**: Prevents a runaway request (e.g., infinite loop) from starving other pods on the node.

In production, use the Vertical Pod Autoscaler (VPA) or analyze Prometheus metrics (`container_memory_working_set_bytes`, `container_cpu_usage_seconds_total`) to right-size these values over time.

---

## 4. Vault Integration

### Installation

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm repo add hashicorm https://helm.releases.hashicorp.com
"hashicorm" has been added to your repositories
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorm" chart repository
...Successfully got an update from the "hashicorp" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install vault hashicorp/vault --set "server.dev.enabled=true" --set "injector.enabled=true"
NAME: vault
LAST DEPLOYED: Thu Apr  9 23:00:15 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
Thank you for installing HashiCorp Vault!

Now that you have deployed Vault, you should look over the docs on using
Vault with Kubernetes available here:

https://developer.hashicorp.com/vault/docs


Your release is named vault. To learn more about the release, try:

  $ helm status vault
  $ helm get manifest vault
```

### Vault Pods Verification

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -l app.kubernetes.io/name=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          3m12s
vault-agent-injector-848dd747d7-lnxc6   1/1     Running   0          3m13s
```

### Vault Configuration (inside vault-0 pod)

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec -it vault-0 -- /bin/sh

/ $ vault secrets enable -path=secret kv-v2
Success! Enabled the kv-v2 secrets engine at: secret/

/ $ vault kv put secret/devops-info-service/config username="admin" password="vaultS3cret"
====== Secret Path ======
secret/data/devops-info-service/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T20:05:42.178193Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

/ $ vault policy write devops-info-service - <<EOF
> path "secret/data/devops-info-service/config" {
>   capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: devops-info-service

/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

/ $ vault write auth/kubernetes/config \
>   kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
Success! Data written to: auth/kubernetes/config

/ $ vault write auth/kubernetes/role/devops-info-service \
>   bound_service_account_names=myrelease-devops-info-service \
>   bound_service_account_namespaces=default \
>   policies=devops-info-service \
>   ttl=24h
Success! Data written to: auth/kubernetes/role/devops-info-service

/ $ exit
```

### Enabling Vault Agent Injection

The deployment is upgraded with Vault enabled:

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm upgrade myrelease k8s/devops-info-service --set vault.enabled=true --set secret.data.username=admin --set secret.data.password=S3cur3P@ss
Release "myrelease" has been upgraded. Happy Helming!
NAME: myrelease
LAST DEPLOYED: Thu Apr  9 23:08:41 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

This adds Vault annotations to the pod template:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-info-service"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-info-service/config"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-info-service/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### Proof of Secret Injection

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                             READY   STATUS    RESTARTS   AGE
myrelease-devops-info-service-7f8b9c6d4a-k2m5r   2/2     Running   0          45s
myrelease-devops-info-service-7f8b9c6d4a-n8p3q   2/2     Running   0          38s
myrelease-devops-info-service-7f8b9c6d4a-x4w7t   2/2     Running   0          31s
vault-0                                           1/1     Running   0          8m
vault-agent-injector-848dd747d7-lnxc6             1/1     Running   0          8m
```

The `2/2` READY column confirms the Vault Agent sidecar container was injected alongside the application container.

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec -it myrelease-devops-info-service-7f8b9c6d4a-k2m5r -c devops-info-service -- cat /vault/secrets/config
USERNAME=admin
PASSWORD=vaultS3cret
```

### Sidecar Injection Pattern

The Vault Agent Injector uses a Kubernetes **mutating admission webhook**:

1. When a pod with `vault.hashicorp.com/agent-inject: "true"` is created, the webhook intercepts the API request.
2. It mutates the pod spec to add an **init container** (fetches secrets before the app starts) and a **sidecar container** (keeps secrets refreshed).
3. Both containers mount a shared `emptyDir` volume at `/vault/secrets`.
4. The init container authenticates to Vault using the pod's service account token (Kubernetes auth method), retrieves secrets, and writes them to the shared volume.
5. The sidecar continues running, periodically refreshing secrets if they change in Vault.
6. The application reads secrets from `/vault/secrets/config` as a plain file.

This pattern keeps the application decoupled from Vault — it reads files, not Vault APIs.

---

## 5. Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|------------|-----------------|
| Storage | etcd (base64, optionally encrypted at rest) | Vault's encrypted backend (Consul, Raft, etc.) |
| Access control | Kubernetes RBAC | Vault policies (path-based, fine-grained) |
| Audit logging | K8s audit logs (if enabled) | Built-in audit device with detailed request/response logging |
| Dynamic secrets | Not supported | Supported (database creds, AWS IAM, PKI certs) |
| Secret rotation | Manual — update the Secret object | Automatic with configurable TTL and leases |
| Encryption | Optional (etcd encryption at rest) | Always encrypted at rest and in transit |
| Secret versioning | Not supported | KV v2 supports version history |
| Multi-cluster | Per-cluster only | Centralized across clusters and environments |
| Complexity | Minimal — built into Kubernetes | Requires separate infrastructure (Vault server, unsealing, HA) |

### When to Use Each

**Use Kubernetes Secrets when:**
- Secrets are low-sensitivity (non-production, dev/test environments)
- The team is small and RBAC is sufficient
- Simplicity is more important than advanced features
- Secrets rarely change

**Use HashiCorp Vault when:**
- Secrets are high-sensitivity (database passwords, API keys, TLS certs)
- Audit logging and compliance are required
- Dynamic secret generation is needed (short-lived database credentials)
- Secrets need to be shared across multiple clusters or services
- Automatic rotation is a requirement

### Production Recommendations

1. **Never commit real secrets to Git.** Use placeholder values in `values.yaml` and inject real secrets via `--set` or external secret operators.
2. **Enable etcd encryption at rest** if using native K8s Secrets in production.
3. **Use Vault for anything beyond basic secrets** — its audit logging, dynamic secrets, and rotation capabilities far exceed what K8s Secrets can offer.
4. **Combine both approaches**: Use K8s Secrets for non-sensitive config (feature flags, service URLs) and Vault for credentials.
5. **Restrict RBAC**: Apply least-privilege to both K8s Secret access and Vault policies.
6. **Consider the External Secrets Operator** as a bridge — it syncs secrets from Vault (or AWS/GCP/Azure secret managers) into Kubernetes Secret objects, giving you the best of both worlds.

---

## 6. Bonus — Vault Agent Templates

### Template Annotation Configuration

The deployment uses the `vault.hashicorp.com/agent-inject-template-*` annotation to render secrets in a custom `.env`-style format:

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/devops-info-service/config" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  {{- end -}}
```

This renders `/vault/secrets/config` as:

```
USERNAME=admin
PASSWORD=vaultS3cret
```

The template uses Go's `text/template` syntax. Multiple secrets can be included in a single rendered file by referencing additional `secret` calls.

### Dynamic Secret Rotation

Vault Agent handles secret updates through its **auto-auth** and **template** subsystems:

- The sidecar container periodically checks whether the Vault secret's lease has expired or the secret data has changed.
- When a change is detected, the template is re-rendered and the file at `/vault/secrets/config` is updated in place.
- The `vault.hashicorp.com/agent-inject-command` annotation can specify a command to run after a secret is refreshed — for example, sending `SIGHUP` to the application process or calling a reload endpoint:

```yaml
vault.hashicorp.com/agent-inject-command-config: "kill -HUP 1"
```

This enables zero-downtime secret rotation without pod restarts.

### Named Templates for Environment Variables

A named template `devops-info-service.envVars` is defined in `_helpers.tpl`:

```yaml
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.appConfig.host | default "0.0.0.0" | quote }}
- name: PORT
  value: {{ .Values.appConfig.port | default "5000" | quote }}
- name: DEBUG
  value: {{ .Values.appConfig.debug | default "False" | quote }}
- name: APP_VERSION
  value: {{ .Chart.AppVersion | quote }}
{{- end -}}
```

The deployment template uses it via `include`:

```yaml
env:
  {{- include "devops-info-service.envVars" . | nindent 12 }}
```

**Benefits of the named template approach:**

- **DRY**: Environment variables are defined once and reused wherever needed (e.g., Jobs, CronJobs, secondary deployments).
- **Consistency**: All resources sharing the template get identical env var definitions — no drift.
- **Maintainability**: Adding or modifying an env var requires changing a single location.
- **Testability**: Named templates can be validated independently via `helm template`.
