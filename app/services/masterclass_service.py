import logging
from html import escape
from pathlib import Path
from typing import Any

from app.schemas.masterclass import MasterclassAccessPayload
from app.services.resend_service import ResendServiceError, send_email_with_resend


logger = logging.getLogger(__name__)

MASTERCLASS_ACCESS_EMAIL_ID = "masterclass-acceso"
MASTERCLASS_ACCESS_SUBJECT = "Tu acceso a la masterclass de Madre Selva"
MASTERCLASS_EMAILS_DIR = Path(__file__).resolve().parents[1] / "emails" / "masterclass"
MASTERCLASS_ACCESS_TEMPLATE = MASTERCLASS_EMAILS_DIR / "masterclass-acceso.html"


class MasterclassServiceError(RuntimeError):
    """Error controlado al preparar o enviar emails de masterclass."""


def load_masterclass_access_template() -> str:
    if not MASTERCLASS_ACCESS_TEMPLATE.exists():
        raise MasterclassServiceError("Template de masterclass no encontrado.")

    return MASTERCLASS_ACCESS_TEMPLATE.read_text(encoding="utf-8")


def render_masterclass_access_template(
    template_html: str,
    payload: MasterclassAccessPayload,
) -> str:
    replacements = {
        "{{NOMBRE}}": escape(payload.nombre),
        "{{MASTERCLASS_NOMBRE}}": escape(payload.masterclass_nombre),
        "{{FECHA_MASTERCLASS}}": escape(payload.fecha_masterclass),
        "{{HORA_MASTERCLASS}}": escape(payload.hora_masterclass),
        "{{MEET_URL}}": escape(str(payload.meet_url)),
    }

    rendered_html = template_html
    for placeholder, value in replacements.items():
        rendered_html = rendered_html.replace(placeholder, value)

    return rendered_html


def build_masterclass_access_text(payload: MasterclassAccessPayload) -> str:
    return (
        f"Hola {payload.nombre},\n\n"
        f"Ya tenes tu acceso a {payload.masterclass_nombre}.\n\n"
        f"Fecha: {payload.fecha_masterclass}\n"
        f"Hora: {payload.hora_masterclass}\n"
        f"Link de Google Meet: {payload.meet_url}\n\n"
        "Te recomendamos entrar unos minutos antes para probar audio, camara y conexion.\n\n"
        "Madre Selva / Movimiento Na Lu'um"
    )


def send_masterclass_access_email(payload: MasterclassAccessPayload) -> dict[str, Any]:
    try:
        template_html = load_masterclass_access_template()
        rendered_html = render_masterclass_access_template(template_html, payload)
        return send_email_with_resend(
            to_email=str(payload.email),
            subject=MASTERCLASS_ACCESS_SUBJECT,
            html=rendered_html,
            text=build_masterclass_access_text(payload),
        )
    except ResendServiceError:
        raise
    except Exception as exc:
        logger.exception(
            "Error preparando email de masterclass. email=%s email_id=%s",
            payload.email,
            MASTERCLASS_ACCESS_EMAIL_ID,
        )
        raise MasterclassServiceError(
            "No se pudo preparar el email de acceso a masterclass."
        ) from exc
