from django.db.models import Count
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Project, Task
from .permissions import CanDeleteTask, IsAuthorOrReadOnly, IsProjectOwnerOrReadOnly
from .serializers import CommentSerializer, MemberSerializer, ProjectSerializer, TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD de proyectos. Cada usuario ve solo los proyectos donde participa."""

    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrReadOnly]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # generación de docs Swagger
            return Project.objects.none()
        return (
            Project.objects.for_user(self.request.user)
            .select_related("owner")
            .prefetch_related("members")
            .annotate(task_count=Count("tasks"))
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(request=MemberSerializer, responses=ProjectSerializer)
    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Agrega un miembro por username (solo el dueño)."""
        project = self.get_object()
        serializer = MemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["username"]
        if user.pk == project.owner_id:
            return Response({"detail": "El dueño ya forma parte del proyecto."}, status=400)
        project.members.add(user)
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(request=MemberSerializer, responses=ProjectSerializer)
    @action(detail=True, methods=["post"], url_path="members/remove")
    def remove_member(self, request, pk=None):
        """Quita un miembro por username (solo el dueño). Sus tareas quedan sin asignar."""
        project = self.get_object()
        serializer = MemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["username"]
        project.members.remove(user)
        project.tasks.filter(assigned_to=user).update(assigned_to=None)
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Estadísticas del proyecto: tareas por estado, prioridad, vencidas y % de avance."""
        project = self.get_object()
        tasks = project.tasks.all()
        total = tasks.count()

        by_status = {choice.value: 0 for choice in Task.Status}
        for row in tasks.values("status").annotate(n=Count("id")):
            by_status[row["status"]] = row["n"]

        by_priority = {choice.label: 0 for choice in Task.Priority}
        for row in tasks.values("priority").annotate(n=Count("id")):
            by_priority[Task.Priority(row["priority"]).label] = row["n"]

        overdue = (
            tasks.filter(due_date__lt=timezone.localdate()).exclude(status=Task.Status.DONE).count()
        )
        done = by_status[Task.Status.DONE]
        return Response(
            {
                "project": project.name,
                "total_tasks": total,
                "by_status": by_status,
                "by_priority": by_priority,
                "overdue": overdue,
                "progress_percent": round(done * 100 / total, 1) if total else 0,
            }
        )


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD de tareas.

    Filtros: ?project=1&status=todo&priority=3&assigned_to=2&due_date__lte=2026-12-31
    Búsqueda: ?search=texto   Orden: ?ordering=due_date | -priority | created_at
    """

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, CanDeleteTask]
    filterset_fields = {
        "project": ["exact"],
        "status": ["exact"],
        "priority": ["exact"],
        "assigned_to": ["exact", "isnull"],
        "due_date": ["exact", "lte", "gte"],
    }
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "created_at", "title"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(
            project__in=Project.objects.for_user(self.request.user)
        ).select_related("project", "project__owner", "assigned_to", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        """Tareas asignadas al usuario logueado."""
        qs = self.filter_queryset(self.get_queryset().filter(assigned_to=request.user))
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """Comentarios de tareas. Filtrar con ?task=ID."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    filterset_fields = ["task"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return Comment.objects.filter(
            task__project__in=Project.objects.for_user(self.request.user)
        ).select_related("author", "task")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
