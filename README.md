# Deploying Prometheus Service Discovery in Kubernetes

This guide explains how to deploy the Prometheus service discovery server in a Kubernetes cluster.

## Prerequisites

- A running Kubernetes cluster
- kubectl configured to access your cluster
- Prometheus running in your cluster

## Deployment

You can deploy all components at once using the provided manifest file:

```bash
kubectl apply -f k8s-manifests.yaml
```

This will create:
- ConfigMaps for both the metrics server and service discovery
- Two metrics server deployments (server1 with value 30, server2 with value 50)
- Service discovery deployment with its service

Alternatively, you can deploy components individually:

```bash
# Deploy first metrics server
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-server-1
  labels:
    app: metrics-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-server
      instance: server1
  template:
    metadata:
      labels:
        app: metrics-server
        instance: server1
    spec:
      containers:
      - name: metrics-server
        image: tiangolo/uvicorn-gunicorn-fastapi:python3.9
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config-volume
          mountPath: /app
        env:
        - name: METRIC_VALUE
          value: "30"
        - name: METRICS_PATH
          value: "/metrics2"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: metrics-server-config
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-server-1
spec:
  selector:
    app: metrics-server
    instance: server1
  ports:
  - port: 9090
    targetPort: 80
EOF
```

3. Deploy the second metrics server:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-server-2
  labels:
    app: metrics-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-server
      instance: server2
  template:
    metadata:
      labels:
        app: metrics-server
        instance: server2
    spec:
      containers:
      - name: metrics-server
        image: tiangolo/uvicorn-gunicorn-fastapi:python3.9
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config-volume
          mountPath: /app
        env:
        - name: METRIC_VALUE
          value: "50"
        - name: METRICS_PATH
          value: "/metrics2"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: metrics-server-config
---
apiVersion: v1
kind: Service
metadata:
  name: metrics-server-2
spec:
  selector:
    app: metrics-server
    instance: server2
  ports:
  - port: 9090
    targetPort: 80
EOF
```

## Deploy Service Discovery


1. Create a ConfigMap for the service discovery script:

```bash
kubectl create configmap promdiscovery-config --from-file=promdiscovery.py
```bash

2. Create the deployment:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: promdiscovery
  labels:
    app: promdiscovery
spec:
  replicas: 1
  selector:
    matchLabels:
      app: promdiscovery
  template:
    metadata:
      labels:
        app: promdiscovery
    spec:
      containers:
      - name: promdiscovery
        image: tiangolo/uvicorn-gunicorn-fastapi:python3.9
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config-volume
          mountPath: /app
        env:
        - name: METRICS_PATH
          value: "/metrics2"
        - name: TARGET_NAMESPACE
          value: "default"
        - name: TARGET_PORT
          value: "9090"
        - name: TARGET_SELECTOR
          value: "app=metrics-server"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: promdiscovery-config
EOF
```

3. Create a service for the discovery server:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: promdiscovery
spec:
  selector:
    app: promdiscovery
  ports:
  - port: 80
    targetPort: 80
EOF
```

4. Update your Prometheus configuration to use the service discovery endpoint:

```yaml
scrape_configs:
  - job_name: 'kubernetes-service-discovery'
    http_sd_configs:
      - url: 'http://promdiscovery.default.svc.cluster.local/targets'
        refresh_interval: 10s
    relabel_configs:
      - source_labels: [__meta_http_sd_label_instance]
        target_label: instance
```

## Verify the Deployment

1. Check if the deployment is running:
```bash
kubectl get deployments promdiscovery
```

2. Check the pods:
```bash
kubectl get pods -l app=promdiscovery
```

3. View the logs:
```bash
kubectl logs -l app=promdiscovery
```

## Configuration

The service discovery server can be configured using the following environment variables:

- `METRICS_PATH`: The path where metrics are exposed (default: "/metrics2")
- `TARGET_NAMESPACE`: The namespace to look for targets (default: "default")
- `TARGET_PORT`: The port where metrics are exposed (default: "9090")
- `TARGET_SELECTOR`: The label selector for finding target pods (default: "app=metrics-server")

You can modify these values in the deployment YAML as needed.

## Cleanup

To remove all deployments:

```bash
kubectl delete deployment promdiscovery metrics-server-1 metrics-server-2
kubectl delete service promdiscovery metrics-server-1 metrics-server-2
kubectl delete configmap promdiscovery-config metrics-server-config
