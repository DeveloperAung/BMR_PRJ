from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email: str, code: str):
    subject = "Your verification code"
    body = f"Your OTP code is: {code}. It expires in 10 minutes."
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

def send_username_email(email: str, username: str):
    subject = "Your username"
    body = f"Your username is: {username}"
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
