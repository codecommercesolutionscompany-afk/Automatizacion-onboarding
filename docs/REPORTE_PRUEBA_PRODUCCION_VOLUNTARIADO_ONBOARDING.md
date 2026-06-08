# Reporte de Prueba Real en Producción: Voluntariado Onboarding

## 1. Contexto de la Prueba
- Rama feature `feature/voluntariado-onboarding-v1` mergeada exitosamente a `main`.
- Backend productivo desplegado automáticamente en Render.
- El endpoint fue probado en el entorno de producción.
- La prueba se realizó exclusivamente con un correo electrónico interno, sin involucrar contactos reales del CRM.

## 2. Endpoint Probado
- **POST** `/api/v1/automatizacion/onboarding/voluntariado`

## 3. Payload Usado
```json
{
  "nombre": "Prueba Voluntariado",
  "email": "neyenfrandino1+voluntariado-test@gmail.com",
  "whatsapp": "+5491122334455",
  "estado": "Cerrado",
  "producto": "VOLUNTARIADO",
  "fecha_reserva": "2026-06-08T10:00:00",
  "fecha_llegada": "2026-06-25T14:00:00",
  "fecha_salida": "2026-06-30T08:00:00"
}
```

## 4. Resultado del Primer Envío Real
- El correo llegó exitosamente a la cuenta de Gmail de prueba.
- El correo no apareció en la bandeja "Principal" directamente, pero se localizó al buscar por palabras clave (requiere monitoreo de reputación de dominio).
- Resend aceptó y procesó el envío correctamente.
- El Backend respondió con `status: sent`.
- `email_sent: true`.
- `scheduled_count: 4`.
- `cm_tasks_count: 0`.

## 5. Problema Inicial Detectado
- A pesar de que el email se envió y el backend reportó éxito, inicialmente **no aparecieron registros en Google Sheets**.
- Al consultar directamente con la función `check_sent_email`, esta devolvía `not_found`.
- **Diagnóstico:** El script de Google Apps Script había sido guardado con la lógica nueva, pero el deployment activo (la URL `/exec` conectada a Render) no estaba actualizado con la última versión del código.

## 6. Corrección Aplicada en Apps Script
- Se generó una actualización del deployment (`Nueva implementación`) en Apps Script asegurando que el código ejecutado en la URL `/exec` fuera el más reciente, manteniendo la misma URL.
- Se realizó una prueba directa de `register_sent_email` que funcionó correctamente.
- Posteriormente, `check_sent_email` validó correctamente devolviendo `duplicate` / `exists: true`.

## 7. Validación de Programados
- Se ejecutó una prueba directa de `register_scheduled_email` inyectando manualmente `02-que-traer-voluntariado`.
- Resultado: `status: registered`.
- Se verificó la creación exitosa de la fila en la pestaña `PDC_Email_Programacion` bajo el Servicio `VOLUNTARIADO`.

## 8. Segunda Prueba del Webhook Real
Al volver a enviar el mismo payload al webhook de producción, la respuesta obtenida fue:
- `status: already_sent`
- `email_sent: False`
- `sheet_registered: False`
- `scheduled_count: 4`
- `scheduled_registered_count: 3`
- `scheduled_duplicate_count: 1`
- `cm_tasks_count: 0`
- `cm_tasks_duplicate_count: 0`

**Interpretación del comportamiento:**
- El sistema evitó reenviar el correo de bienvenida (`01-bienvenida-voluntariado`) detectándolo como duplicado exitosamente.
- Detectó como duplicado el correo programado `02` (cargado manualmente en el paso anterior).
- Registró correctamente los correos programados pendientes (`03`, `04` y `05`).
- Confirmó la nula creación de tareas para el Community Manager (`cm_tasks_count: 0`).

## 9. Validación Final
Se confirma de manera definitiva que:
- `PDC_Email_Envios` contiene el registro de `01-bienvenida-voluntariado` etiquetado con Servicio `VOLUNTARIADO`.
- `PDC_Email_Programacion` contiene los registros `02`, `03`, `04` y `05` de Voluntariado.
- `PDC_Tareas_CM` se mantiene limpia, sin nuevas tareas asociadas a Voluntariado.
- **No** se ejecutó el endpoint `process-scheduled-emails`.
- **No** se creó ni activó el trigger del CRM.
- **No** se interactuó con contactos reales.
- Los flujos operativos de **PDC y Masterclass continúan intactos** y protegidos.

## 10. Estado Final
- **Prueba productiva interna EXITOSA.**
- La integración completa (Backend + Resend + Apps Script + Sheets) está validada y funcionando en producción para el flujo de Voluntariado.
- La arquitectura está lista para la fase de integración con el CRM.
- *Nota:* Mantener inactivo el cronograma y evitar el uso de contactos reales hasta completar el siguiente paso.

## 11. Próximo Paso Recomendado
- **Diseñar el trigger CRM para Voluntariado:**
  - Definir el mapeo exacto de columnas desde el CRM hacia el webhook: `producto`, `estado`, `fecha_llegada`, `fecha_salida`, `nombre`, `email`, `whatsapp`.
  - Configurar y probar el trigger utilizando una fila simulada (fake lead) dentro del CRM.
  - Únicamente tras validar el flujo automatizado desde el CRM, habilitar la operación real para los usuarios finales.
