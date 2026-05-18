from typing import Any

from pydantic import BaseModel, EmailStr, field_validator


class LeadWebhookPayload(BaseModel):
    """Payload recibido desde el Sheet/CRM cuando cambia el estado de una tarjeta."""

    nombre: str | None = None
    email: EmailStr | None = None
    estado: str | None = None
    producto: str | None = None

    @field_validator("nombre", "email", "estado", "producto", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class SendEmailPayload(BaseModel):
    nombre: str
    email: EmailStr
    email_id: str
