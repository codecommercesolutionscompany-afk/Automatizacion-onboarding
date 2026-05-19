import logging
from typing import Any

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


def post_to_sheet(payload: dict[str, Any], context: str) -> dict[str, Any]:
    if not settings.pdc_sheet_webhook_url:
        logger.warning("PDC_SHEET_WEBHOOK_URL no esta definida. context=%s", context)
        return {"status": "skipped", "ok": False, "reason": "missing_webhook_url"}

    try:
        response = requests.post(
            settings.pdc_sheet_webhook_url,
            json=payload,
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo llamar Apps Script. context=%s error=%s", context, exc)
        return {"status": "error", "ok": False, "error": str(exc)}

    if not response.ok:
        logger.warning(
            "Apps Script devolvio error. context=%s status_code=%s response=%s",
            context,
            response.status_code,
            response.text,
        )
        return {
            "status": "error",
            "ok": False,
            "status_code": response.status_code,
            "response": response.text,
        }

    try:
        data = response.json()
    except ValueError:
        data = {"status": "ok", "raw_response": response.text}

    status = str(data.get("status", "ok")).lower()
    if status == "duplicate":
        logger.warning("Apps Script reporto duplicado. context=%s response=%s", context, data)
    else:
        logger.warning("Apps Script OK. context=%s status=%s", context, status)

    data["ok"] = True
    return data


def check_sent_email(email: str, email_id: str) -> bool | None:
    payload = {
        "action": "check_sent_email",
        "correo": email,
        "email_id": email_id,
    }
    result = post_to_sheet(payload, f"check_sent_email email={email} email_id={email_id}")
    status = str(result.get("status", "")).lower()

    if status == "duplicate":
        return True

    if "exists" in result:
        return bool(result["exists"])

    if status in {"ok", "not_found", "missing", "absent"}:
        return False

    if not result.get("ok"):
        return None

    return False


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
            "PDC_SHEET_WEBHOOK_URL no esta definida. No se registra envio en Sheet."
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
            "No se pudo registrar envio en Sheet. email=%s email_id=%s error=%s",
            email,
            email_id,
            exc,
        )
        return False

    if not response.ok:
        logger.warning(
            "No se pudo registrar envio en Sheet. email=%s email_id=%s "
            "status_code=%s response=%s",
            email,
            email_id,
            response.status_code,
            response.text,
        )
        return False

    try:
        data = response.json()
    except ValueError:
        data = {"status": "ok"}

    if str(data.get("status", "")).lower() == "duplicate":
        logger.warning(
            "Apps Script reporto envio duplicado. email=%s email_id=%s",
            email,
            email_id,
        )
        return True

    logger.warning(
        "Registro de envio guardado en Sheet. email=%s email_id=%s status_code=%s",
        email,
        email_id,
        response.status_code,
    )
    return True


def register_scheduled_email(
    nombre: str,
    email: str,
    whatsapp: str | None,
    servicio: str,
    fecha_reserva: str | None,
    fecha_llegada: str | None,
    email_id: str,
    email_title: str,
    fecha_programada: str,
    bloque: str,
    estado: str = "programado",
    observaciones: str | None = None,
) -> dict[str, Any]:
    payload = {
        "action": "register_scheduled_email",
        "nombre": nombre,
        "correo": email,
        "whatsapp": whatsapp or "",
        "servicio": servicio,
        "fecha_reserva": fecha_reserva or "",
        "fecha_llegada": fecha_llegada or "",
        "email_id": email_id,
        "email_titulo": email_title,
        "fecha_programada": fecha_programada,
        "bloque": bloque,
        "estado": estado,
        "observaciones": observaciones or "",
    }
    return post_to_sheet(
        payload,
        f"register_scheduled_email email={email} email_id={email_id}",
    )


def register_cm_task(
    nombre: str,
    email: str,
    whatsapp: str | None,
    servicio: str,
    motivo: str,
    mensaje_sugerido: str,
    estado: str,
    fecha_sugerida: str,
    observaciones: str | None = None,
) -> dict[str, Any]:
    payload = {
        "action": "register_cm_task",
        "nombre": nombre,
        "correo": email,
        "whatsapp": whatsapp or "",
        "servicio": servicio,
        "motivo": motivo,
        "mensaje_sugerido": mensaje_sugerido,
        "estado": estado,
        "fecha_sugerida": fecha_sugerida,
        "observaciones": observaciones or "",
    }
    return post_to_sheet(payload, f"register_cm_task email={email} motivo={motivo}")
