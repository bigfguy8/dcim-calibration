# DCIM Calibration ChatGPT Action scaffold

This folder is a **connector scaffold**, not an installed ChatGPT plugin. The OpenAPI schema exposes read-only project status and logged effort.

## Setup
1. Run `python V10_Termux_Master.py --root ~/dcim_calibration --serve-api` in Termux after setting a long random `V10_API_KEY`. The service listens only on `127.0.0.1` by default.
2. ChatGPT cannot reach a phone's `127.0.0.1` directly. For an Action, deploy/proxy it behind a trusted public HTTPS endpoint or an authenticated HTTPS tunnel; do not expose an unauthenticated server.
3. Replace `https://YOUR_PUBLIC_HTTPS_DOMAIN` in `V10_ChatGPT_Action_OpenAPI.yaml` with that real HTTPS base URL.
4. In the ChatGPT plugin/action setup available to your account, create an API action, paste/import the OpenAPI schema, and configure Bearer API-key authentication with the same `V10_API_KEY`. Test `/health`, `/project/status`, and `/project/time`.
5. This scaffold intentionally has no remote delete, XML-write, camera-control, or Telegram-publish endpoint.

The current ChatGPT integration model and UI vary by account. OpenAI documents Actions as OpenAPI-defined API integrations; this scaffold cannot install itself into ChatGPT.
