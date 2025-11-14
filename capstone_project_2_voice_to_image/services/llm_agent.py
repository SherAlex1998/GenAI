import os
import re
from typing import Final

from dotenv import load_dotenv
from openai import OpenAI

from services.logger import log

load_dotenv()

PROMPT_TEMPLATE: Final[str] = (
    "You are an expert prompt engineer for text-to-image models. "
    "Rewrite the given user request into a vivid, specific English prompt that highlights the main subject, "
    "environment, composition, lighting, mood, colors, camera details, and artistic style as appropriate. "
    "Do not mention that you are rewriting or improving a prompt; just output the final prompt."
)


class LLMAgent:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")

        log("Initializing OpenAI client...")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def build_image_prompt(self, transcript: str) -> str:
        if not transcript or not transcript.strip():
            raise ValueError("Transcript is empty.")

        normalized = transcript.strip()
        normalized = re.sub(r"\s+", " ", normalized)

        if not normalized.endswith((".", "!", "?")):
            normalized += "."

        messages = [
            {"role": "system", "content": PROMPT_TEMPLATE},
            {
                "role": "user",
                "content": (
                    "User speech transcript:\n"
                    f"{normalized}\n\n"
                    "Produce only the improved image-generation prompt."
                ),
            },
        ]

        try:
            response = self.client.responses.create(
                model=self.model,
                temperature=self.temperature,
                input=messages,
            )
            log("LLM prompt generation succeeded.")
            log(f"LLM prompt: {response.output_text}")
        except Exception as ex:
            raise RuntimeError(f"Failed to contact LLM for prompt generation: {ex}") from ex

        prompt = getattr(response, "output_text", "").strip()
        if not prompt:
            raise RuntimeError("LLM returned an empty prompt.")

        return prompt