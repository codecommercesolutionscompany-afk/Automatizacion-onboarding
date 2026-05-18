import logging

from fastapi import APIRouter, HTTPException

from app.schemas.onboarding import LeadWebhookPayload, SendEmailPayload
from app.services.email_templates import (
    EMAIL_SUBJECTS,
    EmailTemplateError,
    load_pdc_email_template,
    render_email_template,
)
from app.services.resend_service import ResendServiceError, send_email_with_resend
from app.services.sheet_service import register_email_sent


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/automatizacion/onboarding", tags=["onboarding"])


def get_missing_contact_fields(lead: LeadWebhookPayload) -> list[str]:
    missing_fields: list[str] = []

    if not lead.nombre or not lead.nombre.strip():
        missing_fields.append("nombre")

    if not lead.email:
        missing_fields.append("email")

    return missing_fields


def build_plain_text_email(nombre: str) -> str:
    return (
        f"Hola {nombre.strip()},\n\n"
        "Te compartimos informacion importante del onboarding PDC de Madre Selva.\n\n"
        "Movimiento Na Lu'um - Madre Selva"
    )


def _send_pdc_email(nombre: str, email: str, email_id: str) -> dict:
    template_html = load_pdc_email_template(email_id)
    rendered_html = render_email_template(template_html, nombre, email, email_id)
    resend_response = send_email_with_resend(
        to_email=email,
        subject=EMAIL_SUBJECTS[email_id],
        html=rendered_html,
        text=build_plain_text_email(nombre),
    )
    logger.warning("Email enviado por Resend. email=%s email_id=%s", email, email_id)
    sheet_registered = register_email_sent(
        nombre=nombre,
        email=email,
        email_id=email_id,
        servicio="PDC",
        estado_envio="sent",
        proveedor="Resend",
    )
    return {
        "resend_response": resend_response,
        "sheet_registered": sheet_registered,
    }


def send_pdc_email(nombre: str, email: str, email_id: str) -> dict:
    try:
        return _send_pdc_email(nombre, email, email_id)
    except (EmailTemplateError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ResendServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el email de onboarding.",
        ) from exc


@router.post("")
def onboarding_webhook(lead: LeadWebhookPayload) -> dict:
    """Procesa el webhook del CRM y dispara onboarding si el lead califica."""
    estado_normalizado = (lead.estado or "").strip().lower()
    producto_normalizado = (lead.producto or "").strip().upper()

    if estado_normalizado != "cerrado" or producto_normalizado != "PDC":
        return {
            "status": "ignored",
            "message": "Lead ignorado: no cumple las condiciones de onboarding.",
        }

    missing_fields = get_missing_contact_fields(lead)
    if missing_fields:
        return {
            "status": "alert",
            "message": "No se envio el onboarding porque faltan datos obligatorios.",
            "alert_for": "pm_sheet",
            "missing_fields": missing_fields,
        }

    email_id = "01-bienvenida"
    send_result = send_pdc_email(
        nombre=lead.nombre or "",
        email=str(lead.email),
        email_id=email_id,
    )

    return {
        "status": "sent",
        "message": "Email de onboarding enviado correctamente.",
        "email": str(lead.email),
        "email_id": email_id,
        "sheet_registered": send_result["sheet_registered"],
        "resend_response": send_result["resend_response"],
    }


@router.post("/send-email")
def send_onboarding_email(payload: SendEmailPayload) -> dict:
    try:
        send_result = _send_pdc_email(
            nombre=payload.nombre,
            email=str(payload.email),
            email_id=payload.email_id,
        )
    except Exception as exc:
        logger.exception(
            "Error enviando email manual de onboarding. email=%s email_id=%s nombre=%s",
            payload.email,
            payload.email_id,
            payload.nombre,
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el email de onboarding.",
        ) from exc

    return {
        "status": "sent",
        "email": str(payload.email),
        "email_id": payload.email_id,
        "sheet_registered": send_result["sheet_registered"],
    }
