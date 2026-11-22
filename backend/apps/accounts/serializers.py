from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.catalog.models import CareerProgram, Department

from .models import StudentProfile

User = get_user_model()


def user_role(user):
    """Rol derivado: los administradores son is_staff; el resto, estudiantes."""
    return "ADMIN" if user.is_staff else "STUDENT"


class ProfileSerializer(serializers.ModelSerializer):
    """Usuario + perfil. Lectura (GET /profile/) y actualización parcial (PATCH)."""

    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", max_length=150, required=False)
    last_name = serializers.CharField(
        source="user.last_name", max_length=150, required=False, allow_blank=True
    )
    role = serializers.SerializerMethodField()
    current_program = serializers.PrimaryKeyRelatedField(
        queryset=CareerProgram.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    preferred_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = StudentProfile
        fields = (
            "email",
            "first_name",
            "last_name",
            "role",
            "education_level",
            "current_program",
            "preferred_department",
        )

    def get_role(self, obj):
        return user_role(obj.user)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save(update_fields=list(user_data))
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    education_level = serializers.ChoiceField(choices=StudentProfile.EducationLevel.choices)
    preferred_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True
    )

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        # Se valida la contraseña contra las reglas de Django, usando los datos del usuario.
        candidate = User(
            username=attrs["email"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        user = User.objects.create_user(
            username=email,  # el correo en minúsculas es el nombre de usuario
            email=email,
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data.get("last_name", ""),
        )
        return StudentProfile.objects.create(
            user=user,
            education_level=validated_data["education_level"],
            preferred_department=validated_data.get("preferred_department"),
        )


class LoginSerializer(TokenObtainPairSerializer):
    """Acepta 'email' (o 'username'); devuelve access, refresh y datos básicos del usuario."""

    def to_internal_value(self, data):
        data = data.copy()
        login = data.get("email") or data.get("username") or ""
        data["username"] = str(login).strip().lower()
        return super().to_internal_value(data)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "role": user_role(self.user),
        }
        return data