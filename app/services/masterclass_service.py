import logging
from datetime import date
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.schemas.masterclass import MasterclassAccessPayload, MasterclassReminderPayload
from app.services.resend_service import ResendServiceError, send_email_with_resend


logger = logging.getLogger(__name__)

MASTERCLASS_ACCESS_EMAIL_ID = "masterclass-acceso"
MASTERCLASS_ACCESS_SUBJECT = "Tu acceso a la masterclass de Madre Selva"
MASTERCLASS_EMAILS_DIR = Path(__file__).resolve().parents[1] / "emails" / "masterclass"
MASTERCLASS_ACCESS_TEMPLATE = MASTERCLASS_EMAILS_DIR / "masterclass-acceso.html"
MASTERCLASS_REMINDER_CONFIG = {
    "2_dias": {
        "email_id": "masterclass-recordatorio-2-dias",
        "subject": "Recordatorio: tu masterclass es en 2 días",
        "template": "masterclass-recordatorio-2-dias.html",
    },
    "hoy": {
        "email_id": "masterclass-recordatorio-hoy",
        "subject": "Hoy es la masterclass · Acá tenés tu acceso",
        "template": "masterclass-recordatorio-hoy.html",
    },
}
MASTERCLASS_CONFIRMATION_BASE_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwVmvIs6zlvErXT24Gn4IlW6sYe6cuHJRwQFWTaBGGBxdYLcGpV7Kxlwir7nIx2xJCU/exec"
)
SPANISH_MONTHS = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


class MasterclassServiceError(RuntimeError):
    """Error controlado al preparar o enviar emails de masterclass."""


def load_masterclass_access_template() -> str:
    if not MASTERCLASS_ACCESS_TEMPLATE.exists():
        raise MasterclassServiceError("Template de masterclass no encontrado.")

    return MASTERCLASS_ACCESS_TEMPLATE.read_text(encoding="utf-8")


def load_masterclass_reminder_template(reminder_type: str) -> str:
    reminder_config = MASTERCLASS_REMINDER_CONFIG.get(reminder_type)
    if not reminder_config:
        raise MasterclassServiceError("Tipo de recordatorio de masterclass invalido.")

    template_path = MASTERCLASS_EMAILS_DIR / reminder_config["template"]
    if not template_path.exists():
        raise MasterclassServiceError("Template de recordatorio de masterclass no encontrado.")

    return template_path.read_text(encoding="utf-8")


def format_spanish_date(date_value: str) -> str:
    try:
        parsed_date = date.fromisoformat(date_value.strip())
    except ValueError:
        return date_value.strip()

    month_name = SPANISH_MONTHS[parsed_date.month]
    return f"{parsed_date.day} de {month_name} de {parsed_date.year}"


def format_argentina_time(time_value: str) -> str:
    stripped_time = time_value.strip()
    time_parts = stripped_time.split(":")

    if len(time_parts) >= 2 and time_parts[0].isdigit() and time_parts[1].isdigit():
        return f"{int(time_parts[0]):02d}:{int(time_parts[1]):02d} hs Argentina"

    return f"{stripped_time} hs Argentina"


def build_masterclass_confirmation_url(email: str) -> str:
    encoded_email = quote(email.strip(), safe="")
    return (
        f"{MASTERCLASS_CONFIRMATION_BASE_URL}"
        f"?action=confirm_masterclass_access"
        f"&correo={encoded_email}"
        f"&email_id={MASTERCLASS_ACCESS_EMAIL_ID}"
    )


def render_masterclass_access_template(
    template_html: str,
    payload: MasterclassAccessPayload,
) -> str:
    formatted_date = format_spanish_date(payload.fecha_masterclass)
    formatted_time = format_argentina_time(payload.hora_masterclass)
    confirmation_url = build_masterclass_confirmation_url(str(payload.email))
    replacements = {
        "{{NOMBRE}}": escape(payload.nombre),
        "{{MASTERCLASS_NOMBRE}}": escape(payload.masterclass_nombre),
        "{{FECHA_MASTERCLASS_DISPLAY}}": escape(formatted_date),
        "{{HORA_MASTERCLASS_DISPLAY}}": escape(formatted_time),
        "{{MEET_URL}}": escape(str(payload.meet_url)),
        "{{CONFIRMATION_URL}}": escape(confirmation_url),
    }

    rendered_html = template_html
    for placeholder, value in replacements.items():
        rendered_html = rendered_html.replace(placeholder, value)

    return rendered_html


def render_masterclass_reminder_template(
    template_html: str,
    payload: MasterclassReminderPayload,
) -> str:
    formatted_date = format_spanish_date(payload.fecha_masterclass)
    formatted_time = format_argentina_time(payload.hora_masterclass)
    replacements = {
        "{{NOMBRE}}": escape(payload.nombre),
        "{{MASTERCLASS_NOMBRE}}": escape(payload.masterclass_nombre),
        "{{FECHA_MASTERCLASS_DISPLAY}}": escape(formatted_date),
        "{{HORA_MASTERCLASS_DISPLAY}}": escape(formatted_time),
        "{{MEET_URL}}": escape(str(payload.meet_url)),
    }

    rendered_html = template_html
    for placeholder, value in replacements.items():
        rendered_html = rendered_html.replace(placeholder, value)

    return rendered_html


def build_masterclass_access_text(payload: MasterclassAccessPayload) -> str:
    formatted_date = format_spanish_date(payload.fecha_masterclass)
    formatted_time = format_argentina_time(payload.hora_masterclass)
    confirmation_url = build_masterclass_confirmation_url(str(payload.email))

    return (
        f"Hola {payload.nombre},\n\n"
        f"Ya tenes tu acceso a {payload.masterclass_nombre}.\n\n"
        f"Fecha: {formatted_date}\n"
        f"Hora: {formatted_time}\n"
        f"Link de Google Meet: {payload.meet_url}\n\n"
        "Confirma que recibiste el acceso aca:\n"
        f"{confirmation_url}\n\n"
        "Te recomendamos entrar unos minutos antes para probar audio, camara y conexion.\n\n"
        "Madre Selva / Movimiento Na Lu'um"
    )


def build_masterclass_reminder_text(payload: MasterclassReminderPayload) -> str:
    formatted_date = format_spanish_date(payload.fecha_masterclass)
    formatted_time = format_argentina_time(payload.hora_masterclass)

    return (
        f"Hola {payload.nombre},\n\n"
        f"Te recordamos tu participacion en {payload.masterclass_nombre}.\n\n"
        f"Fecha: {formatted_date}\n"
        f"Hora: {formatted_time}\n"
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


def get_masterclass_reminder_email_id(reminder_type: str) -> str:
    reminder_config = MASTERCLASS_REMINDER_CONFIG.get(reminder_type)
    if not reminder_config:
        raise MasterclassServiceError("Tipo de recordatorio de masterclass invalido.")

    return reminder_config["email_id"]


def send_masterclass_reminder_email(payload: MasterclassReminderPayload) -> dict[str, Any]:
    try:
        reminder_config = MASTERCLASS_REMINDER_CONFIG[payload.reminder_type]
        template_html = load_masterclass_reminder_template(payload.reminder_type)
        rendered_html = render_masterclass_reminder_template(template_html, payload)
        return send_email_with_resend(
            to_email=str(payload.email),
            subject=reminder_config["subject"],
            html=rendered_html,
            text=build_masterclass_reminder_text(payload),
        )
    except ResendServiceError:
        raise
    except Exception as exc:
        logger.exception(
            "Error preparando recordatorio de masterclass. email=%s email_id=%s",
            payload.email,
            get_masterclass_reminder_email_id(payload.reminder_type),
        )
        raise MasterclassServiceError(
            "No se pudo preparar el recordatorio de masterclass."
        ) from exc
