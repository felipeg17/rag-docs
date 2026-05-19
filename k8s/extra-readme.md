# Kubernetes Deployment

Deploy rag-docs to Kubernetes using Skaffold for local development or kubectl for production.

## Prerequisites

- `kubectl` installed and configured
- Kubernetes cluster (local: Minikube, Kind, or Docker Desktop)
- Skaffold (for local development)

## Local Development with Skaffold

### 1. Start Minikube

```bash
# Minimal resources
minikube start --driver=docker --memory=4096 --cpus=3

# With GPU support (for Ollama)
minikube start --driver=docker --memory=16384 --cpus=8 --gpus=all
minikube addons enable nvidia-device-plugin
```

### 2. Create Secrets

```bash
kubectl create secret generic api-keys \
  --from-literal=OPENAI_API_KEY=dummy \
  --from-literal=COHERE_API_KEY=dummy
```

### 3. Run with Skaffold

#### Ollama Inside Minikube (Recommended)

```bash
skaffold dev --profile local,ollama -f skaffold.yaml
```

Skaffold will build images, deploy to Minikube, stream logs, and watch for code changes.

**First run takes longer** while downloading the LLM model.

#### Ollama on Host Machine

Run Ollama locally:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

Then deploy:

```bash
skaffold dev --profile local,chroma --cache-artifacts=false --port-forward -f skaffold.yaml
```

### 4. Access Services

Skaffold automatically port-forwards:

- **Backend**: http://localhost:8106
- **API Docs**: http://localhost:8106/docs
- **Frontend**: http://localhost:8501
- **PostgreSQL**: localhost:5432
- **ChromaDB**: localhost:8000 (if using Chroma)

## Profiles

Combine profiles to customize your setup:

```bash
# LLM providers
--profile ollama         # Ollama (local)
--profile openai         # OpenAI (requires API key)

# Vector databases
--profile chroma         # ChromaDB
--profile pgvector       # PostgreSQL + pgvector

# Environment
--profile local          # Minikube with port-forwarding
--profile remote         # Production-like setup
```

Examples:

```bash
skaffold dev --profile local,ollama              # Ollama LLM + ChromaDB
skaffold dev --profile local,chroma --port-forward
skaffold dev --profile local,pgvector            # PGVector backend
```

## Production Deployment

### 1. Build and Push Images

```bash
docker build -t myregistry/rag-docs-backend:latest backend/
docker build -t myregistry/rag-docs-frontend:latest frontend/

docker push myregistry/rag-docs-backend:latest
docker push myregistry/rag-docs-frontend:latest
```

### 2. Create Namespace and Secrets

```bash
kubectl create namespace rag-docs

kubectl create secret generic api-keys \
  --from-literal=OPENAI_API_KEY=your-key \
  --from-literal=COHERE_API_KEY=your-key \
  -n rag-docs
```

### 3. Apply Manifests

```bash
kubectl apply -f postgres.yaml -n rag-docs
kubectl apply -f chroma.yaml -n rag-docs      # If using ChromaDB
kubectl apply -f backend.yaml -n rag-docs
kubectl apply -f frontend.yaml -n rag-docs

kubectl get pods -n rag-docs
```

### 4. Expose Services

```bash
kubectl expose deployment backend \
  --type=LoadBalancer \
  --port=8106 \
  -n rag-docs

kubectl expose deployment frontend \
  --type=LoadBalancer \
  --port=8501 \
  -n rag-docs

kubectl get services -n rag-docs
```

## File Structure

```
k8s/
├── postgres.yaml        # PostgreSQL database
├── chroma.yaml          # ChromaDB vector database
├── backend.yaml         # Backend deployment
├── frontend.yaml        # Frontend deployment
├── skaffold.yaml        # Skaffold configuration
└── README.md
```

## Scaling

```bash
# Scale backend replicas
kubectl scale deployment backend --replicas=3 -n rag-docs

# Scale frontend
kubectl scale deployment frontend --replicas=2 -n rag-docs
```

## Monitoring

### View Logs

```bash
kubectl logs -f deployment/backend -n rag-docs
kubectl logs -f deployment/frontend -n rag-docs
```

### Port-Forward for Debugging

```bash
kubectl port-forward svc/backend 8106:8106 -n rag-docs
kubectl port-forward svc/postgres 5432:5432 -n rag-docs
```

### Check Resource Usage

```bash
kubectl top pods -n rag-docs
kubectl top nodes
```

## Database Migrations

Run migrations on Kubernetes:

```bash
# Connect to PostgreSQL pod
kubectl exec -it postgres-0 -n rag-docs -- psql -U postgres

# Or create a one-time job for migrations
kubectl apply -f migration-job.yaml -n rag-docs
```

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name> -n rag-docs
```

Check for:
- Insufficient resources (memory, CPU)
- ImagePullBackOff (registry authentication)
- PersistentVolumeClaim pending

### Backend Can't Connect to Database

```bash
kubectl exec -it <backend-pod> -n rag-docs -- \
  psql -h postgres -U postgres -d ragdocs
```

### Skaffold Build Fails

```bash
# Test Docker build directly
docker build -t test-image backend/

# Clean Skaffold cache
skaffold cache prune
```

### Memory/CPU Issues

```bash
kubectl describe node
kubectl top pods -n rag-docs

# Increase Minikube resources
minikube start --memory=8192 --cpus=4
```

## Cleanup

```bash
# Delete Minikube
minikube delete

# Delete Kubernetes namespace
kubectl delete namespace rag-docs

# Stop Skaffold
# Press Ctrl+C in terminal
```

## Resources

- [Skaffold Docs](https://skaffold.dev/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Setup Guide](../docs/SETUP.md)
- [Main README](../README.md)
