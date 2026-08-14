from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView

from .views import (
    ChangePasswordView,
    CookieTokenRefreshView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Login/logout: returns JWTs in the response body AND sets them as
    # httponly cookies, so browser clients don't need to store tokens
    # manually (e.g. in localStorage).
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Plain JWT endpoints (useful for mobile apps / scripts that manage
    # their own token storage instead of relying on cookies).
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
