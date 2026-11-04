"""Check the live vision/JSON API contract before opening the Epic login page."""

import asyncio
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

from settings import settings


class StatusDescription(BaseModel):
    description: str


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


if __name__ == "__main__":
    asyncio.run(main())
