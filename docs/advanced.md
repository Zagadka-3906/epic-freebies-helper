# 开发说明

[English](advanced.en.md) · [使用说明](../README.md) · [维护记录](maintenance-log.md)

## 运行路径

`app/deploy.py` → 账号解析 → 浏览器上下文 → Epic 登录 → 周免发现与领取确认 → 可选通知。

| 文件 | 职责 |
| --- | --- |
| `app/settings.py` | 环境变量、路径、单一模型配置 |
| `app/extensions/deepseek_provider.py` | 官方图片输入、JSON 输出、超时和有限重试 |
| `app/extensions/hcaptcha_adapter.py` | 本地拖拽解法、归一化坐标映射及点击边界检查 |
| `app/extensions/hcaptcha_runtime.py` | 挑战任务的时间限制 |
| `app/services/browser_context.py` | Camoufox/Firefox 启动和代理 |
| `app/extensions/playwright_runtime.py` | 仅在 Playwright 驱动子进程加载 Firefox 迟到帧事件保护 |
| `app/services/epic_authorization_service.py` | 登录、TOTP 与商城会话确认 |
| `app/services/epic_games_service.py` | 周免发现、结账及入库验证 |
| `app/services/*notification_service.py` | Telegram / WXPush 通知 |

## 模型接入契约

`hcaptcha-challenger==0.19.0` 的 `Reasoner` 提供 `ChatProvider` 协议，但 `AgentV` 没有传递自定义 provider。启动时仅替换默认 provider 工厂；不修改全局 Google SDK 客户端。

依赖仍读取名为 `GEMINI_API_KEY` 的内部字段。此处填入无敏感信息的占位符，排除配置序列化；实际密钥由 `DeepSeekProvider` 单独读取 `DEEPSEEK_API_KEY`。无需 Google 密钥，也不发送 Google 请求。

请求固定访问官方 `/chat/completions` 和 `deepseek-flash`。使用 `response_format=json_object`，提示中给出 Pydantic JSON Schema 和形状示例，再严格验证响应。没有旧模型的文本猜测、字段别名解包或服务商降级。

点选/拖拽任务上传原始挑战图，要求整图归一化坐标 `0..1000`；映射回页面后检查边界。九宫格分类保留依赖自己的行列坐标。不要把浏览器页面像素、带网格的投影图与整图归一化坐标混用。

模型网络请求最多两次，单次含响应体读取的总期限为 45 秒。空间任务使用官方 `thinking={"type":"enabled"}` 和 `reasoning_effort=low`，输出上限 8192 tokens。挑战层关闭递归重试；登录默认最多 3 次。

## 修改与验证

仓库 [AGENTS.md](../AGENTS.md) 禁止执行测试套件。使用静态检查、依赖协议检查，以及经授权的小规模 API 预检：

```bash
uv run black app scripts -C -l 100 --check
uv run ruff check app scripts tests
# 先设置 PYTHONPATH=app
uv run --frozen python scripts/check_hcaptcha_contract.py
uv run --frozen python scripts/check_deepseek.py
```

API 预检会产生少量计费请求；不连接 Epic，不证明验证码通过率。Docker 构建与真实领取需要分别验证，不得从静态检查推断成功。

依赖使用 `uv.lock` 冻结。升级 hCaptcha/Playwright 时，检查 provider 工厂、截图接口和 Firefox 私有驱动方法是否变化。Camoufox 下载由 `scripts/install_camoufox.py` 固定到兼容版本；失败后使用已安装的 Firefox。

影响行为、故障判断或用户说明的修改，必须追加到 `docs/maintenance-log.md`，包含日期、症状、根因判断、文件与结果。旧维护记录描述当时的实现，当前配置以 README 和源码为准。
