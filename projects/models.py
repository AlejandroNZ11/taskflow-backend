from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        """Proyectos donde el usuario es dueño o miembro (sin duplicados)."""
        ids = self.model._base_manager.filter(Q(owner=user) | Q(members=user)).values("pk")
        return self.filter(pk__in=ids)


class Project(models.Model):
    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="dueño",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="projects", blank=True, verbose_name="miembros"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"

    def __str__(self):
        return self.name

    def is_member(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.pk == self.owner_id or self.members.filter(pk=user.pk).exists()

    def all_members(self):
        """Dueño + miembros, útil para asignar tareas."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.filter(Q(pk=self.owner_id) | Q(projects=self)).distinct()


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "Por hacer"
        IN_PROGRESS = "in_progress", "En progreso"
        DONE = "done", "Hecha"

    class Priority(models.IntegerChoices):
        LOW = 1, "Baja"
        MEDIUM = 2, "Media"
        HIGH = 3, "Alta"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="proyecto"
    )
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.TODO, db_index=True
    )
    priority = models.PositiveSmallIntegerField(
        "prioridad", choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="asignada a",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
        verbose_name="creada por",
    )
    due_date = models.DateField("fecha límite", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "due_date", "-created_at"]
        verbose_name = "tarea"
        verbose_name_plural = "tareas"

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status != self.Status.DONE
            and self.due_date < timezone.localdate()
        )


class Comment(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments", verbose_name="tarea"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments", verbose_name="autor"
    )
    text = models.TextField("texto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"

    def __str__(self):
        return f"{self.author} en {self.task}"
