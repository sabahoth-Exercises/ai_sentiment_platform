import re
from pydantic import BaseModel, Field, field_validator

LATIN_TEXT_RE = re.compile(r"^[A-Za-z0-9\s\.,!\?\-\'\"\(\):;]+$")
HAS_LETTER_RE = re.compile(r"[A-Za-z]")  # at least one letter

# Валидация данных
class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=5,
        max_length=1500,
        description="Latin-only meaningful text for sentiment analysis.",
        examples=["I love this app"],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        # 1. Allowed characters only
        if not LATIN_TEXT_RE.fullmatch(value):
            raise ValueError(
                "hint": "Only Latin letters, numbers, spaces and basic punctuation are allowed. Text must contain at least one Latin letter, 5 letters."
            )

        # 2. Must contain at least one letter
        if not HAS_LETTER_RE.search(value):
            raise ValueError(
                "Text must contain Latin letter."
            )
    

        return value


class PredictResponse(BaseModel):
    task_id: str = Field(
        ...,
        description="Celery task identifier",
        examples=["4f8f2b5e-1234-5678-9abc-def012345678"],
    )


class ResultResponse(BaseModel):
    status: str = Field(..., examples=["pending", "done"])
    sentiment: str | None = Field(default=None, examples=["positive"])