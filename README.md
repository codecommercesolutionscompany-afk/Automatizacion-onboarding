# Automatizacion Onboarding PDC

Backend FastAPI para centralizar la automatizacion de onboarding del PDC de Madre Selva. Este proyecto recibe webhooks desde CRM/Sheet, valida si el lead aplica, renderiza templates HTML locales, envia emails usando Resend y registra los envios correctos en Google Sheets via Apps Script.

La logica de emails vive aca: templates HTML, reemplazo de variables, envio por Resend y futuras automatizaciones.

## Requisitos

- Python 3.12+
- Cuenta/API key de Resend

## Variables de entorno

Crear un archivo `.env` local usando `.env.example` como base:

```env
RESEND_API_KEY=
RESEND_FROM_EMAIL=
PDC_CONFIRMATION_URL=
PDC_SHEET_WEBHOOK_URL=
```

`PDC_CONFIRMATION_URL` es opcional y se usa para reemplazar `[PEGAR_LINK_DE_CONFIRMACION]` cuando el HTML todavia no trae el link armado con `{{CORREO}}`.

`PDC_SHEET_WEBHOOK_URL` permite registrar en Google Sheets los emails enviados correctamente.

## Correr local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs locales:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Endpoints

### Webhook de onboarding

```http
POST /api/v1/automatizacion/onboarding
```

Ejemplo:

```json
{
  "nombre": "Nombre del lead",
  "email": "persona@email.com",
  "estado": "cerrado",
  "producto": "PDC"
}
```

Reglas:

- Si `estado != cerrado`, devuelve `ignored`.
- Si `producto != PDC`, devuelve `ignored`.
- Si faltan `nombre` o `email`, devuelve `alert`.
- Si aplica, envia el email `01-bienvenida`.

### Envio manual de email

```http
POST /api/v1/automatizacion/onboarding/send-email
```

Ejemplo:

```json
{
  "nombre": "Nombre del participante",
  "email": "persona@email.com",
  "email_id": "02-mochila"
}
```

Respuesta esperada:

```json
{
  "status": "sent",
  "email": "persona@email.com",
  "email_id": "02-mochila"
}
```

## Templates HTML

Los HTML del onboarding PDC van en:

```text
app/emails/pdc/
```

IDs disponibles:

- `01-bienvenida` -> `01-bienvenida-pdc.html`
- `02-mochila` -> `02-mochila-pdc.html`
- `03-como-llegar` -> `03-como-llegar-pdc.html`
- `04-como-vivir` -> `04-como-vivir-pdc.html`
- `05-vida-practica` -> `05-vida-practica-pdc.html`
- `06-recordatorio-final` -> `06-ultimo-recordatorio-pdc.html`

Tambien puede vivir aca `sequence.json` cuando se incorpore la automatizacion de secuencia.

Placeholders soportados:

- `{{NOMBRE}}`
- `{{CORREO}}`
- `[PEGAR_LINK_DE_CONFIRMACION]`

## Docker

Build:

```bash
docker build -t automatizacion-onboarding .
```

Run:

```bash
docker run --env-file .env -p 8000:8000 automatizacion-onboarding
```

El `Dockerfile` es compatible con Render y usa `PORT` cuando la plataforma lo provee.

## Validacion

```bash
python -m compileall app
uvicorn app.main:app --reload
```
