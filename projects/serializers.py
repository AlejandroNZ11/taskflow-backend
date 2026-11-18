from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import UserMiniSerializer

from .models import Comment, Project, Task

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    members = UserMiniSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner", "members", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_task_count(self, obj) -> int:
        # Viene anotado desde el queryset; si no (por ejemplo, recién creado), se calcula.
        count = getattr(obj, "task_count", None)
        return count if count is not None else obj.tasks.count()


class MemberSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No existe un usuario con ese nombre.")


class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    assigned_to_detail = UserMiniSerializer(source="assigned_to", read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "project", "title", "description",
            "status", "status_display", "priority", "priority_display",
            "assigned_to", "assigned_to_detail", "created_by",
            "due_date", "is_overdue", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Solo se pueden usar proyectos donde el usuario es miembro.
            self.fields["project"].queryset = Project.objects.for_user(request.user)

    def validate_project(self, project):
        if self.instance and project.pk != self.instance.project_id:
            raise serializers.ValidationError("No se puede mover una tarea a otro proyecto.")
        return project

    def validate(self, attrs):
        project = attrs.get("project") or getattr(self.instance, "project", None)
        assigned = attrs.get("assigned_to", getattr(self.instance, "assigned_to", None))
        if project and assigned and not project.is_member(assigned):
            raise serializers.ValidationError(
                {"assigned_to": "El usuario asignado debe ser miembro del proyecto."}
            )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.none())
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "text", "created_at"]
        read_only_fields = ["id", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["task"].queryset = Task.objects.filter(
                project__in=Project.objects.for_user(request.user)
            )

    def validate_task(self, task):
        if self.instance and task.pk != self.instance.task_id:
            raise serializers.ValidationError("No se puede mover un comentario a otra tarea.")
        return task
