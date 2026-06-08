# Reporte de Cierre: Integración CRM Voluntariado Onboarding

## 1. Contexto
- Voluntariado Onboarding V1 ya se encontraba desplegado y en producción.
- Previamente se validó el correcto funcionamiento del endpoint real, Resend, Apps Script y Sheets.
- La fase actual documentada en este reporte corresponde a la conexión del disparo automático desde el CRM al cambiar el estado del lead.

## 2. Columnas CRM Confirmadas
**Headers originales:**
Nombre, Instagram, Whatsapp, Correo, Etapa, Fecha 1° contacto, Servicio, Fecha reserva, Fecha llegada, $ pago reserva, $ pago saldo, Próx. acción, Fecha de próx acción, Observaciones, Valor, Masterclass acceso enviado, Fecha envío acceso, Masterclass acceso confirmado, Fecha confirmación masterclass.

**Columnas agregadas para el flujo:**
- Fecha salida
- Voluntariado onboarding enviado
- Fecha envío onboarding voluntariado
- Error onboarding voluntariado

## 3. Condición de Disparo
El trigger de Apps Script evalúa las siguientes condiciones para iniciar el flujo:
- `Servicio` = Voluntariado
- `Etapa` = Cerrado/Venta
- `Nombre` completo
- `Correo` completo
- `Fecha llegada` completa
- `Voluntariado onboarding enviado` está vacío (evita dobles envíos)

## 4. Ajuste Técnico Realizado
- Se optó por reutilizar el trigger principal ya existente para PDC (`handlePdcCrmEdit`).
- Se agregó una llamada segura a la función de voluntariado (`handleVoluntariadoCrmEdit_(e)`) al inicio de dicho trigger.
- PDC mantiene su lógica original intacta.
- El script de Voluntariado posee guardas lógicas (`guard clauses`) internas estrictas para no afectar en absoluto el flujo de PDC.

## 5. Problema Detectado y Corrección
- **Problema:** En el intento inicial el webhook no se disparó porque el trigger activo nativo de Google Sheets apuntaba a `handlePdcCrmEdit` y no al nuevo handler individual de Voluntariado.
- **Corrección:** Se integró la llamada a Voluntariado dentro de la función principal `handlePdcCrmEdit`. Adicionalmente, se ajustó la validación de la columna "Etapa" para que soporte el valor exacto de la lista desplegable: `Cerrado/Venta`.

## 6. Prueba Manual Previa
Antes de probar la edición en vivo en la hoja, se ejecutó una prueba de bajo nivel (`testVoluntariadoOnboardingFilaFake`):
- El Backend respondió `HTTP 200`.
- `status`: sent.
- `email_sent`: true.
- `sheet_registered`: true.
- `scheduled_count`: 4.
- `scheduled_registered_count`: 4.
- `cm_tasks_count`: 0.
- El correo fue recibido en la bandeja de prueba.
- El CRM (Google Sheets) marcó correctamente el checkbox de enviado.

## 7. Prueba Automática con Trigger
- Se modificó una fila "fake" cambiando su Etapa a `Cerrado/Venta`.
- El trigger `handlePdcCrmEdit` reaccionó al evento `onEdit`.
- El flujo específico de Voluntariado se disparó correctamente hacia el backend en Render.
- Se envió el email de bienvenida E2E.
- Se registraron los emails programados en la hoja general de envíos.
- Se autocompletaron las celdas del CRM (marcando "Voluntariado onboarding enviado").
- PDC no sufrió ningún tipo de alteración.

## 8. Estado Final
- Flujo E2E validado: **CRM → Apps Script → Backend → Resend → Sheets → CRM funcionando.**
- El sistema está listo para dar luz verde a la operación real controlada.
- El cron (planificador de correos diferidos) aún no se ha ejecutado en esta fase.
- No se realizaron pruebas utilizando contactos reales para proteger el proceso.

## 9. Recomendación Operativa
- Antes de liberar la automatización para el equipo de ventas, ejecutar una **última prueba manual** con una fila fake totalmente limpia.
- Tras el éxito de esa prueba, habilitar el uso real ingresando **únicamente 1 lead real de forma controlada**.
- Durante las primeras semanas de operación, mantener revisión de las pestañas `PDC_Email_Envios` y `PDC_Email_Programacion` para supervisar el correcto enrutamiento multi-servicio de los primeros inscriptos al Voluntariado.
