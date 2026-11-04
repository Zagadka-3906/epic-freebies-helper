# Epic Freebies Helper

[简体中文](README.md) · [Maintenance history](docs/maintenance-log.md) · [Development](docs/advanced.en.md)

A maintained fork of [Ronchy2000/epic-freebies-helper](https://github.com/Ronchy2000/epic-freebies-helper). It uses Playwright/Camoufox to sign in to Epic, find weekly promotions and verify claims. This fork uses the **official DeepSeek API** exclusively.

## Model

The requested model is **DeepSeek-V4.1-Flash-1017**. Its current official API ID is `deepseek-flash`, using `https://api.deepseek.com/chat/completions`; see the [official change log](https://api-docs.deepseek.com/updates/). This alias follows platform updates and is not an immutable 1017 snapshot.

All challenge stages use this model. Spatial requests enable low-effort thinking. Each request has a 45-second deadline and at most two attempts; sign-in defaults to three attempts. Official API usage is billed. A stronger model cannot guarantee that challenges or Epic risk checks will pass.

## GitHub Actions

Add these under **Settings → Secrets and variables → Actions → Secrets**:

| Secret | Purpose |
| --- | --- |
| `EPIC_EMAIL` | Epic email |
| `EPIC_PASSWORD` | Epic password |
| `DEEPSEEK_API_KEY` | Official DeepSeek API key |

Old provider keys and model variables are ignored and can be removed manually from repository settings. Never paste keys into code, logs or issues.

Open **Actions → Epic Awesome Gamer (Scheduled) → Run workflow**:

1. Enable `preflight_only` to verify image input, JSON output, normalized coordinates and browser installation.
2. After preflight succeeds, disable it to run actual collection.
3. Scheduled collection runs Thursdays at 15:20 UTC / 23:20 UTC+8. Enable Actions in your fork; scheduled runs use the default branch.

Preflight sends only simple diagnostic images and does not sign in or claim games. Its success does not prove claim success. Runs on the same branch queue sequentially. The job timeout defaults to 60 minutes; repository Variable `JOB_TIMEOUT_MINUTES` can increase it for multiple accounts.

## Optional Secrets

| Secret | Purpose |
| --- | --- |
| `EPIC_ACCOUNTS` | Multiline `email:password`, overrides the single account; passwords may contain colons |
| `EPIC_TOTP_SECRET` | Authenticator App Base32 secret, not the current six-digit code |
| `BROWSER_PROXY` | HTTP(S)/SOCKS browser proxy URL |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Both enable Telegram result notifications |
| `WXPUSH_ENDPOINT`, `WXPUSH_TOKEN` | Enable self-hosted WXPush notifications; service root or `/wxsend` |
| `WXPUSH_USERID`, `WXPUSH_TEMPLATE_ID`, `WXPUSH_BASE_URL` | Optional recipient, template and details-page URL |

Authenticator TOTP is supported. Email/SMS codes, Passkeys and privacy prompts requiring consent need manual handling. The TOTP configuration is shared across accounts; run accounts with different TOTP secrets separately. Notification delivery failures do not change claim outcomes.

## Local use

Install Python 3.12 and [uv](https://docs.astral.sh/uv/). Copy `.env.example` to `.env` in the repository root and fill in credentials:

```bash
uv sync --frozen
uv run --frozen python scripts/install_camoufox.py
uv run --frozen playwright install firefox
```

Set `PYTHONPATH=app`, then run:

```bash
uv run --frozen python scripts/check_deepseek.py
uv run --frozen app/deploy.py
```

PowerShell: `$env:PYTHONPATH = 'app'`. Linux/macOS: `export PYTHONPATH=app`. Linux also needs browser system dependencies and Xvfb; launch with `xvfb-run -a uv run --frozen app/deploy.py`.

The example environment performs one run. With `ENABLE_APSCHEDULER=true`, the app runs immediately, then every Thursday at 23:20 UTC+8. Avoid running both local and Actions schedules for the same account.

Docker builds this fork's source rather than downloading an upstream image without these changes:

```bash
docker compose -f docker/docker-compose.yaml up -d --build
docker compose -f docker/docker-compose.yaml logs -f
```

It reads the root `.env`, enables weekly scheduling, and persists data under `docker/volumes/`.

## Troubleshooting

- **API preflight fails:** check the official key, balance, model access and network. HTTP 401/402/403/404 are not retried by the provider. HTTP 429/5xx, network timeouts and invalid JSON have at most two attempts.
- **Browser startup fails:** install the pinned Camoufox release; Playwright Firefox is the fallback. Actions uses a fixed Ubuntu release and frozen dependencies.
- **Repeated challenge failures:** inspect screenshots, response times and coordinates. Runner IP reputation, challenge type and page timing also matter. Repeated runs consume API credit.
- **Epic 24-hour limit:** wait at least 24 hours. A clean process exit can indicate an intentional stop; read the workflow summary.
- **Ownership not confirmed:** do not count a checkout click as a successful claim. Inspect Epic's library and logs.

Actions retains logs, screenshots and runtime ZIP files for seven days. ZIP paths are portable; `original-paths.json` maps original names. Artifacts may contain account or session information; review before sharing.

See the [maintenance history](docs/maintenance-log.md) for migration verification and remaining limitations. Licensed under [GPL-3.0](LICENSE), retaining upstream and original-author attribution.
