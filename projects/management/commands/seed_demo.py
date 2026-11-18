"""
Carga datos de ejemplo para la demo:  python manage.py seed_demo
Crea los usuarios 'demo' y 'ana' (contraseña: Demo12345!) con un proyecto y tareas.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import Comment, Project, Task

DEMO_PASSWORD = "Demo12345!"


class Command(BaseCommand):
    help = "Crea usuarios y datos de ejemplo para la presentación."

    def handle(self, *args, **options):
        User = get_user_model()
        users = {}
        for username, first, email in [
            ("demo", "Demo", "demo@taskflow.local"),
            ("ana", "Ana", "ana@taskflow.local"),
        ]:
            user, created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "email": email}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users[username] = user

        demo, ana = users["demo"], users["ana"]
        project, created = Project.objects.get_or_create(
            name="Proyecto Final Backend",
            owner=demo,
            defaults={"description": "Planificación del proyecto final de la materia."},
        )
        project.members.add(ana)

        if created:
            today = timezone.localdate()
            tasks = [
                ("Diseñar modelos de datos", Task.Status.DONE, Task.Priority.HIGH, demo, -5),
                ("Implementar login con JWT", Task.Status.DONE, Task.Priority.HIGH, demo, -2),
                ("Crear colección de Bruno", Task.Status.IN_PROGRESS, Task.Priority.MEDIUM, ana, 2),
                ("Dockerizar la aplicación", Task.Status.IN_PROGRESS, Task.Priority.HIGH, demo, 3),
                ("Desplegar en AWS EC2", Task.Status.TODO, Task.Priority.HIGH, demo, 7),
                ("Preparar la presentación", Task.Status.TODO, Task.Priority.LOW, ana, 10),
                ("Revisar tests", Task.Status.TODO, Task.Priority.MEDIUM, ana, -1),
            ]
            for title, status, priority, assignee, days in tasks:
                task = Task.objects.create(
                    project=project,
                    title=title,
                    status=status,
                    priority=priority,
                    assigned_to=assignee,
                    created_by=demo,
                    due_date=today + timedelta(days=days),
                )
                if status == Task.Status.IN_PROGRESS:
                    Comment.objects.create(task=task, author=ana, text="Ya estoy avanzando con esto 👍")

        self.stdout.write(self.style.SUCCESS("Datos de demo listos."))
        self.stdout.write(f"  Usuarios: demo / ana   Contraseña: {DEMO_PASSWORD}")
