from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


try:
    VOLUNTARIADO_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
except ZoneInfoNotFoundError:
    VOLUNTARIADO_TIMEZONE = timezone(timedelta(hours=-3), "America/Argentina/Buenos_Aires")

VOLUNTARIADO_SCHEDULE_EMAIL_IDS = [
    "02-que-traer-voluntariado",
    "03-como-llegar-voluntariado",
    "04-vida-practica-convivencia-voluntariado",
    "05-recordatorio-final-voluntariado",
]

VOLUNTARIADO_EMAIL_OFFSETS = {
    "02-que-traer-voluntariado": {"days": 7, "time": time(9, 0)},
    "03-como-llegar-voluntariado": {"days": 5, "time": time(9, 0)},
    "04-vida-practica-convivencia-voluntariado": {"days": 3, "time": time(15, 0)},
    "05-recordatorio-final-voluntariado": {"days": 1, "time": time(9, 0)},
}

VOLUNTARIADO_BLOCK_TIMES = [time(9, 0), time(15, 0), time(18, 0)]


@dataclass(frozen=True)
class ScheduledEmailVoluntariado:
    email_id: str
    scheduled_at: datetime
    days_before_arrival: int
    send_time: str
    reason: str


def ensure_voluntariado_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=VOLUNTARIADO_TIMEZONE)
    return value.astimezone(VOLUNTARIADO_TIMEZONE)


def next_valid_block(after: datetime) -> datetime:
    current = ensure_voluntariado_timezone(after)
    current_day = current.date()

    for block_time in VOLUNTARIADO_BLOCK_TIMES:
        candidate = datetime.combine(current_day, block_time, tzinfo=VOLUNTARIADO_TIMEZONE)
        if candidate >= current:
            return candidate

    return datetime.combine(
        current_day + timedelta(days=1),
        VOLUNTARIADO_BLOCK_TIMES[0],
        tzinfo=VOLUNTARIADO_TIMEZONE,
    )


def get_available_blocks(start: datetime, end: datetime) -> list[datetime]:
    blocks = []
    current = next_valid_block(start)
    while current < end:
        blocks.append(current)
        current = next_valid_block(current + timedelta(minutes=1))
    return blocks


def build_voluntariado_schedule(
    fecha_llegada: datetime,
    now: datetime | None = None
) -> list[ScheduledEmailVoluntariado]:
    now = ensure_voluntariado_timezone(now or datetime.now(VOLUNTARIADO_TIMEZONE))
    llegada = ensure_voluntariado_timezone(fecha_llegada)
    llegada_date = llegada.date()
    
    if now >= llegada:
        return []

    # Bloque límite para cada email
    # El 05 no puede mandarse el mismo dia de la llegada (strictly before midnight of arrival day)
    max_datetime_for_email = {
        "02-que-traer-voluntariado": llegada,
        "03-como-llegar-voluntariado": llegada,
        "04-vida-practica-convivencia-voluntariado": llegada,
        "05-recordatorio-final-voluntariado": datetime.combine(llegada_date, time(0, 0), tzinfo=VOLUNTARIADO_TIMEZONE)
    }

    # Calcular fechas ideales
    ideal_schedule: dict[str, datetime] = {}
    for email_id in VOLUNTARIADO_SCHEDULE_EMAIL_IDS:
        offset = VOLUNTARIADO_EMAIL_OFFSETS[email_id]
        ideal_date = llegada_date - timedelta(days=offset["days"])
        ideal_datetime = datetime.combine(ideal_date, offset["time"], tzinfo=VOLUNTARIADO_TIMEZONE)
        ideal_schedule[email_id] = ideal_datetime

    # Lista de emails por prioridad estricta si falta tiempo
    priority_order = [
        "03-como-llegar-voluntariado",
        "05-recordatorio-final-voluntariado",
        "02-que-traer-voluntariado",
        "04-vida-practica-convivencia-voluntariado"
    ]
    
    schedule_dict: dict[str, tuple[datetime, str]] = {}
    assigned_blocks = set()

    for email_id in priority_order:
        ideal = ideal_schedule[email_id]
        max_dt = max_datetime_for_email[email_id]
        
        # Intentar bloque ideal
        if ideal >= now and ideal < max_dt and ideal not in assigned_blocks:
            schedule_dict[email_id] = (ideal, "ideal")
            assigned_blocks.add(ideal)
            continue
            
        # Si el ideal no se puede, buscar el bloque libre más cercano
        current_candidate = next_valid_block(now)
        assigned = False
        
        while current_candidate < max_dt:
            if current_candidate not in assigned_blocks:
                schedule_dict[email_id] = (current_candidate, "acelerado")
                assigned_blocks.add(current_candidate)
                assigned = True
                break
            current_candidate = next_valid_block(current_candidate + timedelta(minutes=1))
            
        if not assigned:
            # El correo se descarta (no hay bloques disponibles antes del limite)
            pass

    # Reconstruir la lista final ordenada
    final_schedule: list[ScheduledEmailVoluntariado] = []
    
    # Ordenar por fecha cronologica de envio
    items = [(email_id, dt, reason) for email_id, (dt, reason) in schedule_dict.items()]
    items.sort(key=lambda x: x[1])
    
    for email_id, dt, reason in items:
        days_before = (llegada_date - dt.date()).days
        final_schedule.append(
            ScheduledEmailVoluntariado(
                email_id=email_id,
                scheduled_at=dt,
                days_before_arrival=days_before,
                send_time=dt.strftime("%H:%M"),
                reason=reason
            )
        )

    return final_schedule
