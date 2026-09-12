# IIT Hackathon Demo Guide

## Demo objective

Show that ReproProof AI converts an uploaded research artifact into an evidence-backed engineering decision, then turns that decision into an explainable report and judge-ready presentation.

## Before the demo

1. Start the backend from `backend` with the project virtual environment.
2. Start the frontend from `frontend` with `npm run dev`.
3. Keep an existing demo ZIP ready, preferably one containing a README, dependency manifest, dataset, and executable entry point.
4. Open `/dashboard` in the browser.

## Seven-minute flow

### 1. Upload evidence

Upload the research ZIP from the home page. Point out that the current upload and verification pipeline is unchanged.

### 2. Show the control plane

Open the dashboard and highlight:

- Repository health
- AI confidence
- Active agent state
- Risk exposure
- Health/confidence trend
- React Flow agent topology
- Existing live execution monitor

### 3. Run verification

Start verification from the existing Command Center. Show live progress and execution events rather than a static result.

### 4. Explain the decision

Use the existing report/troubleshooting surface to show:

- Captured execution evidence
- Root cause analysis
- Patch suggestions
- Verification result
- Confidence and risk signals

### 5. Open the enterprise overview API

For a repository ID, demonstrate:

```text
GET /platform/overview/{repository_id}
```

Show the structured response containing:

- Overall verdict
- Score breakdown
- Workflow nodes
- Decision tree
- Recommendations
- Knowledge graph payload

### 6. Export for judges

Demonstrate:

```text
GET /platform/report/{repository_id}/pdf
GET /platform/report/{repository_id}/pptx
GET /platform/readme/{repository_id}
GET /platform/architecture/{repository_id}
```

Open the generated PDF and PPTX. Mention that the PPTX is a real editable Office presentation, not a renamed text file.

### 7. Close with architecture

Explain the extension model:

- New agents register through the agent registry.
- New providers implement ports for LLM, OCR, embeddings, vector stores, Redis, tracing, and sandbox runtimes.
- Existing APIs do not need to change when new agents are added.
- The judge combines evidence with transparent score explanations.
- Repository execution is sandbox-provider gated.

## Judge-facing narrative

"ReproProof does not ask whether a repository looks convincing. It collects evidence, reconstructs the environment, monitors execution, scores reproducibility and integrity, explains every score, and exports the result in formats a research team and an evaluation panel can actually use."

## Safety line

Call out that missing LLM, OCR, vector, Redis, or sandbox providers produce explicit unavailable states. The platform does not fabricate research conclusions or execute arbitrary repository code directly on the application host.

## Fallback demo

If an external service is unavailable:

- Use the existing deterministic repository analysis.
- Use the local judge overview and generated architecture artifact.
- Show the provider-independent API contracts.
- Use the existing report PDF export.
- Explain that provider-backed novelty/RAG and isolated execution are deployment adapters, not hardcoded demo claims.

## Final checklist

- Backend starts successfully.
- Frontend builds successfully.
- Demo ZIP is available.
- Dashboard opens at `/dashboard`.
- Verification stream is visible.
- Platform overview endpoint is reachable.
- PDF and PPTX downloads are tested.
- No secrets are shown on screen.
- Do not claim novelty or execution results that are not present in the evidence.
