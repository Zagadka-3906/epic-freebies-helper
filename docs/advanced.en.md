# Development

[简体中文](advanced.md) · [Usage](../README.en.md) · [Maintenance history](maintenance-log.md)

## Execution path

`app/deploy.py` → account parsing → browser context → Epic sign-in → promotion discovery and ownership confirmation → optional notifications.

| Component | Responsibility |
| --- | --- |
| `app/settings.py` | Environment, paths and a single model configuration |
| `app/extensions/deepseek_provider.py` | Official image input, JSON output, deadlines and bounded retries |
| `app/extensions/hcaptcha_adapter.py` | Local drag solvers, normalized coordinate mapping and click bounds |
| `app/extensions/hcaptcha_runtime.py` | Challenge execution deadlines |
| `app/services/browser_context.py` | Camoufox/Firefox startup and proxies |
| `app/extensions/playwright_runtime.py` | Firefox late-frame guard loaded only into Playwright driver subprocesses |
| `app/services/epic_authorization_service.py` | Login, TOTP and store session confirmation |
| `app/services/epic_games_service.py` | Promotion discovery, checkout and ownership verification |
| `app/services/*notification_service.py` | Telegram / WXPush delivery |

## Provider contract

`hcaptcha-challenger==0.19.0` exposes the `ChatProvider` protocol on `Reasoner`, but `AgentV` does not forward a custom provider. Startup replaces only the default provider factory. It does not modify Google SDK clients globally.

The dependency still reads an internal field named `GEMINI_API_KEY`. We fill it with a harmless placeholder and exclude it from serialized configuration. `DeepSeekProvider` reads the real `DEEPSEEK_API_KEY` directly. No Google credential or Google API request is used.

Requests use the official `/chat/completions` endpoint and `deepseek-flash`. JSON mode receives a Pydantic JSON Schema and shape example, and responses undergo strict model validation. Legacy output guessing, field aliases and provider fallbacks have been removed.

Spatial tasks send the raw challenge image and request whole-image normalized coordinates in `0..1000`; mapped page coordinates are checked before clicking. Binary grid classification retains the dependency's row/column format. Do not mix page pixels, grid overlays and normalized image coordinates.

Each model call has at most two attempts, each with a 45-second overall deadline including body reads. Spatial requests use official `thinking={"type":"enabled"}`, `reasoning_effort=low`, and a 4096-token output limit. Recursive challenge retries are disabled; sign-in defaults to three attempts.

## Verification

Repository [AGENTS.md](../AGENTS.md) prohibits test-suite execution. Use static checks, dependency contract inspection and authorized small API preflights:

```bash
uv run black app scripts -C -l 100 --check
uv run ruff check app scripts tests
# Set PYTHONPATH=app first
uv run --frozen python scripts/check_hcaptcha_contract.py
uv run --frozen python scripts/check_deepseek.py
```

API preflight makes a few billed requests. It does not contact Epic or measure challenge success rates. Container builds and actual claims require separate verification.

Dependencies are frozen in `uv.lock`. Before upgrading hCaptcha/Playwright, inspect the provider factory, screenshot APIs and private Firefox driver method. `scripts/install_camoufox.py` pins a compatible browser release; installed Firefox handles fallback.

Append behavioral changes, troubleshooting judgments and user-facing updates to `docs/maintenance-log.md`, recording date, symptoms, root-cause judgment, files and results. Historical entries describe their original implementations; current configuration is defined by the README and source.
