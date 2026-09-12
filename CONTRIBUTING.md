# Contributing

Keep changes additive and bounded-context aligned. Reuse existing ports and services before introducing new abstractions. Preserve API request/response contracts and existing frontend routes.

Before submitting a change:

- Run `python -m compileall -q app` from `backend`.
- Run `python -m pytest tests -q` from `backend`.
- Run `npm run build` from `frontend`.
- Add focused smoke coverage for new behavior.
- Update the relevant implementation report and changelog.
- Do not commit secrets, runtime uploads, reports, backups, or build output.
