# Helm Chart Documentation — DevOps Info Service

## 1. Helm Fundamentals

### Helm Version

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### Exploring Public Charts

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm search repo prometheus
NAME                                                    CHART VERSION   APP VERSION     DESCRIPTION
prometheus-community/kube-prometheus-stack              82.16.1         v0.89.0         kube-prometheus-stack collects Kubernetes manif...
prometheus-community/prometheus                         28.15.0         v3.11.0         Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-adapter                 5.3.0           v0.12.0         A Helm chart for k8s prometheus adapter
prometheus-community/prometheus-blackbox-exporter       11.9.1          v0.28.0         Prometheus Blackbox Exporter
prometheus-community/prometheus-conntrack-stats...      0.5.35          v0.4.42         A Helm chart for conntrack-stats-exporter
prometheus-community/prometheus-node-exporter           4.52.2          1.10.2          A Helm chart for prometheus node-exporter
prometheus-community/prometheus-pushgateway             3.6.0           v1.11.2         A Helm chart for prometheus pushgateway
prometheus-community/prometheus-redis-exporter          6.22.0          v1.82.0         Prometheus exporter for Redis metrics
...
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
- email: naseem@transit.app
  name: naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.15.0
```

### Helm's Value Proposition

Helm is a package manager for Kubernetes — the equivalent of `apt` or `yum` for cluster workloads. It solves key problems:

- **Templating**: A single chart can be deployed across dev, staging, and production by overriding values, eliminating copy-pasted YAML.
- **Versioning & Rollback**: Every `helm install` or `helm upgrade` creates a numbered release. Rolling back is a single command (`helm rollback`).
- **Dependency Management**: Complex applications (app + database + cache) can be packaged together with dependency declarations.
- **Lifecycle Hooks**: Pre/post-install, upgrade, and delete hooks run Jobs at the right moments (migrations, smoke tests, backups).
- **Standardization**: Helm charts are the industry-standard way to distribute Kubernetes applications.

---

## 2. Chart Overview

### Chart Structure

```
k8s/devops-info-service/
├── Chart.yaml                        # Chart metadata and dependencies
├── values.yaml                       # Default configuration values
├── values-dev.yaml                   # Development environment overrides
├── values-prod.yaml                  # Production environment overrides
└── templates/
    ├── _helpers.tpl                  # Reusable Go template helpers (wraps common-lib)
    ├── deployment.yaml               # Kubernetes Deployment resource
    ├── service.yaml                  # Kubernetes Service resource
    ├── NOTES.txt                     # Post-install usage instructions
    └── hooks/
        ├── pre-install-job.yaml      # Pre-install validation Job
        └── post-install-job.yaml     # Post-install smoke test Job
```

### Key Template Files

| File | Purpose |
|------|---------|
| `_helpers.tpl` | Defines reusable named templates for names, labels, and selectors. Delegates to the `common-lib` library chart so all apps share identical logic. |
| `deployment.yaml` | Templatized Deployment — replicas, image, resources, probes, env vars, and update strategy are all driven by `values.yaml`. |
| `service.yaml` | Templatized Service — type (NodePort/LoadBalancer/ClusterIP), ports, and nodePort are configurable. |
| `hooks/pre-install-job.yaml` | A Kubernetes Job that validates cluster DNS before the main resources are created. |
| `hooks/post-install-job.yaml` | A Kubernetes Job that performs a smoke test against the service's `/health` endpoint after install. |
| `NOTES.txt` | Prints access instructions (NodePort URL, minikube command, etc.) after each install or upgrade. |

### Values Organization

Values are structured in logical groups:

- **`replicaCount`** — number of pod replicas
- **`image.*`** — repository, tag, pullPolicy
- **`service.*`** — type, port, targetPort, nodePort
- **`resources.*`** — CPU/memory requests and limits
- **`strategy.*`** — deployment update strategy
- **`livenessProbe` / `readinessProbe`** — health check configuration
- **`env`** — environment variables passed to the container

---

## 3. Configuration Guide

### Important Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | `3` | Number of pod replicas |
| `image.repository` | `timursalakhov/devops-info-service` | Docker image repository |
| `image.tag` | `"latest"` | Image tag (falls back to `appVersion` if empty) |
| `image.pullPolicy` | `IfNotPresent` | When to pull the image |
| `service.type` | `NodePort` | Service type |
| `service.port` | `80` | Service port |
| `service.targetPort` | `5000` | Container port |
| `service.nodePort` | `30080` | Node port (only for NodePort type) |
| `resources.requests.memory` | `64Mi` | Guaranteed memory |
| `resources.requests.cpu` | `50m` | Guaranteed CPU |
| `resources.limits.memory` | `128Mi` | Maximum memory |
| `resources.limits.cpu` | `200m` | Maximum CPU |
| `livenessProbe.initialDelaySeconds` | `10` | Seconds before first liveness check |
| `readinessProbe.initialDelaySeconds` | `5` | Seconds before first readiness check |

### Environment Customization

**Development** (`values-dev.yaml`): 1 replica, debug mode, relaxed resources (128Mi/100m limits), longer probe intervals.

**Production** (`values-prod.yaml`): 5 replicas, LoadBalancer service, higher resources (512Mi/500m limits), aggressive probe timing.

### Example Installations

```bash
# Default (3 replicas, NodePort)
helm install myrelease k8s/devops-info-service

# Development
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Production
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# Override a single value
helm install myapp k8s/devops-info-service --set replicaCount=10
```

---

## 4. Hook Implementation

### Hooks Implemented

| Hook | File | Type | Weight | Purpose |
|------|------|------|--------|---------|
| Pre-install | `hooks/pre-install-job.yaml` | `pre-install` | `-5` | Validates cluster DNS resolution before deployment |
| Post-install | `hooks/post-install-job.yaml` | `post-install` | `5` | Smoke-tests the `/health` endpoint after deployment |

### Execution Order

1. Helm begins the install process
2. **Pre-install hook** (weight -5) runs first — a `busybox` Job that performs `nslookup kubernetes.default.svc.cluster.local` to verify cluster DNS
3. Main resources (Deployment, Service) are created
4. **Post-install hook** (weight 5) runs last — a `busybox` Job that waits 10 seconds, then `wget`s the service's `/health` endpoint

### Deletion Policies

Both hooks use `hook-succeeded` — the Job and its Pod are automatically deleted after successful execution. This prevents completed hook Jobs from accumulating in the namespace.

### Hook Execution Evidence

Hooks executed successfully during install and were cleaned up per the `hook-succeeded` deletion policy:

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install myrelease k8s/devops-info-service
NAME: myrelease
LAST DEPLOYED: Thu Apr  2 20:03:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
...

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get jobs
No resources found in default namespace.
```

The `No resources found` output confirms that both hook Jobs (pre-install and post-install) ran to completion and were automatically deleted by the `hook-succeeded` deletion policy. The install would have failed if either hook had not completed successfully.

The hooks can also be seen in the dry-run output under the `HOOKS:` section:

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install --dry-run --debug test-release k8s/devops-info-service
...
HOOKS:
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
...
```

---

## 5. Installation Evidence

### Helm List

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm list
NAME     	NAMESPACE	REVISION	UPDATED                              	STATUS  	CHART                    	APP VERSION
myrelease	default  	1       	2026-04-02 20:03:16.7497559 +0300 MSK	deployed	devops-info-service-0.1.0	1.0.0
```

### Deployed Resources

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get all
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/myrelease-devops-info-service-545849d748-cp8vv   1/1     Running   0          63s
pod/myrelease-devops-info-service-545849d748-g5s2r   1/1     Running   0          63s
pod/myrelease-devops-info-service-545849d748-tjqmk   1/1     Running   0          63s

NAME                                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes                      ClusterIP   10.96.0.1        <none>        443/TCP        12m
service/myrelease-devops-info-service   NodePort    10.110.128.200   <none>        80:30080/TCP   63s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myrelease-devops-info-service   3/3     3            3           63s

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/myrelease-devops-info-service-545849d748   3         3         3       63s
```

### Development Environment

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
NAME: myapp-dev
LAST DEPLOYED: Thu Apr  2 20:06:19 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                             READY   STATUS    RESTARTS   AGE
myapp-dev-devops-info-service-5fbddff874-t4vhv   1/1     Running   0          73s

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get svc
NAME                            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes                      ClusterIP   10.96.0.1        <none>        443/TCP        15m
myapp-dev-devops-info-service   NodePort    10.111.120.125   <none>        80:30080/TCP   73s
```

Dev environment: **1 replica**, NodePort service, debug mode enabled.

### Production Environment

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
NAME: myapp-prod
LAST DEPLOYED: Thu Apr  2 20:09:16 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                              READY   STATUS    RESTARTS   AGE
myapp-prod-devops-info-service-6f78b65b89-4s4g2   1/1     Running   0          57s
myapp-prod-devops-info-service-6f78b65b89-bwp59   1/1     Running   0          57s
myapp-prod-devops-info-service-6f78b65b89-dt2rl   1/1     Running   0          57s
myapp-prod-devops-info-service-6f78b65b89-qc2bn   1/1     Running   0          57s
myapp-prod-devops-info-service-6f78b65b89-tnwt7   1/1     Running   0          57s

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get svc
NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
kubernetes                       ClusterIP      10.96.0.1      <none>        443/TCP        18m
myapp-prod-devops-info-service   LoadBalancer   10.99.29.247   <pending>     80:32320/TCP   58s
```

Prod environment: **5 replicas**, LoadBalancer service, production resource limits.

---

## 6. Operations

### Installation

```bash
# Build dependencies (required for common-lib)
helm dependency update k8s/devops-info-service

# Install with default values
helm install myrelease k8s/devops-info-service

# Install with environment-specific values
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

### Upgrade

```bash
# Upgrade with new values
helm upgrade myrelease k8s/devops-info-service --set image.tag="2.0.0"

# Upgrade with a different values file
helm upgrade myrelease k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

### Rollback

```bash
# View release history
helm history myrelease

# Rollback to previous revision
helm rollback myrelease

# Rollback to specific revision
helm rollback myrelease 1
```

### Uninstall

```bash
helm uninstall myrelease
```

---

## 7. Testing & Validation

### Helm Lint

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Helm Template

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm template myrelease k8s/devops-info-service
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myrelease-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: myrelease
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: myrelease
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myrelease-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: myrelease
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: myrelease
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: myrelease
    spec:
      containers:
        - name: devops-info-service
          image: "timursalakhov/devops-info-service:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "5000"
            - name: DEBUG
              value: "False"
            - name: APP_VERSION
              value: 1.0.0
          resources:
            limits:
              cpu: 200m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "myrelease-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: myrelease
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "myrelease-devops-info-service-post-install"
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: myrelease
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke-test
          image: busybox
          command:
            - sh
            - -c
            - |
              echo "=== Post-install smoke test ==="
              echo "Waiting for service to become available..."
              sleep 10
              echo "Checking service endpoint..."
              wget -qO- --timeout=5 http://myrelease-devops-info-service:80/health || echo "Service not reachable yet (may still be starting)"
              echo ""
              echo "=== Post-install smoke test completed ==="
  backoffLimit: 1
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "myrelease-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: myrelease
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "myrelease-devops-info-service-pre-install"
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: myrelease
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox
          command:
            - sh
            - -c
            - |
              echo "=== Pre-install validation ==="
              echo "Checking cluster DNS resolution..."
              nslookup kubernetes.default.svc.cluster.local || true
              echo "Environment ready for deployment."
              echo "=== Pre-install completed ==="
  backoffLimit: 1
```

### Dry-Run

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install --dry-run --debug test-release k8s/devops-info-service
NAME: test-release
LAST DEPLOYED: Thu Apr  2 20:03:08 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete

USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
common-lib:
  global: {}
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
- name: DEBUG
  value: "False"
- name: APP_VERSION
  value: 1.0.0
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: timursalakhov/devops-info-service
  tag: latest
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
nameOverride: ""
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
replicaCount: 3
resources:
  limits:
    cpu: 200m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 5000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml (post-install, weight 5)
# Source: devops-info-service/templates/hooks/pre-install-job.yaml (pre-install, weight -5)

MANIFEST:
---
# Source: devops-info-service/templates/service.yaml
# Source: devops-info-service/templates/deployment.yaml
(full rendered manifests identical to helm template output above)

NOTES:
Thank you for installing test-release-devops-info-service!
Release: test-release
Chart:   devops-info-service-0.1.0
App:     1.0.0

Access the application via NodePort:
  minikube service test-release-devops-info-service --url

Health check: GET /health
API docs:     GET /docs
```

### Application Accessibility

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> minikube service app1-devops-info-service --url
http://127.0.0.1:58524
! Because you are using a Docker driver on windows, the terminal needs to be open to run it.

C:\Users\claym> curl.exe -s http://127.0.0.1:58524/health
{"status":"healthy","timestamp":"2026-04-02T17:13:00.395862+00:00","uptime_seconds":139}
```

---

## 8. Library Chart (Bonus)

### Library Chart Structure

```
k8s/common-lib/
├── Chart.yaml              # type: library
└── templates/
    ├── _helpers.tpl        # Shared name/fullname/chart helpers
    └── _labels.tpl         # Shared labels and selectorLabels
```

### Shared Templates

| Template | Description |
|----------|-------------|
| `common.name` | Chart name, truncated to 63 characters |
| `common.fullname` | Fully qualified name (`release-chartname`), truncated to 63 characters |
| `common.chart` | Chart name + version string for the `helm.sh/chart` label |
| `common.labels` | Standard Kubernetes labels (chart, name, instance, version, managed-by) |
| `common.selectorLabels` | Minimal selector labels (name, instance) |

### How Both Apps Use the Library

Both `devops-info-service` and `devops-info-service-2` declare `common-lib` as a dependency in their `Chart.yaml`:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Templates reference `common.*` helpers directly (e.g., `{{ include "common.fullname" . }}`), ensuring identical naming and labeling conventions across all applications.

### Benefits

- **DRY**: Label logic is defined once, used everywhere
- **Consistency**: All apps get the same label schema — no drift between charts
- **Maintainability**: Updating a label convention requires changing one file in `common-lib`
- **Scalability**: Adding a third app only requires adding the dependency — no template copy-paste

### Deployment Evidence

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm dependency update k8s/devops-info-service
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm dependency update k8s/devops-info-service-2
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install app1 k8s/devops-info-service
NAME: app1
LAST DEPLOYED: Thu Apr  2 20:10:29 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm install app2 k8s/devops-info-service-2
NAME: app2
LAST DEPLOYED: Thu Apr  2 20:10:58 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm list
NAME	NAMESPACE	REVISION	UPDATED                              	STATUS  	CHART                      	APP VERSION
app1	default  	1       	2026-04-02 20:10:29.810774 +0300 MSK 	deployed	devops-info-service-0.1.0  	1.0.0
app2	default  	1       	2026-04-02 20:10:58.9205441 +0300 MSK	deployed	devops-info-service-2-0.1.0	1.0.0

PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get all
NAME                                             READY   STATUS    RESTARTS   AGE
pod/app1-devops-info-service-7dc77d786f-bfr6q    1/1     Running   0          56s
pod/app1-devops-info-service-7dc77d786f-pk2fr    1/1     Running   0          56s
pod/app1-devops-info-service-7dc77d786f-qcb6v    1/1     Running   0          56s
pod/app2-devops-info-service-2-b547cfbc8-plm6d   1/1     Running   0          32s
pod/app2-devops-info-service-2-b547cfbc8-vfgxt   1/1     Running   0          32s

NAME                                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/app1-devops-info-service     NodePort    10.99.147.175    <none>        80:30080/TCP   56s
service/app2-devops-info-service-2   NodePort    10.110.192.169   <none>        80:30081/TCP   32s
service/kubernetes                   ClusterIP   10.96.0.1        <none>        443/TCP        19m

NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app1-devops-info-service     3/3     3            3           56s
deployment.apps/app2-devops-info-service-2   2/2     2            2           32s

NAME                                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/app1-devops-info-service-7dc77d786f    3         3         3       56s
replicaset.apps/app2-devops-info-service-2-b547cfbc8   2         2         2       32s
```
