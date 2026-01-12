# rag-docs in minikube

## Run Ollama in minikube locally

1.  Create a minikube cluster (recommeded specs for ollama), to have full GPU support from Nvidia,
    it's required to install some additional packages (check [here](https://medium.com/elevate-tech/ollama-with-open-web-ui-and-nvidia-gpu-support-on-rootless-docker-4748b483580a)).

    ```sh
    minikube start --driver=docker --memory=16384 --cpus=8 --gpus=all
    minikube addons enable nvidia-device-plugin
    # It should appear a number >0
    kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" => "}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
    # Add gcloud auth
    minikube addons enable gcp-auth --force --refresh
    ```

2.  Skaffold out with `ollama` profile.

    ```sh
    skaffold dev --profile local,ollama -f skaffold.yaml
    ```

**Note**: It might take a while the first time while it downloads the model.

Alternatively, if it's required to build the containers each time add the `--cache-artifacts=false` tag.

    ```sh
    skaffold dev --profile local --cache-artifacts=false -f skaffold.yaml
    ```
