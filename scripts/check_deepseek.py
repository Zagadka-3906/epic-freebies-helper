"""Live official API preflight; no Epic login and no game claims."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from hcaptcha_challenger.models import PointCoordinate
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from extensions.deepseek_provider import MODEL, DeepSeekProvider
from settings import settings


class VisionReadiness(BaseModel):
    left_color: str
    right_color: str


class SpatialReadiness(BaseModel):
    points: list[PointCoordinate] = Field(min_length=1, max_length=1)


async def main() -> None:
    if error := settings.llm_configuration_error:
        raise RuntimeError(error)
    provider = DeepSeekProvider(settings)
    with TemporaryDirectory(prefix="epic-api-preflight-") as directory:
        image_path = Path(directory) / "diagnostic.png"
        image = Image.new("RGB", (200, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((25, 25, 75, 75), fill="red")
        draw.rectangle((125, 25, 175, 75), fill="blue")
        image.save(image_path)
        vision = await provider.generate_with_images(
            images=[image_path],
            response_schema=VisionReadiness,
            user_prompt="Name the two colored objects' colors in English, lowercase: left and right.",
        )
        if (vision.left_color.lower().strip(), vision.right_color.lower().strip()) != (
            "red",
            "blue",
        ):
            raise RuntimeError("DeepSeek vision response did not identify diagnostic image colors")
        print(f"Official DeepSeek vision/JSON API ready | model={MODEL}", flush=True)
        spatial = await provider.generate_with_images(
            images=[image_path],
            response_schema=SpatialReadiness,
            user_prompt="Return the center of the red circle as one point. "
            "Use normalized 0..1000 coordinates relative to the entire image, "
            "top-left=(0,0), bottom-right=(1000,1000).",
        )
        point = spatial.points[0]
        if abs(point.x - 250) > 75 or abs(point.y - 500) > 75:
            raise RuntimeError(
                "DeepSeek diagnostic coordinates did not match the normalized image space"
            )
        print(
            "Official DeepSeek spatial/JSON API ready | thinking=enabled | effort=low", flush=True
        )


if __name__ == "__main__":
    asyncio.run(main())
