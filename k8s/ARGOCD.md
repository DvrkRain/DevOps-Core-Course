# ArgoCD GitOps Documentation — DevOps Info Service

## 1. ArgoCD Setup

### Installation via Helm

ArgoCD is installed in a dedicated `argocd` namespace using the official Helm chart.

```powershell
# Add the ArgoCD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create the namespace
kubectl create namespace argocd

# Install ArgoCD
helm install argocd argo/argo-cd --namespace argocd

# Wait for the server pod to become ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

### Installation Verification

```powershell
kubectl get pods -n argocd
```

Expected output — all pods should be `Running 1/1`:

```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m
argocd-applicationset-controller-xxxxxxxxx-xxxxx    1/1     Running   0          2m
argocd-dex-server-xxxxxxxxx-xxxxx                   1/1     Running   0          2m
argocd-notifications-controller-xxxxxxxxx-xxxxx     1/1     Running   0          2m
argocd-redis-xxxxxxxxx-xxxxx                        1/1     Running   0          2m
argocd-repo-server-xxxxxxxxx-xxxxx                  1/1     Running   0          2m
argocd-server-xxxxxxxxx-xxxxx                       1/1     Running   0          2m
```

<!-- SCREENSHOT: paste kubectl get pods -n argocd output here -->

### UI Access via Port-Forward

```powershell
# Keep this running in a separate terminal
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

ArgoCD UI is accessible at **https://localhost:8080** (accept the self-signed certificate warning).

### Admin Password Retrieval

On Windows, the base64 decode requires PowerShell:

```powershell
$secret = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secret))
```

Login credentials:
- **Username:** `admin`
- **Password:** output of the command above

### CLI Installation (Windows)

```powershell
# Download the latest ArgoCD CLI binary for Windows
$version = (Invoke-RestMethod "https://api.github.com/repos/argoproj/argo-cd/releases/latest").tag_name
Invoke-WebRequest -Uri "https://github.com/argoproj/argo-cd/releases/download/$version/argocd-windows-amd64.exe" -OutFile "$env:USERPROFILE\argocd.exe"

# Move to a directory in PATH (e.g., C:\Windows\System32 or add to PATH manually)
Move-Item "$env:USERPROFILE\argocd.exe" "C:\Windows\System32\argocd.exe"

# Verify installation
argocd version --client
```

### CLI Login

```powershell
# Port-forward must be running in another terminal
argocd login localhost:8080 --insecure --username admin --password <password-from-above>

# Verify connection
argocd app list
```

<!-- SCREENSHOT: paste argocd app list output here after apps are deployed -->

---

## 2. Application Configuration

### Directory Structure

```
k8s/
├── argocd/
│   ├── application.yaml          # Task 2: Main app (default namespace, manual sync)
│   ├── application-dev.yaml      # Task 3: Dev environment (auto-sync)
│   ├── application-prod.yaml     # Task 3: Prod environment (manual sync)
│   └── application-set.yaml      # Bonus: ApplicationSet for both envs
└── devops-info-service/
    ├── Chart.yaml
    ├── values.yaml               # Base defaults (replicaCount:1, NodePort:30080)
    ├── values-dev.yaml           # Dev overrides (ClusterIP, debug=True, 1 replica)
    └── values-prod.yaml          # Prod overrides (LoadBalancer, 5 replicas)
```

### Main Application Manifest (`application.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/DvrkRain/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info-service
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

**Key fields explained:**

| Field | Value | Purpose |
|-------|-------|---------|
| `repoURL` | GitHub repo URL | Where ArgoCD pulls the Helm chart from |
| `targetRevision` | `lab13` | Git branch ArgoCD watches |
| `path` | `k8s/devops-info-service` | Location of the Helm chart within the repo |
| `destination.server` | `https://kubernetes.default.svc` | In-cluster Kubernetes API |
| `destination.namespace` | `default` | Where resources are deployed |
| `syncPolicy` | no `automated` block | Manual sync required |

### Deploying the Application

```powershell
# Apply the manifest (ArgoCD registers the app but does not sync yet)
kubectl apply -f k8s/argocd/application.yaml

# Perform initial sync via CLI
argocd app sync devops-info-service

# Watch progress
argocd app get devops-info-service

# Verify pods are running
kubectl get pods -n default
```

### Testing the GitOps Workflow

To observe ArgoCD detecting drift:

1. Edit `k8s/devops-info-service/values.yaml` — change `replicaCount: 1` to `replicaCount: 2`
2. Commit and push to `lab13` branch
3. In ArgoCD UI, the app will show **OutOfSync** within ~3 minutes (default poll interval)
4. Click **Sync** in the UI or run `argocd app sync devops-info-service`
5. Verify: `kubectl get pods -n default` shows 2 pods

<!-- SCREENSHOT: ArgoCD UI showing OutOfSync state -->
<!-- SCREENSHOT: ArgoCD UI after Sync showing Synced + Healthy -->

---

## 3. Multi-Environment Deployment

### Namespace Separation

Dev and prod run in isolated Kubernetes namespaces, preventing resource conflicts.

```powershell
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Environment — Auto-Sync (`application-dev.yaml`)

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

**Configuration differences from base (`values-dev.yaml` overrides):**

| Setting | Dev | Base (Default) |
|---------|-----|----------------|
| `replicaCount` | 1 | 1 |
| `service.type` | ClusterIP | NodePort |
| `image.pullPolicy` | IfNotPresent | IfNotPresent |
| `appConfig.debug` | `"True"` | `"False"` |
| `config.environment` | `"dev"` | `"dev"` |
| `config.logLevel` | `"debug"` | `"debug"` |
| `resources.limits.cpu` | `100m` | `200m` |

**Service is ClusterIP in dev** — no NodePort conflict with the main app in `default`. Access via:
```powershell
kubectl port-forward svc/<release>-devops-info-service -n dev 8081:80
```

### Prod Environment — Manual Sync (`application-prod.yaml`)

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
  # No 'automated' block — every deploy requires explicit approval
```

**Configuration differences from base (`values-prod.yaml` overrides):**

| Setting | Prod | Base (Default) |
|---------|------|----------------|
| `replicaCount` | 5 | 1 |
| `service.type` | LoadBalancer | NodePort |
| `image.pullPolicy` | Always | IfNotPresent |
| `appConfig.debug` | `"False"` | `"False"` |
| `config.environment` | `"prod"` | `"dev"` |
| `config.logLevel` | `"info"` | `"debug"` |
| `resources.requests.cpu` | `100m` | `50m` |
| `resources.limits.memory` | `512Mi` | `128Mi` |

### Why Production Uses Manual Sync

| Reason | Explanation |
|--------|-------------|
| **Change review** | Every production deployment gets explicit human approval |
| **Controlled timing** | Deployments happen on schedule, not immediately on push |
| **Compliance** | Audit trail: who approved, when, and why |
| **Rollback planning** | Operators can assess risk and prepare rollback before deploying |
| **Blast radius** | A bad commit doesn't immediately break production |

### Deploying Both Environments

```powershell
# Apply both application manifests
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

# Dev syncs automatically (wait ~30 seconds)
# Prod requires manual sync:
argocd app sync devops-info-service-prod

# Verify both environments
kubectl get pods -n dev
kubectl get pods -n prod
argocd app list
```

<!-- SCREENSHOT: ArgoCD UI showing both devops-info-service-dev and devops-info-service-prod -->
<!-- SCREENSHOT: kubectl get pods -n dev output -->
<!-- SCREENSHOT: kubectl get pods -n prod output -->

---

## 4. Self-Healing Evidence

ArgoCD self-healing and Kubernetes self-healing are distinct mechanisms with different scopes:

| Mechanism | Trigger | Scope | Response |
|-----------|---------|-------|----------|
| **Kubernetes self-healing** | Pod crash / deletion | Pod level | ReplicaSet recreates the pod to match `replicaCount` |
| **ArgoCD self-healing** | Cluster state drifts from Git | Resource level | ArgoCD re-applies Git-defined manifests to the cluster |

### Test 1 — Manual Scaling (ArgoCD Self-Healing)

The `devops-info-service-dev` application has `selfHeal: true`, so any manual change to cluster state is reverted automatically.

**Procedure:**

```powershell
# Step 1: Check current replica count
kubectl get deployment -n dev

# Step 2: Manually scale up (simulating unauthorized change)
# Replace <deployment-name> with actual name from step above
kubectl scale deployment <deployment-name> -n dev --replicas=5

# Step 3: Observe current state immediately
kubectl get pods -n dev

# Step 4: Wait ~1-3 minutes for ArgoCD to detect drift and revert
kubectl get pods -n dev -w
```

**Expected behavior:** ArgoCD detects the `replicaCount` differs from Git (1 replica defined in `values-dev.yaml`) and scales the deployment back to 1.

<!-- EVIDENCE: Paste before/after output here with timestamps -->
```
[TIMESTAMP BEFORE] kubectl get deployment -n dev:
<paste output>

[TIMESTAMP AFTER MANUAL SCALE] kubectl get pods -n dev:
<paste output showing 5 pods>

[TIMESTAMP AFTER ARGOCD REVERTS] kubectl get pods -n dev:
<paste output showing 1 pod restored>
```

### Test 2 — Pod Deletion (Kubernetes Self-Healing)

```powershell
# Find pod name
kubectl get pods -n dev

# Delete a pod
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service

# Watch immediate recreation by Kubernetes ReplicaSet controller
kubectl get pods -n dev -w
```

**Expected behavior:** Kubernetes recreates the pod within seconds. This is NOT ArgoCD — the ReplicaSet controller notices the pod count is below desired and creates a replacement pod immediately.

<!-- EVIDENCE: Paste output here with timestamps -->
```
[TIMESTAMP] kubectl delete pod output:
<paste>

[TIMESTAMP] kubectl get pods -n dev -w showing new pod:
<paste>
```

### Test 3 — Configuration Drift (ArgoCD Self-Healing)

```powershell
# Find deployment name
kubectl get deployment -n dev

# Manually add a label to the deployment (simulating config drift)
kubectl label deployment <deployment-name> -n dev manually-added=true

# Check ArgoCD diff
argocd app diff devops-info-service-dev

# Wait for ArgoCD to revert the change (~1-3 min)
kubectl get deployment <deployment-name> -n dev -o jsonpath='{.metadata.labels}'
```

**Expected behavior:** The manually added label is removed by ArgoCD as it re-applies the Git-defined state.

<!-- EVIDENCE: Paste diff and before/after labels here -->
```
argocd app diff devops-info-service-dev output:
<paste>

Labels before ArgoCD revert:
<paste>

Labels after ArgoCD revert:
<paste>
```

### Sync Behavior Summary

| Event | Who handles it | Interval |
|-------|---------------|----------|
| Pod crash | Kubernetes (ReplicaSet) | Immediate |
| Replica count changed manually | ArgoCD (selfHeal) | ~3 min (default poll) |
| Resource config drifts from Git | ArgoCD (selfHeal) | ~3 min (default poll) |
| New commit pushed to Git | ArgoCD (automated) | ~3 min or via webhook |

ArgoCD's default Git polling interval is **3 minutes**. Webhooks can reduce this to near-instant.

---

## 5. Bonus — ApplicationSet

### Overview

Instead of maintaining three separate Application manifests, an ApplicationSet generates them from a single template using a **List generator**. This is the recommended pattern for multi-environment or multi-tenant deployments.

### Manifest (`application-set.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-info-service-set
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: true
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: false
  template:
    metadata:
      name: 'devops-info-service-{{.env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/DvrkRain/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/devops-info-service
        helm:
          valueFiles:
            - values.yaml
            - '{{.valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{.namespace}}'
      syncPolicy:
        {{- if .autoSync }}
        automated:
          prune: true
          selfHeal: true
        {{- end }}
        syncOptions:
          - CreateNamespace=true
```

### Generator Configuration Explained

| Field | Purpose |
|-------|---------|
| `goTemplate: true` | Enables Go templating for conditional blocks (e.g., `{{- if .autoSync }}`) |
| `generators[].list.elements` | Defines the parameter matrix — one Application per element |
| `{{.env}}` | Injected parameter used in the app name |
| `{{.namespace}}` | Injected parameter used as deployment target namespace |
| `{{.valuesFile}}` | Injected parameter selecting the environment-specific values file |
| `{{- if .autoSync }}` | Conditional block — dev gets `automated` sync, prod does not |

### Deploying the ApplicationSet

```powershell
# Apply (this replaces individual application-dev.yaml and application-prod.yaml)
kubectl apply -f k8s/argocd/application-set.yaml

# Verify two applications were generated
argocd app list

# Check generated apps
argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

<!-- SCREENSHOT: ArgoCD UI showing ApplicationSet-generated applications -->
<!-- SCREENSHOT: argocd app list showing both generated apps -->

### ApplicationSet vs Individual Applications

| Aspect | Individual Applications | ApplicationSet |
|--------|------------------------|----------------|
| **Files to maintain** | One per environment (N files) | Single template |
| **Adding an environment** | Create a new YAML file | Add one list element |
| **Risk of divergence** | Config can drift between app files | Template guarantees consistency |
| **Conditional logic** | Handled per-file | Inline Go template conditionals |
| **Best for** | 1-2 apps, complex per-app config | Many environments, mono-repo, multi-cluster |

### Available Generator Types

| Generator | Use Case |
|-----------|----------|
| **List** | Explicit list of environments (this lab) |
| **Cluster** | Deploy to multiple Kubernetes clusters |
| **Git** | Auto-discover apps from Git directory structure |
| **Matrix** | Combine two generators (e.g., every app × every cluster) |
| **Merge** | Merge outputs of multiple generators |
