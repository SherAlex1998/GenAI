import base64
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI

from services.logger import log

load_dotenv()


class ImageGenerationError(RuntimeError):
    pass


class ImageGenerationService:
    pass

    def __init__(
        self,
        model: str = "dall-e-2",
        default_size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024",
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.default_size = default_size

        log(
            f"ImageGenerationService initialized with model={model}, "
            f"default_size={default_size}."
        )

    def generate_image(
        self,
        prompt: str,
        *,
        size: Optional[Literal["1024x1024", "1024x1536", "1536x1024"]] = None,
    ) -> dict:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        image_size = size or self.default_size
        log(f"Sending prompt to OpenAI Image API (size={image_size}).")

        try:
            response = self.client.images.generate(
                model=self.model,
                size=image_size,
                prompt=prompt.strip(),
                response_format="b64_json",
            )
        except Exception as ex:
            log(f"[Error] Image generation failed: {ex}")
            raise ImageGenerationError(f"Failed to generate image: {ex}") from ex

        data = response.data[0]
        image_b64 = getattr(data, "b64_json", None)
        if not image_b64:
            raise ImageGenerationError("Image payload is empty.")

        image_bytes = base64.b64decode(image_b64)
        log("Image generation succeeded (base64 payload).")
        return {
            "format": "base64",
            "data": image_b64,
            "bytes": image_bytes,
        }

