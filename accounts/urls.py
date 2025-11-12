from django.urls import path
from .views import (
    SignupView,
    CustomLoginView,
    logout_view,
    verify_otp_view,
    resend_otp_view,
)

app_name = "accounts"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("resend-otp/", resend_otp_view, name="resend_otp"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]
