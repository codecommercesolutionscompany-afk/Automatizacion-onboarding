from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


try:
    PDC_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
except ZoneInfoNotFoundError:
    PDC_TIMEZONE = timezone(timedelta(hours=-3), "America/Argentina/Buenos_Aires")
PDC_SCHEDULE_EMAIL_IDS = [
    "02-mochila",
    "03-como-llegar",
    "04-como-vivir",
    "05-vida-practica",
    "06-recordatorio-final",
]

PDC_BLOCK_TIMES = [time(9, 0), time(15, 0), time(18, 0)]
PDC_CM_MESSAGE = (
    "Hola, ¿cómo estás? Te escribimos para avisarte que te enviamos por email "
    "más de una guía importante del PDC.\n\n"
    "Como tu fecha de llegada está cerca, agrupamos parte de la información "
    "para que puedas leerla con tiempo y llegar con tranquilidad.\n\n"
    "No hace falta que leas todo apurado/a, pero sí te recomendamos revisar "
    "los correos durante el día y confirmar la lectura desde el botón que "
    "aparece al final de cada uno.\n\n"
    "Cualquier duda puntual, nos podés escribir por acá."
)


@dataclass(frozen=True)
class ScheduledEmail:
    email_id: str
    scheduled_at: datetime
    bloque: str


@dataclass(frozen=True)
class CMTask:
    nombre: str
    correo: str
    whatsapp: str | None
    servicio: str
    motivo: str
    mensaje_sugerido: str
    estado: str
    fecha_sugerida: datetime
    observaciones: str = ""


def ensure_pdc_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=PDC_TIMEZONE)
    return value.astimezone(PDC_TIMEZONE)


def parse_pdc_datetime(value: str | date | datetime | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return ensure_pdc_timezone(value)

    if isinstance(value, date):
        return datetime.combine(value, PDC_BLOCK_TIMES[0], tzinfo=PDC_TIMEZONE)

    value = value.strip()
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            return None
        return datetime.combine(parsed_date, PDC_BLOCK_TIMES[0], tzinfo=PDC_TIMEZONE)

    if "T" not in value and len(value) == 10:
        parsed = datetime.combine(parsed.date(), PDC_BLOCK_TIMES[0])

    return ensure_pdc_timezone(parsed)


def next_valid_block(after: datetime) -> datetime:
    current = ensure_pdc_timezone(after)
    current_day = current.date()

    for block_time in PDC_BLOCK_TIMES:
        candidate = datetime.combine(current_day, block_time, tzinfo=PDC_TIMEZONE)
        if candidate >= current:
            return candidate

    return datetime.combine(
        current_day + timedelta(days=1),
        PDC_BLOCK_TIMES[0],
        tzinfo=PDC_TIMEZONE,
    )


def block_datetime_for_day(day: date, block_index: int, now: datetime) -> datetime:
    block_time = PDC_BLOCK_TIMES[min(block_index, len(PDC_BLOCK_TIMES) - 1)]
    candidate = datetime.combine(day, block_time, tzinfo=PDC_TIMEZONE)
    if candidate < now:
        return next_valid_block(now)
    return candidate


def chunk_emails_for_days(email_ids: list[str], days_count: int) -> list[list[str]]:
    days_count = max(1, min(days_count, len(email_ids)))
    chunks: list[list[str]] = [[] for _ in range(days_count)]

    for index, email_id in enumerate(email_ids):
        chunk_index = (index * days_count) // len(email_ids)
        chunks[chunk_index].append(email_id)

    return [chunk for chunk in chunks if chunk]


def build_pdc_email_schedule(
    fecha_inicio: datetime,
    fecha_llegada: datetime,
    now: datetime | None = None,
) -> list[ScheduledEmail]:
    now = ensure_pdc_timezone(now or datetime.now(PDC_TIMEZONE))
    start = max(ensure_pdc_timezone(fecha_inicio), now)
    start = next_valid_block(start)
    arrival = ensure_pdc_timezone(fecha_llegada)
    deadline = arrival - timedelta(days=10)

    if deadline <= start:
        return build_accelerated_schedule(start)

    start_day = start.date()
    deadline_day = deadline.date()
    available_days = (deadline_day - start_day).days + 1

    if available_days >= len(PDC_SCHEDULE_EMAIL_IDS):
        interval_days = max(1, available_days // len(PDC_SCHEDULE_EMAIL_IDS))
        schedule: list[ScheduledEmail] = []
        for index, email_id in enumerate(PDC_SCHEDULE_EMAIL_IDS):
            scheduled_day = min(
                start_day + timedelta(days=index * interval_days),
                deadline_day,
            )
            scheduled_at = block_datetime_for_day(scheduled_day, 0, now)
            schedule.append(
                ScheduledEmail(
                    email_id=email_id,
                    scheduled_at=scheduled_at,
                    bloque=f"bloque-{index + 1}",
                )
            )
        return schedule

    chunks = chunk_emails_for_days(PDC_SCHEDULE_EMAIL_IDS.copy(), available_days)
    schedule = []
    for day_index, email_ids in enumerate(chunks):
        scheduled_day = start_day + timedelta(days=day_index)
        scheduled_at = block_datetime_for_day(scheduled_day, 0, now)
        bloque = f"bloque-{day_index + 1}"
        for email_id in email_ids:
            schedule.append(
                ScheduledEmail(
                    email_id=email_id,
                    scheduled_at=scheduled_at,
                    bloque=bloque,
                )
            )
    return schedule


def build_accelerated_schedule(start: datetime) -> list[ScheduledEmail]:
    block_starts = [
        next_valid_block(start),
        next_valid_block(next_valid_block(start) + timedelta(minutes=1)),
        next_valid_block(
            next_valid_block(next_valid_block(start) + timedelta(minutes=1))
            + timedelta(minutes=1)
        ),
    ]
    grouped_email_ids = [
        ["02-mochila", "03-como-llegar"],
        ["04-como-vivir", "05-vida-practica"],
        ["06-recordatorio-final"],
    ]

    schedule: list[ScheduledEmail] = []
    for index, email_ids in enumerate(grouped_email_ids):
        bloque = f"bloque-{index + 1}"
        for email_id in email_ids:
            schedule.append(
                ScheduledEmail(
                    email_id=email_id,
                    scheduled_at=block_starts[index],
                    bloque=bloque,
                )
            )
    return schedule


def build_cm_tasks_from_schedule(
    schedule: list[ScheduledEmail],
    nombre: str,
    correo: str,
    whatsapp: str | None = None,
    servicio: str = "PDC",
) -> list[CMTask]:
    tasks: list[CMTask] = []
    blocks: dict[tuple[str, datetime], list[ScheduledEmail]] = {}

    for scheduled_email in schedule:
        key = (scheduled_email.bloque, scheduled_email.scheduled_at)
        blocks.setdefault(key, []).append(scheduled_email)

    for (_bloque, scheduled_at), emails in blocks.items():
        if len(emails) < 2:
            continue

        tasks.append(
            CMTask(
                nombre=nombre,
                correo=correo,
                whatsapp=whatsapp,
                servicio=servicio,
                motivo=f"Se enviaron {len(emails)} emails juntos",
                mensaje_sugerido=PDC_CM_MESSAGE,
                estado="Pendiente",
                fecha_sugerida=scheduled_at,
            )
        )

    return tasks
