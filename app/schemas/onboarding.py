from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class LeadWebhookPayload(BaseModel):
    """Payload recibido desde el Sheet/CRM cuando cambia el estado de una tarjeta."""

    nombre: str | None = None
    email: EmailStr | None = None
    whatsapp: str | None = None
    estado: str | None = None
    producto: str | None = None
    fecha_reserva: str | None = None
    fecha_llegada: str | None = None
    fecha_salida: str | None = None

    @field_validator(
        "nombre",
        "email",
        "whatsapp",
        "estado",
        "producto",
        "fecha_reserva",
        "fecha_llegada",
        "fecha_salida",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class SendEmailPayload(BaseModel):
    nombre: str
    email: EmailStr
    email_id: str


class PreviewSchedulePayload(BaseModel):
    nombre: str
    email: EmailStr
    whatsapp: str | None = None
    fecha_reserva: str | None = None
    fecha_llegada: str

    @field_validator("nombre", "email", "whatsapp", "fecha_reserva", "fecha_llegada", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ProcessScheduledEmailsPayload(BaseModel):
    now: str | None = None
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("now", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value
