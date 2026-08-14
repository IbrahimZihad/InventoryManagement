from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


def _set_jwt_cookies(response, access_token, refresh_token=None):
    """Attach the access token (and optionally refresh token) as httponly cookies."""
    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        str(access_token),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        path="/",
    )
    if refresh_token is not None:
        response.set_cookie(
            settings.JWT_AUTH_REFRESH_COOKIE,
            str(refresh_token),
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            path="/api/accounts/",
        )
    return response


def _clear_jwt_cookies(response):
    response.delete_cookie(settings.JWT_AUTH_COOKIE, path="/")
    response.delete_cookie(settings.JWT_AUTH_REFRESH_COOKIE, path="/api/accounts/")
    return response


class RegisterView(generics.CreateAPIView):
    """POST /api/accounts/register/  - public endpoint, creates a new user + profile."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET /api/accounts/me/            - view own profile
    PUT/PATCH /api/accounts/me/      - update own profile (incl. nested profile fields)
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/accounts/change-password/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /api/accounts/login/
    body: {"username": "...", "password": "..."}

    Authenticates the user and returns a JWT access + refresh token pair
    in the response body, AND sets them as httponly cookies. Browser-based
    clients can rely on the cookies alone (no manual token storage needed);
    API/mobile/script clients can instead take "access"/"refresh" from the
    JSON body and send `Authorization: Bearer <access>` themselves.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
        return _set_jwt_cookies(response, access, refresh)


class LogoutView(APIView):
    """
    POST /api/accounts/logout/
    Blacklists the refresh token (read from the request body if provided,
    otherwise from the httponly cookie set at login) and clears cookies.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_AUTH_REFRESH_COOKIE
        )
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                # Already invalid/expired/blacklisted - nothing more to do.
                pass

        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        return _clear_jwt_cookies(response)


class CookieTokenRefreshView(TokenRefreshView):
    """
    POST /api/accounts/token/refresh/
    Accepts the refresh token from the request body OR from the httponly
    cookie set at login, and re-sets the access-token (and rotated
    refresh-token) cookie(s) on success.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_AUTH_REFRESH_COOKIE
        )
        if not refresh_token:
            return Response(
                {"detail": "No refresh token provided."}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        access = serializer.validated_data["access"]
        new_refresh = serializer.validated_data.get("refresh")  # present if ROTATE_REFRESH_TOKENS

        body = {"access": access}
        if new_refresh:
            body["refresh"] = new_refresh

        response = Response(body, status=status.HTTP_200_OK)
        return _set_jwt_cookies(response, access, new_refresh)
