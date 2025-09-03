from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register),
    path("send-otp/", views.send_otp),
    path("verify-otp/", views.verify_otp),
    path("login/", views.login),
    path("logout/", views.logout),
    path("forgot-password/", views.forgot_password),
    path("reset-password/", views.reset_password),
    path("forgot-username/", views.forgot_username),
    path("google/", views.google_login),
    path("set-password/", views.set_password),
]
