# F-027: K8s resource requests, replicas and frontend probes

| Field | Value |
|---|---|
| Severity | Low |
| Category | infrastructure |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Ollama deployment sets limits only, no requests. Backend/frontend single replica without PodDisruptionBudget. Frontend deployment has no probes.

## Evidence

- `k8s/base/ollama/deployment.yaml:25-26`
- `k8s/base/frontend/deployment.yaml`

## Impact

Scheduling surprises; no self-healing for the frontend.

## Suggested fix

Add requests and frontend probes; PDB once replicas > 1 (relevant for GKE, #30).

## Follow-up

- [ ] Ollama requests
- [ ] Frontend probes
