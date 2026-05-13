# Lab 15 — StatefulSets & Persistent Storage for the DevOps Info Service

This document covers the Lab 15 implementation: how the existing Helm chart was extended to optionally render a `StatefulSet` with per-pod PVCs and a headless `Service`, while keeping the lab14 `Rollout` available behind a values flag.

---

## 1. StatefulSet Concepts

### 1.1 What StatefulSet Guarantees

A `StatefulSet` is a Kubernetes workload controller designed for **stateful applications**. Unlike `Deployment`, it provides three guarantees that are required when each replica is not interchangeable:

1. **Stable, unique network identifiers.** Pods get an ordinal name (`<sts-name>-0`, `<sts-name>-1`, …) that survives rescheduling. Combined with a headless Service, every pod gets a stable DNS A record `<pod>.<svc>.<ns>.svc.cluster.local`.
2. **Stable, persistent storage.** Each pod gets its **own** `PersistentVolumeClaim` provisioned from a `volumeClaimTemplate`. The PVC name (and therefore the underlying volume) is bound to the pod's ordinal — when pod-N is recreated, it reattaches to the same PVC.
3. **Ordered, graceful deployment and scaling.** With `podManagementPolicy: OrderedReady` (default), pod-N is only created after pod-(N-1) is `Ready`; deletes happen in reverse order. `podManagementPolicy: Parallel` relaxes this when ordering doesn't matter.

### 1.2 StatefulSet vs Deployment

| Feature | `Deployment` | `StatefulSet` |
|---|---|---|
| Pod name | `<name>-<replicaset-hash>-<random>` (e.g. `app-5c956fbb7-q5vhp`) | `<name>-<ordinal>` (e.g. `app-0`, `app-1`, `app-2`) |
| Network identity | Random per pod, churns on every restart | Stable per ordinal, survives rescheduling |
| Storage model | One shared PVC referenced via `persistentVolumeClaim`, or `emptyDir` per pod | One PVC **per pod**, generated from `volumeClaimTemplates` |
| PVC lifecycle | Manually created & deleted | Auto-created on scale-up; **kept** on scale-down (data preservation) |
| Scaling order | Any pod created/deleted in parallel | Ordered (`OrderedReady`) or `Parallel`; deletion is reverse-ordinal |
| Update strategies | `RollingUpdate` (`maxSurge`/`maxUnavailable`), `Recreate` | `RollingUpdate` (with `partition`), `OnDelete` |
| Headless Service required? | No | Yes — `spec.serviceName` must point at one |
| Best fit | Stateless workloads (web frontends, REST APIs without local state) | Databases, message brokers, distributed systems with per-replica state |

**Examples of stateful workloads that should use `StatefulSet`:**

- Databases — MySQL, PostgreSQL, MongoDB, etcd, ZooKeeper.
- Message queues / brokers — Kafka, RabbitMQ, NATS.
- Distributed search / storage — Elasticsearch, Cassandra, Redis Cluster, MinIO.
- Anything where each replica owns local data, has a peer-to-peer identity, or needs a deterministic boot order.

For our `devops-info-service` the per-pod state is the visit counter file at `/data/visits` — when each pod has its own PVC, each pod maintains its own counter, which is exactly the demonstration the lab asks for.

### 1.3 Headless Services & DNS

A regular `ClusterIP` Service load-balances traffic across all backing pods through a single virtual IP — clients never know which pod served them. That breaks the "stable identity" promise.

A **headless Service** is one with `spec.clusterIP: None`. Instead of a single virtual IP, kube-dns publishes one A record per **Ready** endpoint of the Service. When the Service is referenced by a StatefulSet's `serviceName`, kube-dns additionally publishes a per-pod record:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

So with our chart deployed as `devops-info-service` in `default`, you can resolve:

| DNS name | Resolves to |
|---|---|
| `devops-info-service-headless.default.svc.cluster.local` | A records for **all** Ready pods (round-robin via DNS) |
| `devops-info-service-0.devops-info-service-headless.default.svc.cluster.local` | The IP of the pod with ordinal 0, only |
| `devops-info-service-1.devops-info-service-headless.default.svc.cluster.local` | The IP of the pod with ordinal 1, only |
| `devops-info-service-2.devops-info-service-headless.default.svc.cluster.local` | The IP of the pod with ordinal 2, only |

Setting `publishNotReadyAddresses: true` on the headless Service also makes peer DNS work during pod boot (so that, e.g., a database can find its peers before they all become Ready) — useful for clustered software, harmless for our demo.

The original (lab12) `NodePort` Service is **kept**: it round-robins across all three pods and is the way external clients reach the application. The headless Service is purely for in-cluster, per-pod DNS.

---

## 2. Implementation

### 2.1 Chart layout

The lab14 chart is reused as-is. Two new templates are added and gated by `statefulSet.enabled`:

| File | Renders when | Purpose |
|---|---|---|
| [`templates/statefulset.yaml`](devops-info-service/templates/statefulset.yaml) | `statefulSet.enabled: true` | StatefulSet with `volumeClaimTemplates` |
| [`templates/service-headless.yaml`](devops-info-service/templates/service-headless.yaml) | `statefulSet.enabled: true` | Headless Service (`clusterIP: None`) |
| [`templates/rollout.yaml`](devops-info-service/templates/rollout.yaml) | `statefulSet.enabled: false` | lab14 Argo Rollout (kept for reference) |
| [`templates/pvc.yaml`](devops-info-service/templates/pvc.yaml) | `persistence.enabled` and `not statefulSet.enabled` | Single shared PVC for the Rollout path |
| [`templates/service.yaml`](devops-info-service/templates/service.yaml) | always | NodePort Service used for external traffic |
| [`templates/configmap.yaml`](devops-info-service/templates/configmap.yaml) | always | Reused unchanged from lab12 |

The two workloads (Rollout / StatefulSet) are mutually exclusive on a single release, so flipping `statefulSet.enabled` cleanly swaps the chart from one mode to the other.

### 2.2 StatefulSet template highlights

Selected snippets from [`templates/statefulset.yaml`](devops-info-service/templates/statefulset.yaml):

```yaml
spec:
  serviceName: {{ include "common.fullname" . }}-headless
  replicas: {{ .Values.replicaCount }}
  podManagementPolicy: {{ .Values.statefulSet.podManagementPolicy | default "OrderedReady" }}
  updateStrategy:
    type: {{ .Values.statefulSet.updateStrategy.type | default "RollingUpdate" }}
    {{- if eq (.Values.statefulSet.updateStrategy.type | default "RollingUpdate") "RollingUpdate" }}
    rollingUpdate:
      partition: {{ .Values.statefulSet.updateStrategy.partition | default 0 }}
    {{- end }}
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: {{ .Values.persistence.size | default "100Mi" }}
        {{- if .Values.persistence.storageClass }}
        storageClassName: {{ .Values.persistence.storageClass }}
        {{- end }}
```

Key points:

- `serviceName` is the headless Service name. If it doesn't match exactly, kube-dns won't publish the per-pod DNS records.
- The `volumeClaimTemplate` is named `data`. Per-pod PVCs are therefore named `data-<sts-name>-<ordinal>`, e.g. `data-devops-info-service-0`. The matching `volumeMount` in the container uses the same `name: data` and mounts `/data`, which is exactly where the FastAPI app writes `visits` (`VISITS_FILE = /data/visits` in [app_python/src/app.py](../app_python/src/app.py)).
- The container spec (env, envFrom, ConfigMap mount, probes, secret/vault wiring) is copied verbatim from `rollout.yaml`, so the SS and Rollout paths run identical pods.

### 2.3 Headless Service template

[`templates/service-headless.yaml`](devops-info-service/templates/service-headless.yaml):

```yaml
spec:
  clusterIP: None
  publishNotReadyAddresses: true
  selector:
    {{- include "common.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      protocol: TCP
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
```

Same selector as the regular Service — it covers the same pods, but kube-dns treats it differently because of `clusterIP: None`.

### 2.4 Values

Added to [`values.yaml`](devops-info-service/values.yaml):

```yaml
statefulSet:
  enabled: false                # default: keep lab14 Rollout behaviour
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate         # or OnDelete
    partition: 0                # update only pods with ordinal >= partition
```

Overlay [`values-statefulset.yaml`](devops-info-service/values-statefulset.yaml) flips the switch and bumps replicas to 3 so the ordering / DNS / per-pod-storage tests are meaningful:

```yaml
replicaCount: 3
statefulSet:
  enabled: true
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    partition: 0
service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: 30080
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

### 2.5 Deploying

> **Image caveat.** `timursalakhov/devops-info-service:latest` on Docker Hub predates lab12 — it doesn't include the `/visits` endpoint or write to `/data/visits`. On Windows + minikube the cleanest fix is to build the image **inside minikube's Docker daemon** (no registry push required) and pin the chart to that local tag.

```powershell
# 1. Make sure the chart's common-lib dependency is fetched
helm dependency update .\k8s\devops-info-service

# 2. Clean any prior release from labs 12-14 so the Service / labels don't collide
helm uninstall devops-info-service -n default 2>$null
kubectl delete pvc -l app.kubernetes.io/instance=devops-info-service -n default 2>$null

# 3. Build the image inside minikube's Docker daemon from the lab15 source
#    (which includes /visits and /metrics from lab12)
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t timursalakhov/devops-info-service:lab15 -f .\app_python\Dockerfile .\app_python

# 4. Install the StatefulSet variant pinned to the locally-built tag
#    (image.pullPolicy defaults to IfNotPresent, so kubelet uses the local image)
helm upgrade --install devops-info-service .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset.yaml --set image.tag=lab15 -n default

# 5. Wait for ordered startup
kubectl rollout status statefulset/devops-info-service -n default --timeout=180s

# 6. Sanity-check that the deployed image has /visits
kubectl exec devops-info-service-0 -n default -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
```

Alternatively, the same overlay is wired up as an ArgoCD Application in [`k8s/argocd/application-statefulset.yaml`](argocd/application-statefulset.yaml), which deploys to a dedicated `statefulset-demo` namespace.

---

## 3. Resource Verification

```powershell
kubectl get po,sts,svc,pvc -n default -o wide
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get po,sts,svc,pvc -n default -o wide
NAME                        READY   STATUS    RESTARTS   AGE     IP           NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-0   1/1     Running   0          2m31s   10.244.0.5   minikube   <none>           <none>
pod/devops-info-service-1   1/1     Running   0          116s    10.244.0.6   minikube   <none>           <none>
pod/devops-info-service-2   1/1     Running   0          108s    10.244.0.7   minikube   <none>           <none>

NAME                                   READY   AGE     CONTAINERS            IMAGES
statefulset.apps/devops-info-service   3/3     2m31s   devops-info-service   timursalakhov/devops-info-service:latest

NAME                                   TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service            NodePort    10.110.158.167   <none>        80:30080/TCP   2m31s   app.kubernetes.io/instance=devops-info-service,app.kubernetes.io/name=devops-info-service
service/devops-info-service-headless   ClusterIP   None             <none>        80/TCP         2m31s   app.kubernetes.io/instance=devops-info-service,app.kubernetes.io/name=devops-info-service
service/kubernetes                     ClusterIP   10.96.0.1        <none>        443/TCP        29m     <none>

NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/data-devops-info-service-0   Bound    pvc-dfb4d924-ee2e-4fc3-aca4-716959e10b32   100Mi      RWO            standard       <unset>                 2m31s   Filesystem
persistentvolumeclaim/data-devops-info-service-1   Bound    pvc-4168d0c5-d760-4c23-b87a-d925d04034fc   100Mi      RWO            standard       <unset>                 116s    Filesystem
persistentvolumeclaim/data-devops-info-service-2   Bound    pvc-576b3675-25ad-4779-9a02-540e86990656   100Mi      RWO            standard       <unset>                 108s    Filesystem
```

---

## 4. Network Identity (DNS Resolution)

The application's `python:slim` base image doesn't ship `nslookup`, so we resolve names two ways:

1. **From inside an app pod**, using the Python interpreter that's already there.
2. **From a one-shot `busybox` debug pod** for the classic `nslookup` output.

### 4.1 Python resolver inside the app pod

```powershell
# Per-pod A record (single IP, the pod with ordinal 1)
kubectl exec -it devops-info-service-0 -n default -- `
  python -c "import socket; print(socket.gethostbyname_ex('devops-info-service-1.devops-info-service-headless'))"

# Headless Service A records (one IP per Ready pod)
kubectl exec -it devops-info-service-0 -n default -- `
  python -c "import socket; print(socket.gethostbyname_ex('devops-info-service-headless'))"
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec -it devops-info-service-0 -n default -- `
>>   python -c "import socket; print(socket.gethostbyname_ex('devops-info-service-1.devops-info-service-headless'))"
('devops-info-service-1.devops-info-service-headless.default.svc.cluster.local', [], ['10.244.0.6'])
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec -it devops-info-service-0 -n default -- `
>>   python -c "import socket; print(socket.gethostbyname_ex('devops-info-service-headless'))"
('devops-info-service-headless.default.svc.cluster.local', [], ['10.244.0.5', '10.244.0.6', '10.244.0.7'])
```

### 4.2 Classic `nslookup` from a busybox debug pod

```powershell
# One-shot, auto-deletes when done
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -n default -- `
  nslookup devops-info-service-1.devops-info-service-headless.default.svc.cluster.local

kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -n default -- `
  nslookup devops-info-service-headless.default.svc.cluster.local
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -n default -- `
>>   nslookup devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53


Name:   devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.6

pod "dns-test" deleted from default namespace
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -n default -- `
>>   nslookup devops-info-service-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53


Name:   devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.7
Name:   devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.6
Name:   devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.5

pod "dns-test" deleted from default namespace
```

### 4.3 Naming pattern

```
<pod>.<headless-service>.<namespace>.svc.cluster.local
```

so within the `default` namespace any pod can address peers as `devops-info-service-0`, `devops-info-service-1`, `devops-info-service-2` (short form) or fully-qualified.

---

## 5. Per-Pod Storage Isolation

Because every pod has its **own** PVC, each pod maintains its own visit counter at `/data/visits`. We prove this by hitting each pod directly via `port-forward`.

Open three PowerShell windows:

```powershell
# Window 1
kubectl port-forward pod/devops-info-service-0 8080:5000 -n default

# Window 2
kubectl port-forward pod/devops-info-service-1 8081:5000 -n default

# Window 3
kubectl port-forward pod/devops-info-service-2 8082:5000 -n default
```

In a fourth window, generate distinct counts per pod:

```powershell
# Hit pod-0 twice, pod-1 once, leave pod-2 alone
curl.exe http://localhost:8080/  ; curl.exe http://localhost:8080/
curl.exe http://localhost:8081/

# Read the counters back via /visits (read-only, no increment)
curl.exe http://localhost:8080/visits
curl.exe http://localhost:8081/visits
curl.exe http://localhost:8082/visits
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe http://localhost:8080/visits
>> curl.exe http://localhost:8081/visits
>> curl.exe http://localhost:8082/visits
{"visits":2}{"visits":1}{"visits":0}
```

A `Deployment` with a single shared `ReadWriteOnce` PVC could **never** show three different counts — every replica would read/write the same file (and on a multi-node cluster the second replica wouldn't even schedule).

---

## 6. Persistence Test

Delete a pod (without scaling the StatefulSet down) and verify the same PVC is reattached and the counter survives:

```powershell
# Note the count before deletion
kubectl exec devops-info-service-0 -n default -- cat /data/visits

# Delete pod-0 (the StatefulSet recreates it with the same name and reuses the same PVC)
kubectl delete pod devops-info-service-0 -n default

# Wait until pod-0 is back
kubectl wait --for=condition=ready pod/devops-info-service-0 -n default --timeout=120s

# Read the counter from the recreated pod
kubectl exec devops-info-service-0 -n default -- cat /data/visits
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec devops-info-service-0 -n default -- cat /data/visits
2  
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl delete pod devops-info-service-0 -n default
pod "devops-info-service-0" deleted from default namespace
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl wait --for=condition=ready pod/devops-info-service-0 -n default --timeout=120s
pod/devops-info-service-0 condition met
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl exec devops-info-service-0 -n default -- cat /data/visits
2
```

---

## 7. Bonus — Update Strategies

### 7.1 Partitioned RollingUpdate

A `RollingUpdate` strategy with `partition: N` updates **only pods with ordinal >= N**. With three replicas and `partition: 2`, only `devops-info-service-2` is updated; `-0` and `-1` keep the previous image. This is the canonical canary pattern for stateful workloads.

```powershell
helm upgrade --install devops-info-service .\k8s\devops-info-service `
  -f .\k8s\devops-info-service\values-statefulset.yaml `
  --set statefulSet.updateStrategy.partition=2 `
  --set image.tag=2026.02.11-3 -n default

# Watch which pods rotate
kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
  -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm upgrade --install devops-info-service .\k8s\devops-info-service `
>>   -f .\k8s\devops-info-service\values-statefulset.yaml `
>>   --set statefulSet.updateStrategy.partition=2 `
>>   --set image.tag=2026.02.11-3 -n default
Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
LAST DEPLOYED: Thu May  7 23:24:50 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
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
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
>>   -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
devops-info-service-0   timursalakhov/devops-info-service:lab15
devops-info-service-1   timursalakhov/devops-info-service:lab15
devops-info-service-2   timursalakhov/devops-info-service:2026.02.11-3
```

To roll out fully, drop the partition back to 0:

```powershell
helm upgrade devops-info-service .\k8s\devops-info-service `
  -f .\k8s\devops-info-service\values-statefulset.yaml `
  --set statefulSet.updateStrategy.partition=0 `
  --set image.tag=2026.02.11-3 -n default
```

**Use cases:** soak-test a new version on a single replica before promoting cluster-wide; pin a known-stable replica during risky upgrades; gradually update a sharded database one shard at a time.

### 7.2 OnDelete strategy

With `updateStrategy.type: OnDelete`, the controller does **nothing** when the pod template changes. Pods only pick up the new spec when they are deleted (manually or by node failure). This gives operators full control over the timing and order of upgrades.

```powershell
helm upgrade --install devops-info-service .\k8s\devops-info-service `
  -f .\k8s\devops-info-service\values-statefulset.yaml `
  --set statefulSet.updateStrategy.type=OnDelete `
  --set image.tag=latest -n default

# Pods still run the old image - nothing happens automatically
kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
  -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"

# Delete one pod to trigger an upgrade for that ordinal only
kubectl delete pod devops-info-service-2 -n default
kubectl wait --for=condition=ready pod/devops-info-service-2 -n default --timeout=120s

# That single pod now runs the new image
kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
  -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> helm upgrade --install devops-info-service .\k8s\devops-info-service `
>>   -f .\k8s\devops-info-service\values-statefulset.yaml `
>>   --set statefulSet.updateStrategy.type=OnDelete `
>>   --set image.tag=latest -n default
Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
LAST DEPLOYED: Thu May  7 23:25:56 2026
NAMESPACE: default
STATUS: deployed
REVISION: 5
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
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
>>   -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
devops-info-service-0   timursalakhov/devops-info-service:2026.02.11-3
devops-info-service-1   timursalakhov/devops-info-service:2026.02.11-3
devops-info-service-2   timursalakhov/devops-info-service:2026.02.11-3
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl delete pod devops-info-service-2 -n default
pod "devops-info-service-2" deleted from default namespace
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl wait --for=condition=ready pod/devops-info-service-2 -n default --timeout=120s
pod/devops-info-service-2 condition met
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> kubectl get pods -l app.kubernetes.io/instance=devops-info-service -n default `
>>   -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
devops-info-service-0   timursalakhov/devops-info-service:2026.02.11-3
devops-info-service-1   timursalakhov/devops-info-service:2026.02.11-3
devops-info-service-2   timursalakhov/devops-info-service:latest
```

**Use cases:**

- Databases that need application-level coordination (drain, leader handoff, snapshot) before an upgrade.
- Compliance scenarios where the operator must explicitly authorise each replica's restart.
- Long-running workloads where automatic rollouts could violate SLAs.

---

## 8. File Inventory

| File | Purpose |
|---|---|
| [`k8s/devops-info-service/templates/statefulset.yaml`](devops-info-service/templates/statefulset.yaml) | StatefulSet with `volumeClaimTemplates`, `updateStrategy`, `podManagementPolicy` (gated by `statefulSet.enabled`) |
| [`k8s/devops-info-service/templates/service-headless.yaml`](devops-info-service/templates/service-headless.yaml) | Headless Service (`clusterIP: None`) for stable per-pod DNS |
| [`k8s/devops-info-service/templates/rollout.yaml`](devops-info-service/templates/rollout.yaml) | Lab14 Argo Rollout, gated `not statefulSet.enabled` |
| [`k8s/devops-info-service/templates/pvc.yaml`](devops-info-service/templates/pvc.yaml) | Standalone PVC for the Rollout path; skipped when SS path is active |
| [`k8s/devops-info-service/values.yaml`](devops-info-service/values.yaml) | Base values; `statefulSet.enabled: false` by default |
| [`k8s/devops-info-service/values-statefulset.yaml`](devops-info-service/values-statefulset.yaml) | Overlay enabling the StatefulSet path with 3 replicas |
| [`k8s/argocd/application-statefulset.yaml`](argocd/application-statefulset.yaml) | ArgoCD Application deploying the SS overlay to namespace `statefulset-demo` |
