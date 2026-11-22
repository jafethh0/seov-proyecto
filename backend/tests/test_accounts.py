"""Pruebas de autenticación y perfil."""
from django.core.cache import cache
from django.test import TestCase

from apps.catalog.models import Department

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/token/refresh/"
LOGOUT = "/api/v1/auth/logout/"
PROFILE = "/api/v1/profile/"

VALID = {
    "email": "Ana@Example.com",
    "password": "ClaveSegura#2026",
    "first_name": "Ana",
    "education_level": "HIGH_SCHOOL",
}


class AccountsTests(TestCase):
    def setUp(self):
        cache.clear()  # el límite de intentos de auth usa la caché
        self.department = Department.objects.create(name="Cortés", slug="cortes")

    def post(self, url, data):
        return self.client.post(url, data, content_type="application/json")

    def login(self, email="ana@example.com", password="ClaveSegura#2026"):
        return self.post(LOGIN, {"email": email, "password": password})

    def auth_header(self, response):
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}

    def test_registro_valido_crea_usuario_y_perfil_sin_tokens(self):
        response = self.post(REGISTER, VALID)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["email"], "ana@example.com")
        self.assertEqual(body["role"], "STUDENT")
        self.assertNotIn("access", body)
        self.assertNotIn("password", body)

    def test_registro_correo_duplicado(self):
        self.post(REGISTER, VALID)
        response = self.post(REGISTER, {**VALID, "email": "ANA@example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_registro_contrasena_debil(self):
        response = self.post(REGISTER, {**VALID, "password": "12345678"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())

    def test_registro_nivel_invalido(self):
        response = self.post(REGISTER, {**VALID, "education_level": "OTRO"})
        self.assertEqual(response.status_code, 400)

    def test_login_con_correo_devuelve_tokens_y_usuario(self):
        self.post(REGISTER, VALID)
        response = self.login(email="ANA@example.com")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["role"], "STUDENT")

    def test_login_contrasena_incorrecta(self):
        self.post(REGISTER, VALID)
        self.assertEqual(self.login(password="incorrecta").status_code, 401)

    def test_perfil_exige_autenticacion(self):
        self.assertEqual(self.client.get(PROFILE).status_code, 401)

    def test_ver_y_actualizar_perfil(self):
        self.post(REGISTER, VALID)
        headers = self.auth_header(self.login())
        response = self.client.get(PROFILE, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["education_level"], "HIGH_SCHOOL")

        response = self.client.patch(
            PROFILE,
            {
                "first_name": "Ana María",
                "education_level": "UNIVERSITY",
                "preferred_department": self.department.id,
                "email": "otro@example.com",  # no se puede cambiar
            },
            content_type="application/json",
            **headers,
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["first_name"], "Ana María")
        self.assertEqual(body["education_level"], "UNIVERSITY")
        self.assertEqual(body["preferred_department"], self.department.id)
        self.assertEqual(body["email"], "ana@example.com")

    def test_cada_usuario_ve_solo_su_perfil(self):
        self.post(REGISTER, VALID)
        self.post(REGISTER, {**VALID, "email": "luis@example.com", "first_name": "Luis"})
        ana = self.client.get(PROFILE, **self.auth_header(self.login())).json()
        luis = self.client.get(
            PROFILE, **self.auth_header(self.login(email="luis@example.com"))
        ).json()
        self.assertEqual(ana["first_name"], "Ana")
        self.assertEqual(luis["first_name"], "Luis")

    def test_logout_revoca_el_refresh_token(self):
        self.post(REGISTER, VALID)
        tokens = self.login().json()
        self.assertEqual(self.post(LOGOUT, {"refresh": tokens["refresh"]}).status_code, 204)
        self.assertEqual(self.post(REFRESH, {"refresh": tokens["refresh"]}).status_code, 401)

    def test_logout_sin_token(self):
        self.assertEqual(self.post(LOGOUT, {}).status_code, 400)

    def test_refresh_rota_el_token(self):
        self.post(REGISTER, VALID)
        tokens = self.login().json()
        first = self.post(REFRESH, {"refresh": tokens["refresh"]})
        self.assertEqual(first.status_code, 200)
        self.assertIn("refresh", first.json())
        # El refresh anterior ya fue usado y queda en la lista negra.
        self.assertEqual(self.post(REFRESH, {"refresh": tokens["refresh"]}).status_code, 401)