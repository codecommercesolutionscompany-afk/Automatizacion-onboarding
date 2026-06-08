# Reporte de Cierre Técnico: Voluntariado Onboarding V1

## 1. Rama
`feature/voluntariado-onboarding-v1`

## 2. Objetivo del Desarrollo
Implementar el flujo de onboarding automatizado para participantes del programa de Voluntariado de Madre Selva, permitiendo el envío estructurado y programado de correos electrónicos, garantizando aislamiento total y seguridad para los programas existentes (PDC y Masterclass).

## 3. Arquitectura Creada
Se integró una arquitectura multi-servicio basada en la pre-existente para PDC, pero completamente desacoplada a nivel de endpoints y lógicas de programación (schedule). Se utiliza la columna `servicio` en Google Sheets para diferenciar el origen de los correos enviados y programados.

## 4. Commits Relevantes
- `docs: add voluntariado onboarding plan`
- `feat: add voluntariado onboarding email templates`
- `feat: add voluntariado email template mappings`
- `feat: add voluntariado schedule service`
- `feat: add voluntariado onboarding preview endpoint`
- `fix: remove voluntariado email confirmation links`
- `feat: add multi-service scheduled email routing`
- `feat: add voluntariado onboarding webhook`

## 5. Endpoints Nuevos
- `POST /api/v1/automatizacion/onboarding/voluntariado/preview-schedule`: Genera un preview en seco del cronograma para Voluntariado.
- `POST /api/v1/automatizacion/onboarding/voluntariado`: Endpoint principal (Webhook CRM) que procesa leads, envía el correo de bienvenida e inscribe el resto del cronograma en Sheets bajo el servicio `VOLUNTARIADO`.

## 6. Templates Creados
Ubicados en `app/emails/voluntariado/`:
1. `01-bienvenida-voluntariado.html`
2. `02-que-traer-voluntariado.html`
3. `03-como-llegar-voluntariado.html`
4. `04-vida-practica-convivencia-voluntariado.html`
5. `05-recordatorio-final-voluntariado.html`

## 7. Email IDs y Subjects
- `01-bienvenida-voluntariado`: "¡Bienvenido/a al Voluntariado en Madre Selva!"
- `02-que-traer-voluntariado`: "Voluntariado en Madre Selva: ¿Qué traer?"
- `03-como-llegar-voluntariado`: "Voluntariado en Madre Selva: ¿Cómo llegar?"
- `04-vida-practica-convivencia-voluntariado`: "Voluntariado en Madre Selva: Vida práctica y convivencia"
- `05-recordatorio-final-voluntariado`: "¡Nos vemos pronto en Madre Selva!"

## 8. Lógica de Schedule de Voluntariado
A diferencia de PDC, no envía los correos en bloques agrupados. Los correos se programan en horarios y días exactos en relación a la `fecha_llegada`:
- `-5 días a las 09:00`: 02-que-traer
- `-2 días a las 09:00`: 03-como-llegar
- `-1 día a las 09:00`: 04-vida-practica
- `-1 día a las 18:00`: 05-recordatorio

## 9. Cron Multi-servicio
La ruta `process_scheduled_emails` del cron se ha actualizado para interpretar dinámicamente la columna `servicio` proveniente de Apps Script. Si es `VOLUNTARIADO`, el enrutador central invoca internamente a `_send_voluntariado_email()`. Si es `PDC` o no viene servicio (retrocompatibilidad histórica), despacha a `_send_pdc_email()`.

## 10. Estado de Apps Script
- El servidor remoto ya reconoce los `email_id` de Voluntariado y no los bloquea gracias al parche aplicado.
- Validado con PowerShell: Se comprobó empíricamente contra `01-bienvenida-voluntariado`, resultando en un `status: not_found`, demostrando que el sistema acepta los identificadores.
- `claim_due_scheduled_emails` (doPost action) está preparado y devuelve debidamente la columna `servicio`.

## 11. Qué NO Está Activo Todavía
- ⚠️ No se ha hecho deploy (producción sigue limpia).
- ⚠️ No existe un Trigger CRM activo que alimente el nuevo webhook de Voluntariado.
- ⚠️ No se han enviado correos a destinatarios reales desde el entorno nuevo.
- ⚠️ Las confirmaciones de lectura para estos emails no están soportadas y se han inhabilitado temporalmente de los HTMLs.
- ⚠️ La rama no ha sido mergeada a `main`.

## 12. Riesgos Pendientes
- La variable `fecha_salida` se procesa y puede renderizarse, pero no tiene una columna persistente todavía confirmada en Google Sheets.
- Falta la primera **Prueba Real Interna** (impactando Resend y Google Sheets con credenciales no-mocked).
- Falta inyectar de manera segura y precisa el webhook dentro de la plataforma del CRM.
- Hay que hacer deploy para pasar de simulaciones locales al entorno productivo de Google Cloud / Servidor.

## 13. Validaciones Realizadas
- `python -m compileall app`: 100% exitoso.
- `python -m pytest`: 100% Passed.
- Mock Scripts sin Resend Real: Pruebas dry-run comprobando enrutamiento con éxito.
- Mock Scripts sin Sheets Real: Pruebas dry-run comprobando registros (emails enviados + programados sin crear tareas CM) con éxito.
- Comprobación PowerShell: Integración `check_sent_email` ratificada.

## 14. Estado de PDC
- **Endpoint Principal (`POST /api/v1/automatizacion/onboarding`)**: Intacto y sin alteraciones lógicas.
- **`schedule_service.py`**: Intacto. Fue revertido para garantizar nulo impacto a la generación de bloques y tareas de Community Manager exclusivas de PDC.
- **PDC Seguro**: Arquitectura estrictamente paralela.

## 15. Estado de Masterclass
- **No tocado**: Fuera del perímetro de modificaciones de esta rama.

## 16. Próximo Plan Recomendado
1. **Prueba Interna Real Controlada:** Correr el script conectando temporalmente a Resend/Sheets apuntando a cuentas del equipo interno.
2. **Deploy:** Despliegue de los binarios/código a Staging o Producción.
3. **Smoke Test Remoto:** Lanzar una petición manual desde Postman/cURL contra la URL pública a un email del equipo para validar integración completa.
4. **Trigger CRM Voluntariado:** Habilitar o crear la automatización real (ejemplo Zapier o CRM nativo) conectándola a `POST /api/v1/automatizacion/onboarding/voluntariado`.
5. **Test de Contacto Piloto:** Generar una alta manual real en el CRM para ratificar el Funnel de principio a fin.
6. **Merge to Main:** Integrar `feature/voluntariado-onboarding-v1` a la rama principal de manera segura.

## 17. Lista de Cosas Prohibidas (Hasta Autorización)
- ❌ Prohibido ejecutar acciones sobre base de datos / contactos reales.
- ❌ Prohibido invocar los crons de manera manual forzada contra perfiles no-test.
- ❌ Prohibido desplegar a producción sin orden explícita.
- ❌ Prohibido configurar triggers productivos en CRM sin previa comprobación en blanco.
