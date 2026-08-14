from rest_framework import generics, permissions

from .serializers import ProfileSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """Public endpoint: POST username/email/password to create a new account."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  -> view own profile
    PUT/PATCH -> update own profile
    Always operates on the currently authenticated user; there is no
    lookup by id, so a user can never view or edit someone else's profile.
    """

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
