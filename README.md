# bright-cedar

Submission-ready 404 generation project. The service exposes the standard miner API only: /health, /status, /generate, /results, and task debug endpoints.

The project uses a local split-stack Qwen runtime and static prompt guidance for procedural Three.js reconstruction. Prompt guidance is embedded at build time; there are no runtime profile overlays or lab-only control APIs.
