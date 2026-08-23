# Repository guidance

- Windows Codex Lead remains the sole final acceptor and main-branch integrator.
- Treat `components/*` as pinned submodules. Modify component source in its own repository, push it, then update the gitlink here.
- Preserve `(job_id, attempt)` idempotency and original-thread ACK evidence.
- Keep the root contract within the intersection accepted by both pinned components.
- Do not enable write mode without compatible component releases and cross-machine verification.
- Never commit real config, credentials, identities, network coordinates, SQLite, dumps, logs, worktrees, artifacts, model files, or binaries.
- Run `python3 scripts/verify_system.py` before committing submodule or compatibility changes.
- Keep third-party dependencies pinned in `dependencies.lock.json`; do not vendor them here.
