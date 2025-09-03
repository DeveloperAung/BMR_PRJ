import random
from datetime import timedelta, timezone, datetime

def generate_otp() -> str:
    return f"{random.randint(0, 9999):04d}"

def expiry(minutes=10):
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)
