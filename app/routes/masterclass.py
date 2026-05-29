import logging

from fastapi import APIRouter, HTTPException

from app.schemas.masterclass import MasterclassAccessPayload, MasterclassReminderPayload
from app.services.masterclass_service import (
    MASTERCLASS_ACCESS_EMAIL_ID,
    MasterclassServiceError,
    get_masterclass_reminder_email_id,
    send_masterclass_access_email,
    send_masterclass_reminder_email,
)
from app.services.resend_service import ResendServiceError


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/automatizacion/masterclass",
    tags=["masterclass"],
)


@router.post("/access")
def send_masterclass_access(payload: MasterclassAccessPayload) -> dict:
    """Envia el acceso de Google Meet para una inscripcion a masterclass."""
    try:
        resend_response = send_masterclass_access_email(payload)
    except ResendServiceError as exc:
        logger.exception(
            "Fallo Resend al enviar acceso masterclass. email=%s email_id=%s",
            payload.email,
            MASTERCLASS_ACCESS_EMAIL_ID,
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el acceso a la masterclass.",
        ) from exc
    except MasterclassServiceError as exc:
        logger.exception(
            "Fallo interno al enviar acceso masterclass. email=%s email_id=%s",
            payload.email,
            MASTERCLASS_ACCESS_EMAIL_ID,
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el acceso a la masterclass.",
        ) from exc

    return {
        "status": "sent",
        "email": str(payload.email),
        "email_id": MASTERCLASS_ACCESS_EMAIL_ID,
        "message": "Acceso a masterclass enviado correctamente.",
        "resend_response": {
            "id": resend_response.get("id"),
        },
    }


@router.post("/send-reminder")
def send_masterclass_reminder(payload: MasterclassReminderPayload) -> dict:
    """Envia un recordatorio de masterclass sin registrar datos en Sheets."""
    email_id = get_masterclass_reminder_email_id(payload.reminder_type)

    try:
        resend_response = send_masterclass_reminder_email(payload)
    except ResendServiceError as exc:
        logger.exception(
            "Fallo Resend al enviar recordatorio masterclass. email=%s email_id=%s",
            payload.email,
            email_id,
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el recordatorio de masterclass.",
        ) from exc
    except MasterclassServiceError as exc:
        logger.exception(
            "Fallo interno al enviar recordatorio masterclass. email=%s email_id=%s",
            payload.email,
            email_id,
        )
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el recordatorio de masterclass.",
        ) from exc

    return {
        "status": "sent",
        "email": str(payload.email),
        "email_id": email_id,
        "message": "Recordatorio de masterclass enviado correctamente.",
        "resend_response": {
            "id": resend_response.get("id"),
        },
    }
