import requests
from django.conf import settings

class PaymentCreateError(Exception): ...
class PaymentVerifyError(Exception): ...

def create_hitpay_payment(amount: str, currency: str = "SGD", webhook_url: str | None = None) -> dict:
    url = getattr(settings, "HITPAY_CREATE_PAYMENT_URL", "https://api.sandbox.hit-pay.com/v1/payment-requests")
    api_key = getattr(settings, "HITPAY_API_KEY", "")
    if not api_key:
        raise PaymentCreateError("HITPAY_API_KEY not configured")

    headers = {
        "X-BUSINESS-API-KEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {
        "amount": str(amount),
        "currency": (currency or "SGD").upper(),
        "payment_methods[]": "paynow_online",
        "generate_qr": "true",
        "webhook": webhook_url or getattr(settings, "HITPAY_WEBHOOK_URL", "https://example.com/webhook/"),
    }

    resp = requests.post(url, data=payload, headers=headers, timeout=30)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise PaymentCreateError(f"HTTP {resp.status_code}: {resp.text}") from e
    return resp.json()
