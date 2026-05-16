import os
from html import escape
from typing import Any

import resend
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator


app = FastAPI(
    title="Automatizacion Onboarding PDC",
    description="Webhook para disparar emails automaticos de onboarding desde CRM.",
    version="1.0.0",
)


class LeadCRM(BaseModel):
    """Payload recibido desde el Sheet/CRM cuando cambia el estado de una tarjeta."""

    nombre: str | None = None
    email: EmailStr | None = None
    estado: str
    producto: str

    @field_validator("nombre", "email", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        """Convierte celdas vacias del Sheet en None para poder responder con alerta."""
        if isinstance(value, str) and not value.strip():
            return None
        return value


def get_missing_contact_fields(lead: LeadCRM) -> list[str]:
    """Detecta datos minimos faltantes para enviar el onboarding."""
    missing_fields: list[str] = []

    if not lead.nombre or not lead.nombre.strip():
        missing_fields.append("nombre")

    if not lead.email:
        missing_fields.append("email")

    return missing_fields


def build_onboarding_email_html(nombre: str) -> str:
    """Construye el cuerpo HTML personalizado del onboarding Madre Selva."""
    nombre_seguro = escape(nombre.strip())

    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Guía para preparar tu mochila - Madre Selva</title>
</head>
<body style="margin:0; padding:0; background:#F7F1E7; font-family:Inter, Arial, sans-serif; color:#26312D;">
  <!-- Preheader oculto -->
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
    Una lista simple, amorosa y completa para llegar a Madre Selva con lo necesario.
  </div>

  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F7F1E7; margin:0; padding:0;">
    <tr>
      <td align="center" style="padding:24px 12px;">

        <!-- Contenedor principal -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:640px; background:#FFFFFF; border-radius:24px; overflow:hidden; border:1px solid #E3D8C8;">

          <!-- Barra superior -->
          <tr>
            <td style="background:#2F5249; padding:16px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="left" style="font-size:12px; letter-spacing:1.5px; text-transform:uppercase; color:#F7F1E7; font-weight:700;">
                    Madre Selva · Antes de llegar
                  </td>
                  <td align="right" style="font-size:12px; color:#D5A04A; font-weight:700;">
                    Onboarding
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Hero -->
          <tr>
            <td style="padding:36px 32px 24px 32px; background:#FFFFFF;">
              <div style="display:inline-block; background:#EFE7DA; color:#A4633A; font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; padding:8px 14px; border-radius:999px;">
                Guía para preparar tu mochila
              </div>
              <h1 style="margin:18px 0 12px 0; font-family:Georgia, 'Times New Roman', serif; font-size:34px; line-height:1.08; color:#2F5249; font-weight:700;">
                Hola {nombre_seguro}, prepará tu mochila con intención
              </h1>
              <p style="margin:0; font-size:17px; line-height:1.65; color:#26312D;">
                Una lista simple, amorosa y completa para llegar a Madre Selva con lo necesario para trabajar, aprender, descansar y compartir en comunidad.
              </p>
            </td>
          </tr>

          <!-- Frase clave -->
          <tr>
            <td style="padding:0 32px 26px 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F7F1E7; border-left:5px solid #D5A04A; border-radius:16px;">
                <tr>
                  <td style="padding:20px 22px;">
                    <p style="margin:0; font-family:Georgia, 'Times New Roman', serif; font-size:21px; line-height:1.4; color:#2F5249;">
                      “Preparar bien tu mochila también es parte del viaje.”
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Introducción -->
          <tr>
            <td style="padding:0 32px 28px 32px;">
              <p style="margin:0 0 14px 0; font-size:15.5px; line-height:1.7; color:#26312D;">
                Durante estos días vamos a aprender haciendo, caminar la tierra, usar las manos, registrar ideas, convivir y habitar la naturaleza de forma simple y consciente.
              </p>
              <p style="margin:0; font-size:15.5px; line-height:1.7; color:#26312D;">
                Traé lo necesario para estar cómodo/a, presente y disponible para vivir la experiencia completa.
              </p>
            </td>
          </tr>

          <!-- Aviso clima -->
          <tr>
            <td style="padding:0 32px 30px 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#FFF8E8; border:1px solid #E8D6A8; border-radius:18px;">
                <tr>
                  <td style="padding:22px;">
                    <p style="margin:0 0 8px 0; color:#A4633A; font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">
                      Aviso importante sobre el clima en Misiones
                    </p>
                    <p style="margin:0; color:#26312D; font-size:15px; line-height:1.65;">
                      Aunque vamos a estar en Misiones, durante esta época puede hacer frío, especialmente por la noche, a la madrugada y en los momentos de descanso. Traé abrigo suficiente: buzo, campera, medias gruesas, pantalón largo cómodo y ropa térmica si tenés.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Sección 1 -->
          <tr>
            <td style="padding:0 32px 18px 32px;">
              <h2 style="margin:0 0 12px 0; font-family:Georgia, 'Times New Roman', serif; font-size:24px; color:#2F5249;">
                01 · Para trabajar con la tierra y las manos
              </h2>
              <p style="margin:0 0 14px 0; color:#26312D; font-size:15px; line-height:1.6;">
                Habrá momentos de práctica, movimiento y trabajo al aire libre. Vení con ropa y herramientas que te permitan participar con libertad.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td width="50%" style="padding:6px 8px 6px 0; font-size:15px;">✓ Botas de lluvia</td>
                  <td width="50%" style="padding:6px 0 6px 8px; font-size:15px;">✓ Ropa de trabajo</td>
                </tr>
                <tr>
                  <td style="padding:6px 8px 6px 0; font-size:15px;">✓ Guantes</td>
                  <td style="padding:6px 0 6px 8px; font-size:15px;">✓ Cinta para medir</td>
                </tr>
                <tr>
                  <td style="padding:6px 8px 6px 0; font-size:15px;">✓ Pinzas</td>
                  <td style="padding:6px 0 6px 8px; font-size:15px;">✓ Martillo</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Separador -->
          <tr><td style="padding:10px 32px;"><div style="height:1px; background:#E6DACB;"></div></td></tr>

          <!-- Sección 2 -->
          <tr>
            <td style="padding:18px 32px;">
              <h2 style="margin:0 0 12px 0; font-family:Georgia, 'Times New Roman', serif; font-size:24px; color:#2F5249;">
                02 · Para acampar y descansar bien
              </h2>
              <p style="margin:0 0 14px 0; color:#26312D; font-size:15px; line-height:1.6;">
                Vas a estar viviendo en contacto directo con la naturaleza. Por eso es muy importante venir preparado/a para acampar y dormir con abrigo.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td width="50%" style="padding:6px 8px 6px 0; font-size:15px;">✓ Carpa</td>
                  <td width="50%" style="padding:6px 0 6px 8px; font-size:15px;">✓ Elementos para acampar</td>
                </tr>
                <tr>
                  <td style="padding:6px 8px 6px 0; font-size:15px;">✓ Bolsa de dormir abrigada</td>
                  <td style="padding:6px 0 6px 8px; font-size:15px;">✓ Ropa para el frío</td>
                </tr>
              </table>
              <div style="margin-top:16px; background:#2F5249; border-radius:16px; padding:18px 20px;">
                <p style="margin:0 0 6px 0; color:#D5A04A; font-size:13px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">
                  Muy importante
                </p>
                <p style="margin:0; color:#F7F1E7; font-size:15px; line-height:1.6;">
                  El cobertor o bolsa de dormir son fundamentales. No contamos con cobertores, mantas ni bolsas de dormir para prestar o alquilar.
                </p>
              </div>
            </td>
          </tr>

          <!-- Sección 3 -->
          <tr>
            <td style="padding:18px 32px; background:#FBF7F0;">
              <h2 style="margin:0 0 12px 0; font-family:Georgia, 'Times New Roman', serif; font-size:24px; color:#2F5249;">
                03 · Para aprender, registrar y crear
              </h2>
              <p style="margin:0 0 14px 0; color:#26312D; font-size:15px; line-height:1.6;">
                También habrá momentos para observar, escribir, diseñar, dibujar y bajar ideas al papel.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td width="50%" style="padding:6px 8px 6px 0; font-size:15px;">✓ Computadora</td>
                  <td width="50%" style="padding:6px 0 6px 8px; font-size:15px;">✓ Cuaderno</td>
                </tr>
                <tr>
                  <td style="padding:6px 8px 6px 0; font-size:15px;">✓ Colores</td>
                  <td style="padding:6px 0 6px 8px; font-size:15px;">✓ Regla</td>
                </tr>
                <tr>
                  <td style="padding:6px 8px 6px 0; font-size:15px;">✓ Lápices</td>
                  <td style="padding:6px 0 6px 8px; font-size:15px;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Sección 4 y 5 -->
          <tr>
            <td style="padding:28px 32px 18px 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td width="50%" valign="top" style="padding:0 10px 0 0;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F7F1E7; border-radius:18px;">
                      <tr>
                        <td style="padding:20px;">
                          <h3 style="margin:0 0 10px 0; font-family:Georgia, 'Times New Roman', serif; font-size:20px; color:#2F5249;">
                            04 · Comunidad
                          </h3>
                          <p style="margin:0; font-size:14.5px; line-height:1.55; color:#26312D;">
                            ✓ Cosas para el club de trueque<br>
                            ✓ Juego de mate, si tenés
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="50%" valign="top" style="padding:0 0 0 10px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F7F1E7; border-radius:18px;">
                      <tr>
                        <td style="padding:20px;">
                          <h3 style="margin:0 0 10px 0; font-family:Georgia, 'Times New Roman', serif; font-size:20px; color:#2F5249;">
                            05 · Cuidado personal
                          </h3>
                          <p style="margin:0; font-size:14.5px; line-height:1.55; color:#26312D;">
                            ✓ Productos de aseo personal, preferentemente biodegradables.
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Sección último día -->
          <tr>
            <td style="padding:10px 32px 30px 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F4EEE4; border-radius:18px; border:1px solid #E5D7C8;">
                <tr>
                  <td style="padding:22px;">
                    <h2 style="margin:0 0 10px 0; font-family:Georgia, 'Times New Roman', serif; font-size:24px; color:#2F5249;">
                      06 · Para el último día
                    </h2>
                    <p style="margin:0; font-size:15px; line-height:1.6; color:#26312D;">
                      Para el cierre de la experiencia, traé una ropa especial y guardala limpia para ese momento.
                    </p>
                    <p style="margin:12px 0 0 0; font-size:16px; line-height:1.6; color:#A4633A; font-weight:800;">
                      ✓ Ropa blanca
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Checklist -->
          <tr>
            <td style="padding:0 32px 34px 32px;">
              <h2 style="margin:0 0 14px 0; font-family:Georgia, 'Times New Roman', serif; font-size:26px; color:#2F5249;">
                Checklist rápido antes de salir
              </h2>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px solid #E4D6C7; border-radius:18px; overflow:hidden;">
                <tr>
                  <td width="50%" style="background:#F7F1E7; padding:18px; font-size:14.5px; line-height:1.8;">
                    □ Botas de lluvia<br>
                    □ Ropa de trabajo<br>
                    □ Guantes<br>
                    □ Cinta para medir<br>
                    □ Pinzas<br>
                    □ Martillo<br>
                    □ Carpa<br>
                    □ Elementos para acampar
                  </td>
                  <td width="50%" style="background:#FBF7F0; padding:18px; font-size:14.5px; line-height:1.8;">
                    □ Bolsa de dormir abrigada<br>
                    □ Ropa para el frío<br>
                    □ Computadora<br>
                    □ Cuaderno<br>
                    □ Colores / regla / lápices<br>
                    □ Club de trueque<br>
                    □ Juego de mate<br>
                    □ Ropa blanca<br>
                    □ Aseo biodegradable
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- CTA -->
          <tr>
            <td align="center" style="padding:0 32px 36px 32px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="background:#A4633A; border-radius:999px;">
                    <a href="https://movimientonaluum.org/" target="_blank" style="display:inline-block; padding:15px 28px; color:#FFFFFF; text-decoration:none; font-size:15px; font-weight:800;">
                      Ver información de la experiencia
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:18px 0 0 0; color:#627467; font-size:13.5px; line-height:1.5;">
                Tu mochila es el primer paso para entrar en la experiencia.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#2F5249; padding:24px 32px;">
              <p style="margin:0 0 8px 0; color:#F7F1E7; font-size:15px; font-weight:800;">
                Movimiento Ná Lu'um · Madre Selva
              </p>
              <p style="margin:0; color:#DAD3C7; font-size:13px; line-height:1.5;">
                Educación viva, territorio y comunidad para aprender a regenerar desde la práctica.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def build_onboarding_email_text(nombre: str) -> str:
    """Construye una version de texto puro como fallback del email HTML."""
    return (
        f"Hola {nombre.strip()},\n\n"
        "Te compartimos la guia para preparar tu mochila antes de llegar a "
        "Madre Selva.\n\n"
        "Recorda traer ropa de trabajo, botas de lluvia, guantes, elementos "
        "para acampar, bolsa de dormir abrigada, ropa para el frio, cuaderno, "
        "computadora si la usas, elementos de aseo personal y ropa blanca para "
        "el ultimo dia.\n\n"
        "Ver informacion de la experiencia: https://movimientonaluum.org/\n\n"
        "Movimiento Na Lu'um - Madre Selva"
    )


def send_onboarding_email(lead: LeadCRM) -> dict[str, Any]:
    """Envia el email de onboarding usando la API oficial de Resend."""
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")

    if not resend_api_key or not from_email:
        raise RuntimeError("Faltan RESEND_API_KEY o RESEND_FROM_EMAIL.")

    resend.api_key = resend_api_key

    return resend.Emails.send(
        {
            "from": from_email,
            "to": [str(lead.email)],
            "subject": "Guia para preparar tu mochila - Madre Selva",
            "html": build_onboarding_email_html(lead.nombre or ""),
            "text": build_onboarding_email_text(lead.nombre or ""),
        }
    )


@app.post("/api/v1/automatizacion/onboarding")
def onboarding_webhook(lead: LeadCRM) -> dict[str, Any]:
    """Procesa el webhook del CRM y dispara onboarding si el lead califica."""
    estado_normalizado = lead.estado.strip().lower()
    producto_normalizado = lead.producto.strip().upper()

    # Ignora leads que todavia no estan cerrados o que no corresponden a PDC.
    if estado_normalizado != "cerrado" or producto_normalizado != "PDC":
        return {
            "status": "ignored",
            "message": "Lead ignorado: no cumple las condiciones de onboarding.",
        }

    # Si el Sheet no trae nombre o email, no se envia y se devuelve alerta para PM/Sheet.
    missing_fields = get_missing_contact_fields(lead)
    if missing_fields:
        return {
            "status": "alert",
            "message": "No se envio el onboarding porque faltan datos obligatorios.",
            "alert_for": "pm_sheet",
            "missing_fields": missing_fields,
        }

    # Dispara el email y convierte cualquier error de Resend/configuracion en HTTP 500.
    try:
        response = send_onboarding_email(lead)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el email de onboarding.",
        ) from exc

    return {
        "status": "sent",
        "message": "Email de onboarding enviado correctamente.",
        "resend_response": response,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
