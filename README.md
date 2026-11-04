# Epic 免费游戏助手

[English](README.en.md) · [维护记录](docs/maintenance-log.md) · [开发说明](docs/advanced.md)

基于 [Ronchy2000/epic-freebies-helper](https://github.com/Ronchy2000/epic-freebies-helper) 的个人维护分支，使用 Playwright/Camoufox 登录 Epic、发现周免并确认领取结果。模型接入统一为 **DeepSeek 官方 API**。

## 模型与配置

使用 **DeepSeek-V4.1-Flash-1017**。按 [DeepSeek 官方更新说明](https://api-docs.deepseek.com/updates/)，当前 API 模型 ID 是 `deepseek-flash`，接口为 `https://api.deepseek.com/chat/completions`。官方别名可能随平台更新，不能把它视为永久固定的 1017 快照。

所有验证码阶段使用同一个模型，不再提供多服务商或单阶段模型切换。API 按官方用量计费；空间任务开启低强度思考，单次请求限时 45 秒，最多请求两次，登录默认最多尝试 3 次。换模型能改善识图能力，但不能保证通过验证码或 Epic 风控。

> 最新验证（2026-11-04）：官方接口预检、Docker 构建和实际验证码挑战均有通过记录，但 Epic 随后拒绝登录验证响应；尚未领取成功。详见[单次运行](https://github.com/Zagadka-3906/epic-freebies-helper/actions/runs/41843219304)及[维护记录](docs/maintenance-log.md)。

## GitHub Actions

在仓库 **Settings → Secrets and variables → Actions → Secrets** 配置：

| Secret | 用途 |
| --- | --- |
| `EPIC_EMAIL` | Epic 邮箱 |
| `EPIC_PASSWORD` | Epic 密码 |
| `DEEPSEEK_API_KEY` | DeepSeek 官方平台 API Key |

旧服务商的密钥和模型变量已不再读取，可以手动从仓库设置中删除。不要在 Issue、日志或代码里填写密钥。

在 **Actions → Epic Awesome Gamer (Scheduled) → Run workflow**：

1. 首次运行勾选 `preflight_only`，确认视觉接口、JSON 输出、归一化坐标和浏览器安装可用。
2. 预检通过后取消勾选，再运行一次实际领取；排障时把 `auth_attempts` 选为 `1`，常规运行默认 `3`。
3. 定时任务每周四 UTC 15:20 / 台北、北京时间 23:20 执行。Fork 后需要在 Actions 页面启用工作流；默认分支上的工作流才参与定时触发。

预检只调用简单诊断图片，不登录 Epic；预检通过不代表领取成功。同一分支的运行串行排队，避免同时登录。多账号可通过仓库 Variable `JOB_TIMEOUT_MINUTES` 增加作业时限，默认 60 分钟。

## 可选配置

| Secret | 用途 |
| --- | --- |
| `EPIC_ACCOUNTS` | 多行 `邮箱:密码`；设置后优先于单账号，密码可包含冒号 |
| `EPIC_TOTP_SECRET` | 验证器 App 的 Base32 密钥，**不是**当前六位验证码 |
| `BROWSER_PROXY` | 可选 HTTP(S)/SOCKS 代理地址 |
| `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID` | 同时设置以启用 Telegram 结果通知 |
| `WXPUSH_ENDPOINT`、`WXPUSH_TOKEN` | 启用自建 WXPush 微信通知，地址指向服务根路径或 `/wxsend` |
| `WXPUSH_USERID`、`WXPUSH_TEMPLATE_ID`、`WXPUSH_BASE_URL` | 可选接收者、模板及详情页地址 |

支持验证器 TOTP，邮箱/短信验证码、Passkey 和需要人工确认的隐私条款仍需手动处理。多账号共用一个 TOTP 配置；不同账号使用不同验证器密钥时，应分开运行。通知发送失败不改变领取结果。

## 本地运行

需要 Python 3.12 和 [uv](https://docs.astral.sh/uv/)。在仓库根目录复制 `.env.example` 为 `.env`，填写账号与官方密钥：

```bash
uv sync --frozen
uv run --frozen python scripts/install_camoufox.py
uv run --frozen playwright install firefox
```

设置 `PYTHONPATH=app`，然后运行：

```bash
uv run --frozen python scripts/check_deepseek.py
uv run --frozen app/deploy.py
```

PowerShell 使用 `$env:PYTHONPATH = 'app'`；Linux/macOS 使用 `export PYTHONPATH=app`。Linux 需安装浏览器系统依赖和 Xvfb，并通过 `xvfb-run -a uv run --frozen app/deploy.py` 启动。

`.env` 默认单次运行；设置 `ENABLE_APSCHEDULER=true` 后先运行一次，再等待每周四 23:20（UTC+8）的本地调度。避免同时开启 Actions 和本地调度。

Docker 从**当前仓库源码构建**，不再拉取不包含本分支改动的上游镜像：

```bash
docker compose -f docker/docker-compose.yaml up -d --build
docker compose -f docker/docker-compose.yaml logs -f
```

同样读取根目录 `.env`，容器启用内部每周调度，运行数据保存在 `docker/volumes/`。

## 失败排查

- **模型预检失败**：先检查官方密钥、账户余额、模型访问和网络。HTTP 401/402/403/404 不在模型请求层重试；429、5xx、网络超时及无效 JSON 最多尝试两次。
- **浏览器启动失败**：优先安装与依赖匹配的 Camoufox 版本，安装失败使用 Playwright Firefox。Actions 使用固定 Ubuntu 和冻结依赖。
- **验证码反复失败**：检查截图、模型响应耗时和返回坐标；云端出口 IP、挑战题型及页面时序也可能导致失败。无需连续重跑消耗额度。
- **Epic 24 小时领取限制**：至少等待 24 小时再试。程序正常退出也可能表示主动停止，查看 Actions 摘要确认。
- **结账后未确认入库**：不能算领取成功。检查日志和 Epic 游戏库，不要仅凭按钮点击判断。

Actions 保存日志、截图及运行 ZIP 共 7 天。ZIP 内用兼容的路径名称，映射表为 `original-paths.json`。下载产物可能包含账号信息和会话数据，分享前先检查。

本次迁移的验证结果与已知限制见[维护记录](docs/maintenance-log.md)。项目遵循 [GPL-3.0](LICENSE)，保留上游及原始作者署名。
