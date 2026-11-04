# 本 Fork：硅基流动免费模型配置

当前 GitHub Actions 固定使用 `LLM_PROVIDER=siliconflow`、
`https://api.siliconflow.cn/v1` 和 `Qwen/Qwen3.5-4B`。
旧的 `LLM_PROVIDER=glm` 仓库变量、`GLM_MODEL` 及 GLM Secrets 不再参与工作流。

## 配置

在仓库 Settings → Secrets and variables → Actions → Secrets 配置：

| Secret | 内容 |
| --- | --- |
| `EPIC_EMAIL` | Epic 账号邮箱 |
| `EPIC_PASSWORD` | Epic 账号密码 |
| `SILICONFLOW_API_KEY` | 硅基流动 API Key |
| `EPIC_TOTP_SECRET` | 可选，验证器 App 的 Base32 密钥 |

无需创建 GLM 或 Gemini 密钥。请勿将 API Key 写入源码或聊天。
硅基流动账号是否需要实名认证、免费模型的调用限制，以控制台为准。

硅基流动官方在 [Qwen3.5 上线说明](https://www.siliconflow.cn/news/yg6n19y2g6frnp4koxu8ye48)
中将 4B 多模态模型列为免费使用。核实日期：2026-11-04。
免费状态、限流和模型供应仍由服务商决定，请定期查看
[模型价格](https://www.siliconflow.cn/pricing)。代码不会自动切换到收费模型或 GLM。
当前免费路线只允许 `Qwen/Qwen3.5-4B`，其他模型名及四个模型覆盖项都会被拒绝。

## 运行和排障

进入 Actions → Epic Awesome Gamer (Scheduled) → Run workflow。
可勾选 `preflight_only`，仅检查真实视觉/JSON 接口及浏览器安装，避免排障时反复登录 Epic。
正常领取前同样会先调用一次模型接口检查；接口、密钥或参数错误会在登录前直接报告。
启动日志应显示 `provider=siliconflow`，四条模型路由均为 `Qwen/Qwen3.5-4B`。
视觉理解、坐标题和复杂拖拽仍可能失败；免费模型的实际通过率需要以运行结果为准。

- 401/403：检查密钥和账号权限。
- 429：等待免费模型限流恢复，避免连续手动重跑。
- 超时：单次模型请求默认 45 秒，最多两次请求；验证码整轮仍受 120 秒预算约束。
- `isloggedin=false`：程序会等待商城会话同步，并探测账号会话，不会因第一次读到 false 立即清 Cookies。
- `Epic 24-hour limit`：至少等待 24 小时再运行。

工作流固定使用 Ubuntu 24.04，按 `uv.lock` 安装依赖，并将 Camoufox
固定为与 Python 包 0.4.11 配套的浏览器 135.0.1-beta.24。
Camoufox 下载失败或出现已知配置兼容异常时，自动尝试 Playwright Firefox。

运行调试资料会先打包成 `epic-runtime.zip` 再上传。内部路径会替换冒号等
不兼容字符，并在 `original-paths.json` 中保留原始路径映射。
GitHub 下载的 artifact ZIP 解压后，可能需要再解压其中的 `epic-runtime.zip`。

本地单次运行请复制 `.env.example` 为 `.env`，填写硅基流动密钥，保留四个模型覆盖项为空。
`GLM` / `Gemini` 的旧适配器仅保留为源码兼容入口，当前 Actions 不会调用它们。
