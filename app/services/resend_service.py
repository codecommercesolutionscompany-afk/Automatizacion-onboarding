import logging
from typing import Any

import resend

from app.core.config import settings


logger = logging.getLogger(__name__)


class ResendServiceError(RuntimeError):
    """Error al configurar o enviar emails con Resend."""


def send_email_with_resend(
    to_email: str,
    subject: str,
    html: str,
    text: str | None = None,
) -> dict[str, Any]:
    if not settings.resend_api_key or not settings.resend_from_email:
        logger.error(
            "Configuracion incompleta para Resend. RESEND_API_KEY_exists=%s "
            "RESEND_FROM_EMAIL_exists=%s",
            bool(settings.resend_api_key),
            bool(settings.resend_from_email),
        )
        raise ResendServiceError("Faltan RESEND_API_KEY o RESEND_FROM_EMAIL.")

    resend.api_key = settings.resend_api_key

    payload: dict[str, Any] = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    if text:
        payload["text"] = text

    logger.warning(
        "Enviando email con Resend. to_email=%s subject=%s RESEND_FROM_EMAIL=%s "
        "RESEND_API_KEY_exists=%s",
        to_email,
        subject,
        settings.resend_from_email,
        bool(settings.resend_api_key),
    )

    try:
        return resend.Emails.send(payload)
    except Exception as exc:
        logger.exception(
            "Error real de Resend enviando email. to_email=%s subject=%s "
            "RESEND_FROM_EMAIL=%s",
            to_email,
            subject,
            settings.resend_from_email,
        )
        raise ResendServiceError("No se pudo enviar el email con Resend.") from exc
