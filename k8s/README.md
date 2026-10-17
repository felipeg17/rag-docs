# rag-docs in minikube

## Run Ollama inside minikube locally

1. Create a minikube cluster (recommended specs for ollama), to have full GPU support from Nvidia,
   it's required to install some additional packages (check [here](https://medium.com/elevate-tech/ollama-with-open-web-ui-and-nvidia-gpu-support-on-rootless-docker-4748b483580a)).

   ```sh
   minikube start --driver=docker --memory=16384 --cpus=8 --gpus=all
   minikube addons enable nvidia-device-plugin
   # It should appear a number >0
   kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" => "}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
   # Add gcloud auth
   minikube addons enable gcp-auth --force --refresh
   ```

**Note:** The `skaffold` commands are intended to run in the root of the repo.

2. Skaffold out with `ollama` profile.

   ```sh
   skaffold dev --profile local,ollama -f skaffold.yaml
   ```

**Note**: It might take a while the first time while it downloads the model.

Alternatively, if it's required to build the containers each time add the `--cache-artifacts=false` tag.

    ```sh
    skaffold dev --profile local --cache-artifacts=false -f skaffold.yaml
    ```

## Run ollama on the host

1. Create a minikube cluster with minimal resources:

   ```sh
   minikube start --driver=docker --memory=4096 --cpus=3
   ```

2. Create secrets:

   ```sh
   kubectl create secret generic api-keys \
   --from-literal=OPENAI_API_KEY=dummy \
   --from-literal=COHERE_API_KEY=dummy \
   -n default
   ```

3. Serve ollama:

   ```sh
   OLLAMA_HOST=0.0.0.0 ollama serve
   ```

4. Skaffold out with `local` profile and the vector db of choice (chroma by default).

   ```sh
   skaffold dev --profile local,chroma --cache-artifacts=false --port-forward -f skaffold.yaml
   ```

**Note:** Forwarding the ports will allow to access the services from the host machine.

## Frontend

The frontend is a static Vite build served by `nginxinc/nginx-unprivileged` (UID 101) on port 8502.
It proxies `/api/v1/*` and `/api/health` to the backend using `API_HOST` and `API_PORT` from
`k8s/base/frontend/configmap.yaml`. nginx reads them at pod start and resolves the host then, so
the backend Service must exist (Skaffold applies all manifests together). A changed value needs a
pod restart (`kubectl rollout restart deploy/rag-docs-frontend`).

With `--port-forward` the app is at http://localhost:8502. Readiness and liveness probes use
`GET /`, which is static and does not depend on the backend.
