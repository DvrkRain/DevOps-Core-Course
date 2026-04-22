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
NAME                                                READY   STATUS    RESTARTS      AGE
argocd-application-controller-0                     1/1     Running   0             2m4s
argocd-applicationset-controller-58cc5f8cf5-z9gdz   1/1     Running   0             2m6s
argocd-dex-server-7cfd7f696c-j2cnr                  1/1     Running   0             2m6s
argocd-notifications-controller-576878c8f7-xpvqh    1/1     Running   0             2m6s
argocd-redis-75d64694b7-s89wc                       1/1     Running   0             2m6s
argocd-repo-server-c498b5698-4bqbw                  1/1     Running   2 (32s ago)   2m6s
argocd-server-944f8866-wgl7c                        1/1     Running   0             2m6s
```

[argocd pods](screenshots/lab13-argocd-pods.png)

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
- **Password:** `QHZlhzb9Ci7cDjGp`

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

[argocd app list](screenshots/lab13-argocd-login-app-list.png)

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

### Application Access Verification

```powershell
# Get the NodePort URL (default namespace, NodePort service)
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> minikube service devops-info-service --url
http://127.0.0.1:50108
❗  Because you are using a Docker driver on windows, the terminal needs to be open to run it.

# Verify the health endpoint responds
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe http://127.0.0.1:50108/health
{"status":"healthy","timestamp":"2026-04-22T17:18:32.134348+00:00","uptime_seconds":5389}
```

Expected response:
```json
{"status":"healthy","timestamp":"...","uptime_seconds":...}
```

### Testing the GitOps Workflow

To observe ArgoCD detecting drift:

1. Edit `k8s/devops-info-service/values.yaml` — change `replicaCount: 1` to `replicaCount: 2`
2. Commit and push to `lab13` branch
3. In ArgoCD UI, the app will show **OutOfSync** within ~3 minutes (default poll interval)
4. Click **Sync** in the UI or run `argocd app sync devops-info-service`
5. Verify: `kubectl get pods -n default` shows 2 pods

[ArgoCD OutOfSync](screenshots/lab13-argocd-outofsync.png)
[ARgoCD Synced](screenshots/lab13-argocd-synced-healthy.png)

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

[devops-info-service dev and prod synced](screenshots/lab13-argocd-dev-prod-healthy.png)
[kubectl dev and prod pods](screenshots/lab13-kubectl-dev-prod-pods.png)

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

[ArgoCD replicas revert](screenshots/lab13-argocd-replicas-revert.png)

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:46:17
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployment -n dev
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service-dev   1/1     1            1           54m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl scale deployment devops-info-service-dev -n dev --replicas=5
deployment.apps/devops-info-service-dev scaled
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -n dev
NAME                                      READY   STATUS    RESTARTS   AGE
devops-info-service-dev-54fd5c8b8-27wnk   1/1     Running   0          55m
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Running   0          4s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Running   0          4s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Running   0          4s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Running   0          4s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -n dev -w
NAME                                      READY   STATUS    RESTARTS   AGE
devops-info-service-dev-54fd5c8b8-27wnk   1/1     Running   0          55m
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Running   0          5s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Running   0          5s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Running   0          5s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Running   0          5s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Terminating   0          8s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Completed     0          11s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Completed     0          11s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Completed     0          11s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Completed     0          11s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-8b7w4   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-5phpq   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-4k2gc   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Completed     0          12s
devops-info-service-dev-54fd5c8b8-d7nbv   0/1     Completed     0          12s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -n dev
NAME                                      READY   STATUS    RESTARTS   AGE
devops-info-service-dev-54fd5c8b8-27wnk   1/1     Running   0          55m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:46:50
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

[ArgoCD deleted pod revert](screenshots/lab13-argocd-pod-delete-revert.png)

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:53:18
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -n dev
NAME                                      READY   STATUS    RESTARTS   AGE
devops-info-service-dev-54fd5c8b8-75xsz   1/1     Running   0          111s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-service
pod "devops-info-service-dev-54fd5c8b8-75xsz" deleted from dev namespace
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -n dev -w
NAME                                      READY   STATUS    RESTARTS   AGE
devops-info-service-dev-54fd5c8b8-jvshr   0/1     Running   0          5s
devops-info-service-dev-54fd5c8b8-jvshr   1/1     Running   0          23s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:53:55
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

[ArgoCD manually added label](screenshots/lab13-argocd-add-label.png)

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:57:07
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployment -n dev
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service-dev   1/1     1            1           65m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl label deployment devops-info-service-dev -n dev manually-added=true
deployment.apps/devops-info-service-dev labeled
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> argocd app diff devops-info-service-dev
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployment devops-info-service-dev -n dev -o jsonpath='{.metadata.labels}'
{"app.kubernetes.io/instance":"devops-info-service","app.kubernetes.io/version":"1.0.0","helm.sh/chart":"devops-info-service-0,1,0","manually-added":"true"}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
19:58:14
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> Get-Date -Format "HH:mm:ss"
20:01:03
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployment devops-info-service-dev -n dev -o jsonpath='{.metadata.labels}'
{"app.kubernetes.io/instance":"devops-info-service","app.kubernetes.io/version":"1.0.0","helm.sh/chart":"devops-info-service-0.1.0"}
```

> **Note:** `argocd app diff` returned no output immediately after adding the label because
> ArgoCD had not yet run a refresh cycle. After the ~3-minute poll interval, ArgoCD detected
> that the cluster state (extra label `manually-added=true`) diverged from the Git-defined
> Helm-rendered state and re-applied the manifest, removing the manually added label.
> The `lab13-argocd-add-label.png` screenshot shows the drift as seen in the ArgoCD UI diff view.

### Sync Behavior Summary

| Event | Who handles it | Interval |
|-------|---------------|----------|
| Pod crash | Kubernetes (ReplicaSet) | Immediate |
| Replica count changed manually | ArgoCD (selfHeal) | ~3 min (default poll) |
| Resource config drifts from Git | ArgoCD (selfHeal) | ~3 min (default poll) |
| New commit pushed to Git | ArgoCD (automated) | ~3 min or via webhook |

ArgoCD's default Git polling interval is **3 minutes**. Webhooks can reduce this to near-instant.
