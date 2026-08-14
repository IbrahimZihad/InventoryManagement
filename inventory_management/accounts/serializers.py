from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


def validate_phone(value):
    if value and not value.replace("+", "").replace(" ", "").isdigit():
        raise serializers.ValidationError(
            "Phone number must contain digits only (optionally starting with '+')."
        )
    return value


class RegisterSerializer(serializers.ModelSerializer):
    """Handles new user sign-up with password confirmation and email uniqueness."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password2", "phone_number", "address"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        return validate_phone(value)

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    """Used by the authenticated user to view/update their own profile."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "bio",
            "avatar",
            "date_joined",
        ]
        read_only_fields = ["id", "username", "date_joined"]

    def validate_phone_number(self, value):
        return validate_phone(value)

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk if self.instance else None)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
