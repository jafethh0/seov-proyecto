# Create your views here.
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import StudentProfile
from .serializers import LoginSerializer, ProfileSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """Registra un estudiante. No devuelve tokens: el cliente inicia sesión después."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(ProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutView(APIView):
    """Revoca (blacklist) el refresh token recibido."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response(
                {"detail": "Falta el token de refresco."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response(
                {"detail": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Perfil del usuario autenticado. Solo permite ver y modificar el propio."""

    serializer_class = ProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        profile, _ = StudentProfile.objects.select_related("user").get_or_create(
            user=self.request.user
        )
        return profile