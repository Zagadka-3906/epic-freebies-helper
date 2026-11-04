"""Inspect installed dependency contracts used by the provider and browser patches."""

import inspect
from importlib.metadata import version

from hcaptcha_challenger.agent import AgentConfig
from hcaptcha_challenger.agent.challenger import RoboticArm
from hcaptcha_challenger.tools.internal.base import Reasoner
from hcaptcha_challenger.tools.internal.providers.protocol import ChatProvider

from extensions.deepseek_provider import DeepSeekProvider


def main() -> None:
    if not version("hcaptcha-challenger").startswith("0.19."):
        raise RuntimeError("Review integration contracts before upgrading hcaptcha-challenger")
    if "provider" not in inspect.signature(Reasoner.__init__).parameters:
        raise RuntimeError("Reasoner no longer supports ChatProvider injection")
    for method in ("_create_default_provider", "cache_response"):
        if not callable(getattr(Reasoner, method, None)):
            raise RuntimeError(f"Missing Reasoner.{method} contract")
    for method in (
        "_capture_spatial_mapping",
        "challenge_image_label_select",
        "challenge_image_drag_drop",
    ):
        if not callable(getattr(RoboticArm, method, None)):
            raise RuntimeError(f"Missing RoboticArm.{method} contract")
    if "GEMINI_API_KEY" not in AgentConfig.model_fields:
        raise RuntimeError("Review the internal AgentConfig compatibility slot")
    if not isinstance(DeepSeekProvider(settings=None), ChatProvider):
        raise RuntimeError("DeepSeekProvider does not implement ChatProvider")
    print("Installed hcaptcha-challenger 0.19 provider/spatial contracts available")


if __name__ == "__main__":
    main()
