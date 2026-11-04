# -*- coding: utf-8 -*-
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

from dotenv import load_dotenv
from hcaptcha_challenger.agent import AgentConfig
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import SettingsConfigDict

from extensions.hcaptcha_adapter import apply_hcaptcha_drag_patch
from extensions.deepseek_provider import MODEL, install_deepseek_provider

# TOTP and notification services read os.environ; share the root dotenv with them.
# Existing process/Actions credentials take precedence over local file values.
load_dotenv(Path(".env"), override=False)

# --- 核心路径定义 ---
PROJECT_ROOT = Path(__file__).parent
VOLUMES_DIR = PROJECT_ROOT.joinpath("volumes")
LOG_DIR = VOLUMES_DIR.joinpath("logs")
USER_DATA_DIR = VOLUMES_DIR.joinpath("user_data")
RUNTIME_DIR = VOLUMES_DIR.joinpath("runtime")
SCREENSHOTS_DIR = VOLUMES_DIR.joinpath("screenshots")
RECORD_DIR = VOLUMES_DIR.joinpath("record")
HCAPTCHA_DIR = VOLUMES_DIR.joinpath("hcaptcha")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


# === 配置类定义 ===
class EpicSettings(AgentConfig):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    DEEPSEEK_API_KEY: SecretStr | None = Field(default=None)
    DEEPSEEK_REQUEST_TIMEOUT_SECONDS: float = Field(default=45.0, ge=10.0, le=50.0)

    # Internal AgentConfig compatibility slot, not a Gemini credential or provider.
    GEMINI_API_KEY: SecretStr = Field(default="deepseek-provider", exclude=True, repr=False)

    BROWSER_BACKEND: str = Field(
        default="auto", description="Supported values: auto, camoufox, playwright"
    )
    BROWSER_PROXY: SecretStr | None = Field(
        default=None, description="Optional HTTP(S) or SOCKS proxy URL shared by browser backends."
    )

    EPIC_ACCOUNTS: SecretStr | None = Field(
        default=None, description="Optional multiline email:password account list"
    )
    EPIC_EMAIL: str = Field(default_factory=lambda: _env("EPIC_EMAIL", ""))
    EPIC_PASSWORD: SecretStr = Field(default_factory=lambda: _env("EPIC_PASSWORD", ""))
    DISABLE_BEZIER_TRAJECTORY: bool = Field(default=False)
    RETRY_ON_FAILURE: bool = Field(
        default=False,
        description="Disable hcaptcha-challenger recursive retries; callers own retry limits.",
    )
    WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS: int = Field(default=3000)

    CHALLENGE_CLASSIFIER_MODEL: str = Field(default="")
    IMAGE_CLASSIFIER_MODEL: str = Field(default="")
    SPATIAL_POINT_REASONER_MODEL: str = Field(default="")
    SPATIAL_PATH_REASONER_MODEL: str = Field(default="")

    cache_dir: Path = HCAPTCHA_DIR.joinpath(".cache")
    challenge_dir: Path = HCAPTCHA_DIR.joinpath(".challenge")
    captcha_response_dir: Path = HCAPTCHA_DIR.joinpath(".captcha")

    ENABLE_APSCHEDULER: bool = Field(default=True)
    AUTH_MAX_ATTEMPTS: int = Field(default=3, ge=1, le=8)

    @model_validator(mode="before")
    @classmethod
    def _set_internal_provider_slot(cls, raw_data):
        data = dict(raw_data) if isinstance(raw_data, dict) else {}
        # Ignore obsolete Gemini environment variables. AgentV still reads this field
        # when constructing tools, but our provider obtains the actual DeepSeek key directly.
        data["GEMINI_API_KEY"] = "deepseek-provider"
        for name in (
            "CHALLENGE_CLASSIFIER_MODEL",
            "IMAGE_CLASSIFIER_MODEL",
            "SPATIAL_POINT_REASONER_MODEL",
            "SPATIAL_PATH_REASONER_MODEL",
        ):
            data[name] = MODEL
        return data

    @model_validator(mode="after")
    def _apply_runtime_defaults(self):
        self.BROWSER_BACKEND = self.BROWSER_BACKEND.strip().lower() or "auto"
        if self.BROWSER_BACKEND not in {"auto", "camoufox", "playwright"}:
            raise ValueError("BROWSER_BACKEND must be auto, camoufox or playwright")
        self.EPIC_EMAIL = self.EPIC_EMAIL.strip()
        return self

    @property
    def user_data_dir(self) -> Path:
        target_ = self.user_data_dir_for("camoufox")
        return target_

    def user_data_dir_for(self, backend: str) -> Path:
        backend = (backend or "camoufox").strip().lower()
        suffix = f".{backend}"
        target_ = USER_DATA_DIR.joinpath(f"{self.EPIC_EMAIL}{suffix}")
        target_.mkdir(parents=True, exist_ok=True)
        return target_

    @property
    def llm_configuration_error(self) -> str | None:
        if self.DEEPSEEK_API_KEY is None or not self.DEEPSEEK_API_KEY.get_secret_value().strip():
            return (
                "DEEPSEEK_API_KEY is empty; configure the official DeepSeek key in Actions Secrets"
            )
        return None


settings = EpicSettings()
settings.ignore_request_questions = ["Please drag the crossing to complete the lines"]
install_deepseek_provider(settings)
apply_hcaptcha_drag_patch()
