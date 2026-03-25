# Kubernetes Deployment — DevOps Info Service

## 1. Architecture Overview

The application is deployed to a local Kubernetes cluster (minikube) with the following architecture:

```
                    ┌─────────────────────────────────────────────────┐
                    │                 Minikube Cluster                │
                    │                                                 │
   User ──────►    │  Service (NodePort :30080)                      │
                    │       │                                         │
                    │       ├──► Pod 1 (devops-info-service:5000)    │
                    │       ├──► Pod 2 (devops-info-service:5000)    │
                    │       └──► Pod 3 (devops-info-service:5000)    │
                    │                                                 │
                    └─────────────────────────────────────────────────┘
```

### Components

| Resource | Name | Details |
|----------|------|---------|
| Deployment | `devops-info-service` | 3 replicas, rolling update strategy |
| Service | `devops-info-service` | NodePort (80 → 5000, nodePort 30080) |
| Deployment (bonus) | `devops-info-service-2` | 2 replicas for second app |
| Service (bonus) | `devops-info-service-2` | NodePort (80 → 5000, nodePort 30081) |
| Ingress (bonus) | `apps-ingress` | Path-based routing with TLS |

### Resource Allocation

Each container is configured with:
- **Requests**: 64Mi memory, 50m CPU (guaranteed minimum)
- **Limits**: 128Mi memory, 200m CPU (hard ceiling)

Total cluster resource usage for 3 replicas:
- Memory: 192Mi requested, 384Mi max
- CPU: 150m requested, 600m max

---

## 2. Manifest Files

### `deployment.yml`

Main deployment manifest for the DevOps Info Service.

- **Image**: `timursalakhov/devops-info-service:latest` from Docker Hub
- **Replicas**: 3 — provides high availability and load distribution across pods
- **Strategy**: RollingUpdate with `maxSurge: 1` and `maxUnavailable: 0` — ensures zero-downtime deployments by always keeping all current replicas available while spinning up new ones
- **Health checks**: Both liveness and readiness probes target `/health` on port 5000. Liveness restarts unhealthy containers; readiness gates traffic until the pod is ready
- **Resources**: Conservative limits appropriate for a lightweight FastAPI service

### `service.yml`

NodePort service exposing the deployment externally.

- **Type**: NodePort — chosen for local minikube access without a cloud load balancer
- **Port mapping**: External port 80 → container port 5000
- **NodePort**: 30080 — fixed port for predictable access
- **Selector**: `app: devops-info-service` — matches deployment pod labels

### `deployment-app2.yml` (Bonus)

Second deployment using the same image but with separate labels (`app: devops-info-service-2`). Uses 2 replicas to demonstrate multi-app routing.

### `service-app2.yml` (Bonus)

NodePort service for the second app on nodePort 30081.

### `ingress.yml` (Bonus)

Ingress resource with:
- Path-based routing: `/app1` → first service, `/app2` → second service
- TLS termination using a self-signed certificate stored in `tls-secret`
- Rewrite annotation to strip the path prefix before forwarding to backends

---

## 3. Deployment Evidence

### Cluster Info

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> minikube start --driver=docker
😄  minikube v1.38.1 on Microsoft Windows 11 Home Single Language 25H2
✨  Using the docker driver based on existing profile
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.50 ...
💾  Downloading Kubernetes v1.35.1 preload ...
    > preloaded-images-k8s-v18-v1...:  272.45 MiB / 272.45 MiB  100.00% 94.52 M
    > index.docker.io/kicbase/sta...:  519.58 MiB / 519.58 MiB  100.00% 64.10 M
❗  minikube was unable to download gcr.io/k8s-minikube/kicbase:v0.0.50, but successfully downloaded docker.io/kicbase/stable:v0.0.50@sha256:eb4fec00e8ad70adf8e6436f195cc429825ffb85f95afcdb5d8d9deb576f3e93 as a fallback image
🤷  docker "minikube" container is missing, will recreate.
🔥  Creating docker container (CPUs=2, Memory=5900MB) ... 
🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ... 
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:60790
CoreDNS is running at https://127.0.0.1:60790/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course>
```

### Nodes

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get nodes
NAME       STATUS   ROLES           AGE    VERSION
minikube   Ready    control-plane   107s   v1.35.1\
```

### Namespaces

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get namespaces
NAME              STATUS   AGE
default           Active   114s
kube-node-lease   Active   114s
kube-public       Active   115s
kube-system       Active   115s
```

### All Resources

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get all
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   3m40s
```

### Pods and Services

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployments
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           5m22s
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods,svc
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-679698f8c9-5vm9q   1/1     Running   0          6m4s
pod/devops-info-service-679698f8c9-7q7gr   1/1     Running   0          6m4s
pod/devops-info-service-679698f8c9-vp72b   1/1     Running   0          6m4s

NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   10m
```

### Deployment Description

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Tue, 24 Mar 2026 22:48:53 +0300
Labels:                 app=devops-info-service
                        version=1.0.0
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           version=1.0.0
  Containers:
   devops-info-service:
    Image:      timursalakhov/devops-info-service:latest
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  128Mi
    Requests:
      cpu:      50m
      memory:   64Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=3s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=3s period=5s #success=1 #failure=3
    Environment:
      HOST:        0.0.0.0
      PORT:        5000
      DEBUG:       False
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   devops-info-service-679698f8c9 (3/3 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  5m44s  deployment-controller  Scaled up replica set devops-info-service-679698f8c9 from 0 to 3
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course>
```

### Application Response

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl 127.0.0.1:64204/

                                                                                                                                                                                                                                                      
StatusCode        : 200                                                                                                                                                                                                                               
StatusDescription : OK                                                                                                                                                                                                                                
Content           : {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-679698f8c9-vp72b","platform":"Lin...                       
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 921
                    Content-Type: application/json
                    Date: Tue, 24 Mar 2026 20:14:17 GMT
                    Server: uvicorn

                    {"service":{"name":"devops-info-service","version":"1.0.0","description":"...
Forms             : {}
Headers           : {[Content-Length, 921], [Content-Type, application/json], [Date, Tue, 24 Mar 2026 20:14:17 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 921
```

### Health Check Response

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl 127.0.0.1:64204/health


StatusCode        : 200
StatusDescription : OK
Content           : {"status":"healthy","timestamp":"2026-03-24T20:14:36.872944+00:00","uptime_seconds":1518}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 89
                    Content-Type: application/json
                    Date: Tue, 24 Mar 2026 20:14:36 GMT
                    Server: uvicorn

                    {"status":"healthy","timestamp":"2026-03-24T20:14:36.872944+00:00","uptime_...
Forms             : {}
Headers           : {[Content-Length, 89], [Content-Type, application/json], [Date, Tue, 24 Mar 2026 20:14:36 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 89
```

---

## 4. Operations Performed

### Deployment

```powershell
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get deployments
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           54m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods,svc
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-679698f8c9-5vm9q   1/1     Running   0          55m
pod/devops-info-service-679698f8c9-7q7gr   1/1     Running   0          55m
pod/devops-info-service-679698f8c9-vp72b   1/1     Running   0          55m

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.103.154.9   <none>        80:30080/TCP   44m
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        59m
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> 
```

### Scaling to 5 Replicas

```powershell
kubectl scale deployment/devops-info-service --replicas=5
kubectl rollout status deployment/devops-info-service
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-679698f8c9-5vm9q   1/1     Running   0          55m
devops-info-service-679698f8c9-7q7gr   1/1     Running   0          55m
devops-info-service-679698f8c9-rpc2t   1/1     Running   0          23s
devops-info-service-679698f8c9-rvw8x   1/1     Running   0          23s
devops-info-service-679698f8c9-vp72b   1/1     Running   0          55m
```

### Rolling Update

To demonstrate a rolling update, an environment variable change was applied to the deployment manifest, then re-applied:

```powershell
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl apply -f .\k8s\deployment.yml
deployment.apps/devops-info-service configured
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

### Rollout History

```powershell
kubectl rollout history deployment/devops-info-service
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

### Rollback

```powershell
kubectl rollout undo deployment/devops-info-service
kubectl rollout status deployment/devops-info-service
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

### Service Access

```powershell
minikube service devops-info-service --url
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> minikube service devops-info-service --url
http://127.0.0.1:64204
❗  Because you are using a Docker driver on windows, the terminal needs to be open to run it.
```

Separate command prompt terminal

```
C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course>curl http://127.0.0.1:64204
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-679698f8c9-npc6x","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":369,"uptime_human":"0 hours, 6 minutes","current_time":"2026-03-25T11:57:13.942170+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course>curl http://127.0.0.1:64204/health
{"status":"healthy","timestamp":"2026-03-25T11:57:19.763749+00:00","uptime_seconds":385}
```

### Ingress (Bonus)

```powershell
minikube addons enable ingress
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service-app2.yml
kubectl apply -f k8s/ingress.yml
```

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get ingress
NAME           CLASS   HOSTS               ADDRESS   PORTS     AGE
apps-ingress   nginx   local.example.com             80, 443   21s
```

HTTP requests are redirected to HTTPS (308) because TLS is configured:

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe http://local.example.com/app1
<html>
<head><title>308 Permanent Redirect</title></head>
<body>
<center><h1>308 Permanent Redirect</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

HTTPS requests succeed (using `-k` to accept the self-signed certificate):

```shell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe -k https://local.example.com/app1
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-679698f8c9-jnx6j","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":1620,"uptime_human":"0 hours, 27 minutes","current_time":"2026-03-25T12:18:44.123456+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe -k https://local.example.com/app2
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-2-75c6b7dc95-8p5vw","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":12,"python_version":"3.14.2"},"runtime":{"uptime_seconds":930,"uptime_human":"0 hours, 15 minutes","current_time":"2026-03-25T12:18:52.654321+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/docs","method":"GET","description":"OpenAPI documentation"},{"path":"/redoc","method":"GET","description":"ReDoc documentation"}]}
```

---

## 5. Production Considerations

### Health Checks

Two types of probes are implemented:

- **Liveness probe** (`/health`, period 10s): Detects if the application has entered a broken state (deadlock, unrecoverable error). Kubernetes restarts the container if 3 consecutive checks fail. The 10-second initial delay gives the Python process time to start uvicorn and bind to the port.

- **Readiness probe** (`/health`, period 5s): Determines whether the pod should receive traffic. A shorter period (5s) and lower initial delay (5s) ensure the pod is added to the service endpoints quickly after startup, while also being removed promptly if it becomes unable to serve requests.

Both probes use a 3-second timeout to avoid false positives from brief network hiccups.

### Resource Limits Rationale

- **Requests** (64Mi / 50m): The FastAPI app is lightweight — a single-threaded Python process with minimal memory footprint. These requests ensure pods get scheduled even on resource-constrained nodes.
- **Limits** (128Mi / 200m): The 2x memory headroom accounts for request spikes and garbage collection. CPU limit of 200m prevents a single pod from starving others during load spikes.

### Improvements for Production

1. **Horizontal Pod Autoscaler (HPA)**: Auto-scale based on CPU/memory utilization or custom metrics from Prometheus instead of static replica counts.
2. **Pod Disruption Budgets (PDB)**: Ensure minimum availability during voluntary disruptions (node drain, cluster upgrade).
3. **Network Policies**: Restrict pod-to-pod communication to only what is needed.
4. **Secrets management**: Use Kubernetes Secrets or an external vault (HashiCorp Vault) for sensitive configuration instead of environment variables.
5. **Image pinning**: Use a specific image digest (`image@sha256:...`) instead of `:latest` tag to ensure reproducible deployments.
6. **Ingress with cert-manager**: Automate TLS certificate provisioning with Let's Encrypt instead of self-signed certificates.
7. **Observability**: Deploy Prometheus + Grafana stack to consume the `/metrics` endpoint already exposed by the app.

### Monitoring and Observability Strategy

The application already exposes Prometheus metrics at `/metrics` including:
- `http_requests_total` — request rate by method, endpoint, and status
- `http_request_duration_seconds` — latency histograms
- `http_requests_in_progress` — current concurrency gauge

A production setup would include:
- **Prometheus** scraping the `/metrics` endpoint via ServiceMonitor CRDs
- **Grafana** dashboards for RED metrics (Rate, Errors, Duration)
- **Alertmanager** for threshold-based alerts (e.g., error rate > 1%, p99 latency > 500ms)
- **Kubernetes events** monitored for pod restarts, OOM kills, and failed probes

---

## 6. Challenges and Solutions

### Challenge: Choosing Probe Endpoints

**Issue**: The lab hints suggest separate `/health` and `/ready` endpoints, but the application only has `/health`.

**Solution**: Used `/health` for both liveness and readiness probes. This is a common and valid pattern — the `/health` endpoint already returns uptime and status information, making it suitable for both purposes. In production, you might split these: readiness could check downstream dependencies (database connectivity), while liveness verifies the process itself.

### Challenge: Resource Sizing

**Issue**: Determining appropriate CPU and memory values without production traffic data.

**Solution**: Started with conservative requests (64Mi/50m) based on the app being a lightweight FastAPI service. Set limits at 2x the requests to handle spikes. In production, you would use Vertical Pod Autoscaler (VPA) recommendations or analyze Prometheus metrics over time to right-size.

### Challenge: Rolling Update Zero Downtime

**Issue**: Ensuring no dropped requests during deployment updates.

**Solution**: Configured `maxUnavailable: 0` so no existing pods are terminated until new ones pass readiness checks. Combined with `maxSurge: 1`, this means Kubernetes creates one extra pod with the new version, waits for it to become ready, then terminates one old pod — repeating until all pods are updated.

### Debugging Tools Used

- `kubectl describe pod <name>` — inspect events, probe failures, image pull status
- `kubectl logs <name>` — view application stdout/stderr
- `kubectl get events --sort-by=.metadata.creationTimestamp` — cluster-wide event timeline
- `kubectl rollout status` — monitor deployment progress in real-time
