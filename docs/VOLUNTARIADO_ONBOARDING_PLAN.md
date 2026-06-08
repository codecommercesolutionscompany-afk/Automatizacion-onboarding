# Plan de Onboarding para Voluntariado (v1)

Este documento describe la fase inicial y el diseño del flujo de onboarding automático para Voluntariado, con una estructura inspirada en PDC, pero adaptada a Voluntariado.

## 1. Objetivo del flujo Voluntariado
Proveer una secuencia automatizada de correos electrónicos a los nuevos voluntarios de Madre Selva. El sistema deberá procesar webhooks entrantes desde el CRM, enviar un correo de bienvenida inmediato y programar una secuencia espaciada de correos con información vital antes de su fecha de llegada.

## 2. Qué se reutiliza de PDC
- **Servicio de envío (`resend_service.py`)**: Totalmente reutilizable.
- **Conexión con Google Sheets (`sheet_service.py`)**: Reutilizable, pasando `servicio="Voluntariado"` en lugar de `"PDC"`.
- **Estructura de payload**: Se reutiliza el schema `LeadWebhookPayload`.
- **Modelo de Cron y Tareas de Community Manager**: El motor base que reclama correos "debidos" y los manda.

## 3. Qué se crea separado
- **Templates de Email**: Nueva carpeta `/app/emails/voluntariado/` con archivos HTML propios.
- **Schedule Service para Voluntariado**: Un nuevo archivo (ej. `app/services/voluntariado_schedule.py`) o una abstracción cuidadosa para no modificar los bloques y días duros (`PDC_BLOCK_TIMES`, etc.) de PDC.
- **Configuración de Templates**: Mapeos y subjects separados para Voluntariado en `email_templates.py`.

## 4. Secuencia propuesta de emails
Se propone una secuencia reducida a 5 emails:
1. 01-bienvenida-voluntariado (Inmediato)
2. 02-que-traer-voluntariado (Programado)
3. 03-como-llegar-voluntariado (Programado)
4. 04-vida-practica-convivencia-voluntariado (Programado)
5. 05-recordatorio-final-voluntariado (Programado)

## 5. Email IDs propuestos
- `01-bienvenida-voluntariado`
- `02-que-traer-voluntariado`
- `03-como-llegar-voluntariado`
- `04-vida-practica-convivencia-voluntariado`
- `05-recordatorio-final-voluntariado`

## 6. Subjects propuestos
- `01-bienvenida-voluntariado`: Bienvenido/a al Voluntariado en Madre Selva
- `02-que-traer-voluntariado`: Qué traer para tu voluntariado en Madre Selva
- `03-como-llegar-voluntariado`: Cómo llegar a Madre Selva
- `04-vida-practica-convivencia-voluntariado`: Vida práctica, tareas y convivencia durante el voluntariado
- `05-recordatorio-final-voluntariado`: Último recordatorio antes de tu llegada

## 7. Variables dinámicas necesarias
- `{{NOMBRE}}`
- `{{CORREO}}`
- `{{WHATSAPP}}`
- `{{FECHA_LLEGADA}}`
- `{{FECHA_SALIDA}}`
- `{{SERVICIO}}`
- `{{LUGAR}}`
- `{{HORARIO_COLABORACION}}`
- `{{APORTE}}`
- `{{LINK_CONFIRMACION}}`
- `{{LINK_COMO_LLEGAR}}`

## 8. Payload esperado
Se espera el mismo objeto de entrada en el webhook:
```json
{
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "whatsapp": "+5491122334455",
  "producto": "VOLUNTARIADO",
  "estado": "Cerrado",
  "fecha_reserva": "2026-06-08T10:00:00",
  "fecha_llegada": "2026-06-25T14:00:00"
}
```

## 9. Hojas/acciones de Google Sheets necesarias
Antes de integrar Voluntariado, hay que auditar si las acciones actuales del Apps Script soportan diferenciar por `servicio="Voluntariado"`:
- `check_sent_email`
- `register_email_sent`
- `register_scheduled_email`
- `register_cm_task`
- `claim_due_scheduled_emails`

## 10. Archivos candidatos a tocar
- `app/routes/onboarding.py` (Para interceptar `producto == "VOLUNTARIADO"` o crear un endpoint `/voluntariado` gemelo).
- `app/services/email_templates.py` (Para mapear los nuevos IDs y HTMLs).
- `app/services/schedule_service.py` (Extraer la lógica genérica sin romper PDC, o crear `voluntariado_schedule.py`).

## 11. Archivos prohibidos
- **Masterclass completo**: `app/routes/masterclass.py`, `app/services/masterclass_service.py`, `app/emails/masterclass/`.
- **Variables de entorno (.env)**: No tocar.
- **Lógica productiva de PDC**: Prohibido tocar, salvo una derivación mínima autorizada.

## 12. Riesgos y Reglas explícitas
- **REGLA EXPLÍCITA**: No modificar `claim_due_scheduled_emails` ni la lógica productiva de PDC hasta confirmar que el Apps Script puede diferenciar por servicio sin romper registros existentes.
- **Alteración de fechas en PDC**: Si se modifica `schedule_service.py` de forma descuidada, los "bloques horarios" y el "chunkeo" de PDC pueden romperse.

## 13. Plan por fases e Implementación real
La primera implementación real debe ser:
1. Crear templates HTML.
2. Crear mapeos de email IDs y subjects.
3. Crear preview/dry-run de Voluntariado.
4. Recién después de lo anterior, conectar el webhook real.

## 14. Validaciones antes de enviar
Antes de despachar/programar:
- `lead.nombre` no debe ser nulo.
- `lead.email` debe ser válido.
- `lead.fecha_llegada` debe ser una fecha ISO válida.

## 15. Estrategia de preview/dry-run
- Crear o adaptar un endpoint `POST /api/v1/automatizacion/onboarding/preview-schedule-voluntariado`.
- Hacer peticiones POST locales para verificar visualmente que las fechas y bloques generados coinciden con los requerimientos esperados.
