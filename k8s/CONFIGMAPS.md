# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation

The application (`app_python/src/app.py`) was extended with a file-based visit counter:

- A **thread-safe counter** reads/writes to `/data/visits` (configurable via `DATA_DIR` env var).
- Each `GET /` request increments the counter and includes the current count in the response.
- A new `GET /visits` endpoint returns the current visit count without incrementing.
- The counter defaults to `0` when the file does not yet exist.

### New Endpoint

| Method | Path     | Description                              |
|--------|----------|------------------------------------------|
| GET    | `/visits` | Returns `{"visits": <count>}` (read-only) |

The root endpoint (`GET /`) now also returns a `"visits"` field in its JSON response.

### Local Testing with Docker

A `docker-compose.yml` was added to `app_python/` that mounts `./data:/data` for persistence:

```bash
cd app_python
docker compose up -d

curl http://localhost:5000/        # visits: 1
curl http://localhost:5000/        # visits: 2
curl http://localhost:5000/visits  # {"visits": 2}

# Restart — counter should persist
docker compose down && docker compose up -d
curl http://localhost:5000/visits  # {"visits": 2}  (preserved)
```
```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> curl.exe http://localhost:5000/      
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"visits":5,"system":{"hostname":"9c430422a111","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":66,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-15T13:13:47.061658+00:00","timezone":"UTC"},"request":{"client_ip":"172.18.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/visits","method":"GET","description":"Visit counter"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> curl.exe http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"visits":6,"system":{"hostname":"9c430422a111","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":67,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-15T13:13:48.268081+00:00","timezone":"UTC"},"request":{"client_ip":"172.18.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/visits","method":"GET","description":"Visit counter"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> curl.exe http://localhost:5000/visits
{"visits":2}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> docker compose down
[+] down 2/2
 ✔ Container app_python-app-python-1 Removed                                                                               0.6s
 ✔ Network app_python_default        Removed                                                                               0.3s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> docker compose up -d
[+] up 2/2
 ✔ Network app_python_default        Created                                                                               0.1s
 ✔ Container app_python-app-python-1 Created                                                                               0.2s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> curl.exe http://localhost:5000/visits      
{"visits":2}
```

---

## 2. ConfigMap Implementation

### ConfigMap Template Structure

Two ConfigMaps are defined in `templates/configmap.yaml`:

1. **File-based ConfigMap** (`<release>-config`) — loads `files/config.json` using `.Files.Get`.
2. **Env-var ConfigMap** (`<release>-env`) — key-value pairs injected as environment variables.

### config.json Content

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "features": {
    "enableMetrics": true,
    "enableDocs": true,
    "logFormat": "json"
  }
}
```

### How ConfigMap Is Mounted as a File

The deployment mounts the `<release>-config` ConfigMap as a volume at `/config`:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: <release>-devops-info-service-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

The file is accessible inside the pod at `/config/config.json`.

### How ConfigMap Provides Environment Variables

The `<release>-env` ConfigMap is injected via `envFrom`:

```yaml
envFrom:
  - configMapRef:
      name: <release>-devops-info-service-env
```

This injects `APP_ENV` and `LOG_LEVEL` as environment variables in the container.

### Verification

```bash
# List ConfigMaps and PVCs
kubectl get configmap,pvc

# Verify config file inside pod
kubectl exec <pod> -- cat /config/config.json

# Verify environment variables
kubectl exec <pod> -- printenv APP_ENV LOG_LEVEL
```

```
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl get configmap,pvc
NAME                                   DATA   AGE
configmap/devops-info-service-config   1      55m
configmap/devops-info-service-env      2      55m
configmap/kube-root-ca.crt             1      78m

NAME                                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-service-data   Bound    pvc-44e48fc6-611d-48ba-9ab9-55bbf19f685e   100Mi      RWO            standard       <unset>                 55m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl get pods                
NAME                                  READY   STATUS    RESTARTS      AGE
devops-info-service-5c956fbb7-q5vhp   1/1     Running   1 (82s ago)   24m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl exec devops-info-service-5c956fbb7-q5vhp -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "features": {
    "enableMetrics": true,
    "enableDocs": true,
    "logFormat": "json"
  }
}

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl exec devops-info-service-5c956fbb7-q5vhp -- printenv APP_ENV LOG_LEVEL
dev
info
```

---

## 3. Persistent Volume

### PVC Configuration

A `PersistentVolumeClaim` is defined in `templates/pvc.yaml`:

```yaml
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

Controlled via `values.yaml`:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""   # uses the cluster default
```

### Access Modes and Storage Class

- **ReadWriteOnce (RWO):** The volume can be mounted as read-write by a single node. This is appropriate for a single-replica deployment writing visit counter data.
- **Storage Class:** Left empty to use the cluster default. On Minikube this is `standard`, which provisions `hostPath` volumes automatically.

### Volume Mount Configuration

The PVC is mounted at `/data` in the deployment:

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-devops-info-service-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

The application writes the visit counter to `/data/visits`.

### Persistence Test

```bash
# 1. Check current visits count
kubectl exec <pod> -- cat /data/visits

# 2. Delete the pod (deployment recreates it)
kubectl delete pod <pod>

# 3. Wait for the new pod and verify the count is preserved
kubectl get pods -w
kubectl exec <new-pod> -- cat /data/visits
```

```
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl get pods
NAME                                  READY   STATUS    RESTARTS        AGE
devops-info-service-5c956fbb7-q5vhp   1/1     Running   1 (4m57s ago)   28m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl exec devops-info-service-5c956fbb7-q5vhp -- cat /data/visits          
4
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl delete pod devops-info-service-5c956fbb7-q5vhp
pod "devops-info-service-5c956fbb7-q5vhp" deleted from default namespace
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl get pods -w
NAME                                  READY   STATUS    RESTARTS   AGE
devops-info-service-5c956fbb7-8k7j5   1/1     Running   0          8s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl exec devops-info-service-5c956fbb7-8k7j5 -- cat /data/visits
4
```

Data survived pod deletion -- the visit count of `4` was preserved across the pod restart via the PersistentVolumeClaim.

---

## 4. ConfigMap vs Secret

| Aspect            | ConfigMap                            | Secret                                      |
|-------------------|--------------------------------------|---------------------------------------------|
| **Purpose**       | Non-sensitive configuration data     | Sensitive data (passwords, tokens, keys)     |
| **Encoding**      | Plain text                           | Base64-encoded (not encrypted by default)    |
| **Size limit**    | 1 MiB                               | 1 MiB                                       |
| **etcd storage**  | Stored in plain text                 | Can be encrypted at rest with EncryptionConfig |
| **RBAC**          | Standard RBAC                        | Should be restricted to least-privilege RBAC  |
| **Usage**         | Mount as files or inject as env vars | Mount as files or inject as env vars          |
| **Examples**      | Feature flags, log levels, config files | DB passwords, API keys, TLS certificates   |

**When to use ConfigMap:**
- Application settings (environment, log level, feature flags)
- Configuration files (JSON, YAML, TOML)
- Any non-sensitive key-value data

**When to use Secret:**
- Database credentials
- API tokens and keys
- TLS certificates and private keys
- Any data that must remain confidential

---

## 5. Bonus — ConfigMap Hot Reload

### Default Update Behavior

When a ConfigMap mounted as a volume is updated (e.g., via `kubectl edit configmap`), the kubelet eventually syncs the change into the pod's mounted directory. The total delay is:

- **kubelet sync period:** ~60 seconds by default
- **ConfigMap cache TTL:** additional delay depending on the API server cache
- **Total:** typically 60–120 seconds before the file reflects the new content

Environment variables injected via `envFrom` are **not** updated — they are set at container startup and remain fixed for the container's lifetime.

### subPath Limitation

When a volume mount uses `subPath` (e.g., `mountPath: /config/config.json, subPath: config.json`), the mounted file is a **copy**, not a symlink. As a result:

- The file does **not** receive automatic updates when the ConfigMap changes.
- Use `subPath` only when you need to mount a single file into a directory without overwriting existing files.
- Avoid `subPath` when you need auto-updates — use a full directory mount instead.

### Chosen Reload Approach: Helm Checksum Annotation

A checksum annotation was added to the pod template in the deployment:

```yaml
metadata:
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

**How it works:**

1. Helm computes a SHA-256 hash of the rendered `configmap.yaml`.
2. The hash is stored as a pod annotation.
3. When `helm upgrade` is run and the ConfigMap content has changed, the hash changes.
4. Kubernetes sees the pod template annotation changed and triggers a rolling restart.

**Testing:**

```bash
# Change config.logLevel in values.yaml from "info" to "debug", then:
helm upgrade devops-info-service . --namespace default

# A new pod rolls out because the checksum annotation changed
kubectl get pods -w
```

### Alternative: Stakater Reloader

[Stakater Reloader](https://github.com/stakater/Reloader) is a Kubernetes controller that watches ConfigMaps and Secrets, automatically triggering rolling restarts when they change — without requiring `helm upgrade`. It is useful for GitOps workflows where ConfigMaps may be updated independently of Helm releases.

The checksum annotation is already active in the deployment:

```
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\app_python> kubectl get deployment devops-info-service -o jsonpath="{.spec.template.metadata.annotations}" | python -m json.tool
{
    "checksum/config": "2704485fbf85d4ffd059e4d4daa68e4d6d8ff5f37a52dbad833ef5efacee24e6"
}
```

Changing `config.logLevel` in `values.yaml` and running `helm upgrade` will produce a new checksum, causing a rolling restart

```diff
- logLevel: "info"
+ logLevel: "debug"
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\k8s\devops-info-service> helm upgrade devops-info-service . --namespace default
Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
LAST DEPLOYED: Wed Apr 15 17:57:33 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service!

Release: devops-info-service
Chart:   devops-info-service-0.1.0
App:     1.0.0

Access the application via NodePort:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services devops-info-service)     
  echo "Visit http://127.0.0.1:$NODE_PORT"

  Or with minikube:
  minikube service devops-info-service --url

Health check: GET /health
API docs:     GET /docs
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\k8s\devops-info-service> kubectl get pods
NAME                                  READY   STATUS        RESTARTS   AGE
devops-info-service-5c956fbb7-8k7j5   1/1     Terminating   0          15m
devops-info-service-7969ff6c-nb886    1/1     Running       0          8s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\k8s\devops-info-service> kubectl get pods
NAME                                 READY   STATUS    RESTARTS   AGE
devops-info-service-7969ff6c-nb886   1/1     Running   0          35s
```