import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    resend_api_key: str | None = os.getenv("RESEND_API_KEY")
    resend_from_email: str | None = os.getenv("RESEND_FROM_EMAIL")
    pdc_confirmation_url: str | None = os.getenv("PDC_CONFIRMATION_URL")
    pdc_sheet_webhook_url: str | None = os.getenv("PDC_SHEET_WEBHOOK_URL")


settings = Settings()
