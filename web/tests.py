from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project, Task

User = get_user_model()


class WebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("juan", "juan@mail.com", "ClaveSegura123!")
        self.other = User.objects.create_user("pedro", "pedro@mail.com", "ClaveSegura123!")

    def test_dashboard_redirige_a_login(self):
        res = self.client.get(reverse("web:dashboard"))
        self.assertRedirects(res, f"{reverse('web:login')}?next=/")

    def test_login_y_dashboard(self):
        res = self.client.post(reverse("web:login"), {"username": "juan", "password": "ClaveSegura123!"})
        self.assertRedirects(res, reverse("web:dashboard"))
        self.assertContains(self.client.get(reverse("web:dashboard")), "Mis proyectos")

    def test_registro_web(self):
        res = self.client.post(reverse("web:register"), {
            "username": "nuevo", "email": "nuevo@mail.com",
            "password1": "ClaveSegura123!", "password2": "ClaveSegura123!",
        })
        self.assertRedirects(res, reverse("web:dashboard"))
        self.assertTrue(User.objects.filter(username="nuevo").exists())

    def test_flujo_proyecto_y_tarea(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("web:project_create"), {"name": "Web", "description": ""})
        project = Project.objects.get(name="Web")
        self.assertRedirects(res, reverse("web:project_detail", args=[project.pk]))

        self.client.post(reverse("web:task_create", args=[project.pk]), {"title": "T1", "priority": 2})
        task = Task.objects.get(title="T1")
        self.client.post(reverse("web:task_status", args=[task.pk]), {"status": "done"})
        task.refresh_from_db()
        self.assertEqual(task.status, "done")

        self.client.post(reverse("web:task_detail", args=[task.pk]), {"text": "Listo!"})
        self.assertContains(self.client.get(reverse("web:task_detail", args=[task.pk])), "Listo!")

    def test_no_puedo_ver_proyecto_ajeno(self):
        project = Project.objects.create(name="Privado", owner=self.other)
        self.client.force_login(self.user)
        res = self.client.get(reverse("web:project_detail", args=[project.pk]))
        self.assertEqual(res.status_code, 404)
