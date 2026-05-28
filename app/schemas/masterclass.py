from typing import Any

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class MasterclassAccessPayload(BaseModel):
    """Payload enviado desde Google Form/Apps Script para acceso a masterclass."""

    nombre: str = Field(min_length=1)
    email: EmailStr
    whatsapp: str | None = None
    instagram: str | None = None
    masterclass_nombre: str = Field(min_length=1)
    fecha_masterclass: str = Field(min_length=1)
    hora_masterclass: str = Field(min_length=1)
    meet_url: HttpUrl

    @field_validator(
        "nombre",
        "email",
        "whatsapp",
        "instagram",
        "masterclass_nombre",
        "fecha_masterclass",
        "hora_masterclass",
        "meet_url",
        mode="before",
    )
    @classmethod
    def strip_empty_strings(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped_value = value.strip()
            return stripped_value or None
        return value
