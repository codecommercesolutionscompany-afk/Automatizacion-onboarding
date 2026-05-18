import logging

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


def register_email_sent(
    nombre: str,
    email: str,
    email_id: str,
    whatsapp: str | None = None,
    servicio: str = "PDC",
    estado_envio: str = "sent",
    proveedor: str = "Resend",
    observaciones: str | None = None,
) -> bool:
    if not settings.pdc_sheet_webhook_url:
        logger.warning(
            "PDC_SHEET_WEBHOOK_URL no está definida. No se registra envío en Sheet."
        )
        return False

    payload = {
        "nombre": nombre,
        "correo": email,
        "whatsapp": whatsapp or "",
        "servicio": servicio,
        "email_id": email_id,
        "estado_envio": estado_envio,
        "proveedor": proveedor,
        "observaciones": observaciones or "",
    }

    try:
        response = requests.post(
            settings.pdc_sheet_webhook_url,
            json=payload,
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.warning(
            "No se pudo registrar envío en Sheet. email=%s email_id=%s error=%s",
            email,
            email_id,
            exc,
        )
        return False

    if not response.ok:
        logger.warning(
            "No se pudo registrar envío en Sheet. email=%s email_id=%s "
            "status_code=%s response=%s",
            email,
            email_id,
            response.status_code,
            response.text,
        )
        return False

    logger.warning(
        "Registro de envío guardado en Sheet. email=%s email_id=%s status_code=%s",
        email,
        email_id,
        response.status_code,
    )
    return True
