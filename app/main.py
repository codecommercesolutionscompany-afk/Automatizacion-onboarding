import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.routes.masterclass import router as masterclass_router
from app.routes.onboarding import router as onboarding_router


app = FastAPI(
    title="Automatizacion Onboarding PDC",
    description="Webhook y envio manual de emails de onboarding para Madre Selva.",
    version="1.0.0",
)

app.include_router(onboarding_router)
app.include_router(masterclass_router)


@app.get("/debug/env")
def debug_env() -> dict:
    return {
        "RESEND_API_KEY_exists": bool(settings.resend_api_key),
        "RESEND_FROM_EMAIL_exists": bool(settings.resend_from_email),
        "PDC_CONFIRMATION_URL_exists": bool(settings.pdc_confirmation_url),
        "PDC_SHEET_WEBHOOK_URL_exists": bool(settings.pdc_sheet_webhook_url),
        "RESEND_FROM_EMAIL": settings.resend_from_email,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
