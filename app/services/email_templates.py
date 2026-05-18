import logging
from pathlib import Path
from urllib.parse import urlencode

from app.core.config import settings


logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_MAP = {
    "01-bienvenida": "01-bienvenida-pdc.html",
    "02-mochila": "02-mochila-pdc.html",
    "03-como-llegar": "03-como-llegar-pdc.html",
    "04-como-vivir": "04-como-vivir-pdc.html",
    "05-vida-practica": "05-vida-practica-pdc.html",
    "06-recordatorio-final": "06-ultimo-recordatorio-pdc.html",
}

EMAIL_SUBJECTS = {
    "01-bienvenida": "Tu lugar en el PDC ya está reservado",
    "02-mochila": "Guía para preparar tu mochila",
    "03-como-llegar": "Cómo llegar a Madre Selva",
    "04-como-vivir": "Cómo vamos a vivir estos días",
    "05-vida-practica": "Vida práctica en Madre Selva",
    "06-recordatorio-final": "Último recordatorio antes de viajar",
}

PDC_EMAILS_DIR = Path(__file__).resolve().parents[1] / "emails" / "pdc"


class EmailTemplateError(ValueError):
    """Error de configuracion o lectura de templates de email."""


def load_pdc_email_template(email_id: str) -> str:
    filename = EMAIL_TEMPLATE_MAP.get(email_id)
    if not filename:
        valid_ids = ", ".join(EMAIL_TEMPLATE_MAP)
        raise EmailTemplateError(
            f"email_id invalido: {email_id}. Valores disponibles: {valid_ids}."
        )

    template_path = PDC_EMAILS_DIR / filename
    logger.warning("Cargando template PDC. email_id=%s path=%s", email_id, template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template no encontrado: {template_path}")

    return template_path.read_text(encoding="utf-8")


def render_email_template(
    html: str,
    nombre: str,
    email: str,
    email_id: str | None = None,
) -> str:
    rendered = html.replace("{{NOMBRE}}", nombre).replace("{{CORREO}}", email)

    if "[PEGAR_LINK_DE_CONFIRMACION]" not in rendered:
        return rendered

    if not settings.pdc_confirmation_url or not email_id:
        return rendered

    query_string = urlencode({"correo": email, "email_id": email_id})
    confirmation_link = f"{settings.pdc_confirmation_url}?{query_string}"
    return rendered.replace("[PEGAR_LINK_DE_CONFIRMACION]", confirmation_link)
