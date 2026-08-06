# AgentTrace Kubernetes Deployment Specification

This document provides production-ready Kubernetes manifests for deploying AgentTrace services on Kubernetes clusters.

---

## 1. Secrets & ConfigMap Manifest

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agenttrace-secrets
type: Opaque
stringData:
  AGENTTRACE_SECRET_KEY: "k8s-production-vault-secret-key-2026"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: agenttrace-config
data:
  INGESTION_SERVER_URL: "http://agenttrace-ingest:8000"
  AGENTTRACE_PII_ALLOW_LIST: "ALLOW_ME_1,ALLOW_ME_2"
```

---

## 2. Ingestion Service Deployment & Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenttrace-ingest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agenttrace-ingest
  template:
    metadata:
      labels:
        app: agenttrace-ingest
    spec:
      containers:
      - name: ingest
        image: agenttrace/agenttrace:0.1.0
        command: ["uvicorn", "ingest:app", "--host", "0.0.0.0", "--port", "8000"]
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: agenttrace-secrets
        - configMapRef:
            name: agenttrace-config
        readinessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: agenttrace-ingest
spec:
  selector:
    app: agenttrace-ingest
  ports:
  - port: 8000
    targetPort: 8000
```

---

## 3. Gateway Proxy Deployment & Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenttrace-gateway
spec:
  replicas: 5
  selector:
    matchLabels:
      app: agenttrace-gateway
  template:
    metadata:
      labels:
        app: agenttrace-gateway
    spec:
      containers:
      - name: gateway
        image: agenttrace/agenttrace:0.1.0
        command: ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8011"]
        ports:
        - containerPort: 8011
        envFrom:
        - secretRef:
            name: agenttrace-secrets
        - configMapRef:
            name: agenttrace-config
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agenttrace-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agenttrace-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```
