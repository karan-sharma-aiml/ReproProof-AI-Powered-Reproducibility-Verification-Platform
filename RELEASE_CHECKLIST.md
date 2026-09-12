# Release Checklist

## Application

- [x] Backend compiles
- [x] FastAPI starts cleanly
- [x] Existing regression suite passes
- [x] Existing routes remain registered
- [x] Additive routes register without duplicates
- [x] Frontend production build passes

## Demo

- [x] `/demo` route is available
- [x] Demo run requires no API key
- [x] Demo returns score, confidence, workflow, and recommendations
- [x] `/executive` summary route is available
- [x] `/knowledge` and `/performance` routes are available

## Exports

- [x] PDF export path retained
- [x] PPTX export path retained
- [x] Markdown export added
- [x] JSON export added
- [x] CSV scorecard export added

## Operations

- [x] Health and readiness endpoints retained
- [x] Observability metrics retained
- [x] Provider fallback is deterministic
- [x] Deployment manifests remain provider-neutral
- [x] Production secrets are environment-driven

## Remaining operational actions

- [ ] Configure durable stores and external providers
- [ ] Configure production trusted hosts and secrets
- [ ] Add signed artifacts, SBOM, image scanning, and promotion gates
- [ ] Run browser-level visual regression in the target deployment
