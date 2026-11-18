"""
Permisos a nivel de objeto.

La visibilidad (ver solo proyectos donde sos miembro) se resuelve en get_queryset:
si no sos miembro, el recurso directamente devuelve 404.
Estas clases controlan QUIÉN puede modificar/borrar lo que sí puede ver.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProjectOwnerOrReadOnly(BasePermission):
    message = "Solo el dueño del proyecto puede modificarlo."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == request.user.id


class CanDeleteTask(BasePermission):
    """Cualquier miembro edita tareas; solo el creador o el dueño del proyecto las borra."""

    message = "Solo quien creó la tarea o el dueño del proyecto puede borrarla."

    def has_object_permission(self, request, view, obj):
        if request.method != "DELETE":
            return True
        return request.user.id in (obj.created_by_id, obj.project.owner_id)


class IsAuthorOrReadOnly(BasePermission):
    message = "Solo el autor puede modificar este comentario."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
