from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Project, Task

User = get_user_model()


class BaseTestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", "owner@mail.com", "x")
        self.member = User.objects.create_user("member", "member@mail.com", "x")
        self.stranger = User.objects.create_user("stranger", "stranger@mail.com", "x")
        self.project = Project.objects.create(name="Proyecto A", owner=self.owner)
        self.project.members.add(self.member)
        self.task = Task.objects.create(project=self.project, title="Tarea 1", created_by=self.owner)


class ProjectApiTests(BaseTestCase):
    def test_crear_proyecto_asigna_dueno(self):
        self.client.force_authenticate(self.stranger)
        res = self.client.post(reverse("project-list"), {"name": "Mío"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["owner"]["username"], "stranger")
        self.assertEqual(res.data["task_count"], 0)

    def test_solo_veo_mis_proyectos(self):
        self.client.force_authenticate(self.stranger)
        res = self.client.get(reverse("project-list"))
        self.assertEqual(res.data["count"], 0)
        detail = self.client.get(reverse("project-detail", args=[self.project.pk]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_miembro_ve_proyecto_sin_duplicados(self):
        self.client.force_authenticate(self.member)
        res = self.client.get(reverse("project-list"))
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["task_count"], 1)

    def test_miembro_no_puede_editar_ni_borrar(self):
        self.client.force_authenticate(self.member)
        url = reverse("project-detail", args=[self.project.pk])
        self.assertEqual(self.client.patch(url, {"name": "X"}).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_dueno_puede_borrar(self):
        self.client.force_authenticate(self.owner)
        res = self.client.delete(reverse("project-detail", args=[self.project.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.exists())

    def test_agregar_y_quitar_miembro(self):
        self.client.force_authenticate(self.owner)
        add = self.client.post(reverse("project-add-member", args=[self.project.pk]), {"username": "stranger"})
        self.assertEqual(add.status_code, status.HTTP_200_OK)
        self.assertTrue(self.project.members.filter(pk=self.stranger.pk).exists())

        self.task.assigned_to = self.stranger
        self.task.save()
        rem = self.client.post(reverse("project-remove-member", args=[self.project.pk]), {"username": "stranger"})
        self.assertEqual(rem.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assigned_to)

    def test_agregar_usuario_inexistente(self):
        self.client.force_authenticate(self.owner)
        res = self.client.post(reverse("project-add-member", args=[self.project.pk]), {"username": "nadie"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_miembro_no_puede_agregar_miembros(self):
        self.client.force_authenticate(self.member)
        res = self.client.post(reverse("project-add-member", args=[self.project.pk]), {"username": "stranger"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_estadisticas(self):
        Task.objects.create(project=self.project, title="Hecha", status=Task.Status.DONE, created_by=self.owner)
        Task.objects.create(
            project=self.project, title="Vencida", created_by=self.owner,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_authenticate(self.member)
        res = self.client.get(reverse("project-stats", args=[self.project.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_tasks"], 3)
        self.assertEqual(res.data["by_status"]["done"], 1)
        self.assertEqual(res.data["overdue"], 1)
        self.assertEqual(res.data["progress_percent"], 33.3)


class TaskApiTests(BaseTestCase):
    def test_miembro_crea_tarea(self):
        self.client.force_authenticate(self.member)
        res = self.client.post(
            reverse("task-list"),
            {"project": self.project.pk, "title": "Nueva", "assigned_to": self.owner.pk, "priority": 3},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["created_by"]["username"], "member")

    def test_no_puedo_crear_tarea_en_proyecto_ajeno(self):
        self.client.force_authenticate(self.stranger)
        res = self.client.post(reverse("task-list"), {"project": self.project.pk, "title": "Hack"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", res.data)

    def test_asignado_debe_ser_miembro(self):
        self.client.force_authenticate(self.owner)
        res = self.client.post(
            reverse("task-list"),
            {"project": self.project.pk, "title": "X", "assigned_to": self.stranger.pk},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned_to", res.data)

    def test_no_veo_tareas_ajenas(self):
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(reverse("task-list")).data["count"], 0)
        res = self.client.get(reverse("task-detail", args=[self.task.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cambiar_estado(self):
        self.client.force_authenticate(self.member)
        res = self.client.patch(reverse("task-detail", args=[self.task.pk]), {"status": "done"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status_display"], "Hecha")

    def test_estado_invalido(self):
        self.client.force_authenticate(self.member)
        res = self.client.patch(reverse("task-detail", args=[self.task.pk]), {"status": "volando"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_se_puede_mover_tarea_de_proyecto(self):
        other = Project.objects.create(name="B", owner=self.owner)
        self.client.force_authenticate(self.owner)
        res = self.client.patch(reverse("task-detail", args=[self.task.pk]), {"project": other.pk})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_miembro_no_borra_tarea_ajena(self):
        self.client.force_authenticate(self.member)
        res = self.client.delete(reverse("task-detail", args=[self.task.pk]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtros_y_busqueda(self):
        Task.objects.create(project=self.project, title="Configurar Docker", status="done", created_by=self.owner)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(reverse("task-list"), {"status": "done"}).data["count"], 1)
        self.assertEqual(self.client.get(reverse("task-list"), {"search": "docker"}).data["count"], 1)

    def test_mis_tareas(self):
        self.task.assigned_to = self.member
        self.task.save()
        self.client.force_authenticate(self.member)
        res = self.client.get(reverse("task-mine"))
        self.assertEqual(res.data["count"], 1)


class CommentApiTests(BaseTestCase):
    def test_comentar_y_permisos_de_autor(self):
        self.client.force_authenticate(self.member)
        res = self.client.post(reverse("comment-list"), {"task": self.task.pk, "text": "Hola"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        comment_url = reverse("comment-detail", args=[res.data["id"]])

        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(comment_url, {"text": "x"}).status_code, status.HTTP_403_FORBIDDEN)

    def test_no_comento_tareas_ajenas(self):
        self.client.force_authenticate(self.stranger)
        res = self.client.post(reverse("comment-list"), {"task": self.task.pk, "text": "Hola"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Comment.objects.exists())


class SeedAndHealthTests(APITestCase):
    def test_seed_demo_es_idempotente(self):
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Task.objects.count(), 7)

    def test_health(self):
        res = self.client.get("/health/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["database"])

    def test_health_con_host_interno_de_render(self):
        # El health check de Render llega con un Host que no está en ALLOWED_HOSTS
        res = self.client.get("/health/", HTTP_HOST="10.0.0.5:10000")
        self.assertEqual(res.status_code, 200)
        # El resto del sitio sigue rechazando hosts no permitidos
        self.assertEqual(self.client.get("/login/", HTTP_HOST="10.0.0.5:10000").status_code, 400)
