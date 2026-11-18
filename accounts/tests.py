from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("juan", "juan@mail.com", "ClaveSegura123!")

    def test_registro_crea_usuario(self):
        data = {
            "username": "maria",
            "email": "Maria@Mail.com",
            "password": "ClaveSegura123!",
            "password2": "ClaveSegura123!",
        }
        res = self.client.post(reverse("register"), data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data)
        self.assertEqual(User.objects.get(username="maria").email, "maria@mail.com")

    def test_registro_passwords_distintas(self):
        data = {"username": "x", "email": "x@mail.com", "password": "ClaveSegura123!", "password2": "otra"}
        res = self.client.post(reverse("register"), data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_password_debil(self):
        data = {"username": "x", "email": "x@mail.com", "password": "123", "password2": "123"}
        res = self.client.post(reverse("register"), data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    def test_registro_email_duplicado(self):
        data = {"username": "otro", "email": "JUAN@mail.com", "password": "ClaveSegura123!", "password2": "ClaveSegura123!"}
        res = self.client.post(reverse("register"), data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_devuelve_jwt_y_permite_ver_perfil(self):
        res = self.client.post(reverse("token_obtain_pair"), {"username": "juan", "password": "ClaveSegura123!"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
        me = self.client.get(reverse("me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "juan")

    def test_login_incorrecto(self):
        res = self.client.post(reverse("token_obtain_pair"), {"username": "juan", "password": "mal"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_perfil_requiere_autenticacion(self):
        self.assertEqual(self.client.get(reverse("me")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_editar_perfil(self):
        self.client.force_authenticate(self.user)
        res = self.client.patch(reverse("me"), {"bio": "Estudiante de backend", "username": "hacker"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Estudiante de backend")
        self.assertEqual(self.user.username, "juan")  # username es de solo lectura
