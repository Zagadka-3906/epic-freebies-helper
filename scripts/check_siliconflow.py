"""Check the live vision/JSON API contract before opening the Epic login page."""

import asyncio
from io import BytesIO

from google import genai
from google.genai import types
from hcaptcha_challenger.models import PointCoordinate
from PIL import Image
from pydantic import BaseModel, Field

from settings import settings


class StatusDescription(BaseModel):
    description: str


class SpatialReadiness(BaseModel):
    points: list[PointCoordinate] = Field(min_length=1, max_length=1)


async def main() -> None:
    if error := settings.llm_configuration_error:
        raise RuntimeError(error)

    # A small diagnostic image verifies vision support as well as key/model access.
    # A text-only request cannot detect a provider rejecting image_url inputs.
    buffer = BytesIO()
    Image.new("RGB", (64, 64), "red").save(buffer, format="PNG")
    response = await genai.Client().aio.models.generate_content(
        model=settings.SILICONFLOW_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/png"),
                    types.Part.from_text(
                        text="Describe the diagnostic image briefly. Return a JSON object."
                    ),
                ],
            )
        ],
        config=types.GenerateContentConfig(response_schema=StatusDescription),
    )
    if (
        not isinstance(response.parsed, StatusDescription)
        or not response.parsed.description.strip()
    ):
        raise RuntimeError("SiliconFlow did not return a usable structured vision response")
    print(f"SiliconFlow vision/JSON API ready | model={settings.SILICONFLOW_MODEL}")

    spatial = await genai.Client().aio.models.generate_content(
        model=settings.SILICONFLOW_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/png"),
                    types.Part.from_text(
                        text="Return the center of this image as one point. "
                        "Use normalized 0..1000 image coordinates. Return a JSON object."
                    ),
                ],
            )
        ],
        config=types.GenerateContentConfig(response_schema=SpatialReadiness),
    )
    if not isinstance(spatial.parsed, SpatialReadiness) or any(
        not (0 <= point.x <= 1000 and 0 <= point.y <= 1000) for point in spatial.parsed.points
    ):
        raise RuntimeError("SiliconFlow spatial API did not return normalized coordinates")
    print("SiliconFlow spatial reasoning API ready | thinking_budget=512 | format=json_schema")


if __name__ == "__main__":
    asyncio.run(main())
