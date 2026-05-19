import logging
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.schemas.onboarding import (
    LeadWebhookPayload,
    ProcessScheduledEmailsPayload,
    PreviewSchedulePayload,
    SendEmailPayload,
)
from app.services.email_templates import (
    EMAIL_SUBJECTS,
    EmailTemplateError,
    load_pdc_email_template,
    render_email_template,
)
from app.services.resend_service import ResendServiceError, send_email_with_resend
from app.services.schedule_service import (
    PDC_TIMEZONE,
    ScheduledEmail,
    build_cm_tasks_from_schedule,
    build_pdc_email_schedule,
    parse_pdc_datetime,
)
from app.services.sheet_service import (
    check_sent_email,
    claim_due_scheduled_emails,
    mark_scheduled_email_failed,
    mark_scheduled_email_sent,
    register_cm_task,
    register_email_sent,
    register_scheduled_email,
)


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


def _send_pdc_email(
    nombre: str,
    email: str,
    email_id: str,
    whatsapp: str | None = None,
) -> dict:
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
        whatsapp=whatsapp,
        servicio="PDC",
        estado_envio="sent",
        proveedor="Resend",
    )
    return {
        "resend_response": resend_response,
        "sheet_registered": sheet_registered,
    }


def send_pdc_email(
    nombre: str,
    email: str,
    email_id: str,
    whatsapp: str | None = None,
) -> dict:
    try:
        return _send_pdc_email(nombre, email, email_id, whatsapp)
    except (EmailTemplateError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ResendServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el email de onboarding.",
        ) from exc


def serialize_schedule(schedule: list[ScheduledEmail]) -> list[dict]:
    return [
        {
            "email_id": scheduled_email.email_id,
            "scheduled_at": scheduled_email.scheduled_at.isoformat(timespec="seconds"),
            "bloque": scheduled_email.bloque,
        }
        for scheduled_email in schedule
    ]


def build_schedule_for_payload(
    fecha_reserva: str | None,
    fecha_llegada: str | None,
) -> list[ScheduledEmail] | None:
    llegada = parse_pdc_datetime(fecha_llegada)
    if not llegada:
        return None

    reserva = parse_pdc_datetime(fecha_reserva)
    return build_pdc_email_schedule(
        fecha_inicio=reserva or datetime.now(PDC_TIMEZONE),
        fecha_llegada=llegada,
    )


def register_schedule_rows(
    lead: LeadWebhookPayload,
    schedule: list[ScheduledEmail],
) -> tuple[int, int]:
    registered_count = 0
    duplicate_count = 0
    email = str(lead.email)

    for scheduled_email in schedule:
        result = register_scheduled_email(
            nombre=lead.nombre or "",
            email=email,
            whatsapp=lead.whatsapp,
            servicio="PDC",
            fecha_reserva=lead.fecha_reserva,
            fecha_llegada=lead.fecha_llegada,
            email_id=scheduled_email.email_id,
            email_title=EMAIL_SUBJECTS[scheduled_email.email_id],
            fecha_programada=scheduled_email.scheduled_at.isoformat(timespec="seconds"),
            bloque=scheduled_email.bloque,
            estado="programado",
        )
        status = str(result.get("status", "")).lower()
        if status == "duplicate":
            duplicate_count += 1
        elif result.get("ok"):
            registered_count += 1

    return registered_count, duplicate_count


def register_cm_tasks_for_schedule(
    lead: LeadWebhookPayload,
    schedule: list[ScheduledEmail],
) -> tuple[int, int]:
    registered_count = 0
    duplicate_count = 0
    tasks = build_cm_tasks_from_schedule(
        schedule=schedule,
        nombre=lead.nombre or "",
        correo=str(lead.email),
        whatsapp=lead.whatsapp,
        servicio="PDC",
    )

    for task in tasks:
        result = register_cm_task(
            nombre=task.nombre,
            email=task.correo,
            whatsapp=task.whatsapp,
            servicio=task.servicio,
            motivo=task.motivo,
            mensaje_sugerido=task.mensaje_sugerido,
            estado=task.estado,
            fecha_sugerida=task.fecha_sugerida.isoformat(timespec="seconds"),
            observaciones=task.observaciones,
        )
        status = str(result.get("status", "")).lower()
        if status == "duplicate":
            duplicate_count += 1
        elif result.get("ok"):
            registered_count += 1

    return registered_count, duplicate_count


def summarize_processing_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return message[:300]


def validate_claimed_email_item(item: dict) -> tuple[int | None, str | None, str | None]:
    row_number = item.get("row_number")
    email = item.get("correo")
    email_id = item.get("email_id")

    try:
        parsed_row_number = int(row_number)
    except (TypeError, ValueError):
        parsed_row_number = None

    parsed_email = str(email).strip() if email else None
    parsed_email_id = str(email_id).strip() if email_id else None
    return parsed_row_number, parsed_email, parsed_email_id


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
    email_already_sent = check_sent_email(str(lead.email), email_id)
    email_sent = False
    send_result = {"sheet_registered": False, "resend_response": None}

    if email_already_sent:
        logger.warning(
            "No se reenvia email 01 porque Apps Script reporto duplicado. email=%s",
            lead.email,
        )
    else:
        send_result = send_pdc_email(
            nombre=lead.nombre or "",
            email=str(lead.email),
            email_id=email_id,
            whatsapp=lead.whatsapp,
        )
        email_sent = True

    schedule = build_schedule_for_payload(lead.fecha_reserva, lead.fecha_llegada)
    scheduled_registered_count = 0
    scheduled_duplicate_count = 0
    cm_tasks_count = 0
    cm_tasks_duplicate_count = 0

    if schedule is None:
        logger.warning(
            "No se programa onboarding futuro PDC porque falta o es invalida "
            "fecha_llegada. email=%s fecha_llegada=%s",
            lead.email,
            lead.fecha_llegada,
        )
        scheduled_count = 0
    else:
        scheduled_count = len(schedule)
        scheduled_registered_count, scheduled_duplicate_count = register_schedule_rows(
            lead,
            schedule,
        )
        cm_tasks_count, cm_tasks_duplicate_count = register_cm_tasks_for_schedule(
            lead,
            schedule,
        )

    return {
        "status": "sent" if email_sent else "already_sent",
        "message": "Onboarding PDC procesado correctamente.",
        "email": str(lead.email),
        "email_id": email_id,
        "email_sent": email_sent,
        "sheet_registered": send_result["sheet_registered"],
        "resend_response": send_result["resend_response"],
        "scheduled_count": scheduled_count,
        "scheduled_registered_count": scheduled_registered_count,
        "scheduled_duplicate_count": scheduled_duplicate_count,
        "cm_tasks_count": cm_tasks_count,
        "cm_tasks_duplicate_count": cm_tasks_duplicate_count,
    }


@router.post("/process-scheduled-emails")
def process_scheduled_emails(
    payload: ProcessScheduledEmailsPayload | None = None,
    x_cron_secret: str | None = Header(default=None, alias="X-Cron-Secret"),
) -> dict:
    if settings.pdc_cron_secret:
        if x_cron_secret != settings.pdc_cron_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        logger.warning(
            "PDC_CRON_SECRET no esta definida. "
            "process-scheduled-emails se ejecuta sin proteccion."
        )

    payload = payload or ProcessScheduledEmailsPayload()
    now = parse_pdc_datetime(payload.now) if payload.now else datetime.now(PDC_TIMEZONE)
    if not now:
        raise HTTPException(
            status_code=400,
            detail="now debe tener formato ISO si se envia.",
        )

    claimed_emails = claim_due_scheduled_emails(now=now, limit=payload.limit)
    items = []
    sent_count = 0
    failed_count = 0

    for claimed_email in claimed_emails:
        row_number, email, email_id = validate_claimed_email_item(claimed_email)
        item_result = {
            "row_number": row_number,
            "email": email,
            "email_id": email_id,
            "status": "failed",
            "sheet_marked": False,
        }

        if row_number is None or not email or not email_id:
            error_message = "Fila reclamada incompleta: faltan row_number, correo o email_id."
            item_result["error"] = error_message
            failed_count += 1
            logger.warning(
                "Email programado invalido. row_number=%s email=%s email_id=%s",
                row_number,
                email,
                email_id,
            )
            items.append(item_result)
            continue

        try:
            send_result = _send_pdc_email(
                nombre=str(claimed_email.get("nombre") or ""),
                email=email,
                email_id=email_id,
                whatsapp=claimed_email.get("whatsapp"),
            )
            sheet_marked = mark_scheduled_email_sent(
                row_number=row_number,
                email=email,
                email_id=email_id,
                observaciones="Enviado por procesador automatico",
            )
            sent_count += 1
            item_result.update(
                {
                    "status": "sent",
                    "sheet_marked": sheet_marked,
                    "sheet_registered": send_result["sheet_registered"],
                }
            )
            logger.warning(
                "Email programado enviado. row_number=%s email=%s email_id=%s "
                "sheet_marked=%s",
                row_number,
                email,
                email_id,
                sheet_marked,
            )
        except Exception as exc:
            error_message = summarize_processing_error(exc)
            sheet_marked = mark_scheduled_email_failed(
                row_number=row_number,
                email=email,
                email_id=email_id,
                observaciones=f"Error al enviar por Resend: {error_message}",
            )
            failed_count += 1
            item_result.update(
                {
                    "status": "failed",
                    "error": error_message,
                    "sheet_marked": sheet_marked,
                }
            )
            logger.exception(
                "Fallo email programado. row_number=%s email=%s email_id=%s "
                "sheet_marked=%s",
                row_number,
                email,
                email_id,
                sheet_marked,
            )

        items.append(item_result)

    return {
        "status": "ok",
        "claimed_count": len(claimed_emails),
        "processed_count": len(items),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "items": items,
    }


@router.post("/preview-schedule")
def preview_schedule(payload: PreviewSchedulePayload) -> dict:
    llegada = parse_pdc_datetime(payload.fecha_llegada)
    if not llegada:
        raise HTTPException(
            status_code=400,
            detail="fecha_llegada es obligatoria y debe tener formato ISO.",
        )

    reserva = parse_pdc_datetime(payload.fecha_reserva)
    schedule = build_pdc_email_schedule(
        fecha_inicio=reserva or datetime.now(PDC_TIMEZONE),
        fecha_llegada=llegada,
    )
    cm_tasks = build_cm_tasks_from_schedule(
        schedule=schedule,
        nombre=payload.nombre,
        correo=str(payload.email),
        whatsapp=payload.whatsapp,
        servicio="PDC",
    )

    return {
        "status": "ok",
        "schedule": serialize_schedule(schedule),
        "cm_tasks_preview": [
            {
                "motivo": task.motivo,
                "fecha_sugerida": task.fecha_sugerida.isoformat(timespec="seconds"),
                "mensaje_sugerido": task.mensaje_sugerido,
            }
            for task in cm_tasks
        ],
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
