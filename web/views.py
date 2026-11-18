"""Vistas del frontend básico (usa sesión de Django, no JWT)."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.models import Project, Task

from .forms import CommentForm, MemberForm, ProjectForm, RegisterForm, TaskForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("web:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"¡Bienvenido/a, {user.username}!")
        return redirect("web:dashboard")
    return render(request, "web/register.html", {"form": form})


@login_required
def dashboard(request):
    projects = Project.objects.for_user(request.user).select_related("owner").annotate(
        total=Count("tasks"),
        done=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
    ).order_by("-created_at")
    my_tasks = (
        Task.objects.filter(assigned_to=request.user)
        .exclude(status=Task.Status.DONE)
        .select_related("project")[:10]
    )
    return render(request, "web/dashboard.html", {"projects": projects, "my_tasks": my_tasks})


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, "Proyecto creado.")
        return redirect("web:project_detail", pk=project.pk)
    return render(request, "web/project_form.html", {"form": form})


def _get_project(request, pk):
    return get_object_or_404(Project.objects.for_user(request.user), pk=pk)


@login_required
def project_detail(request, pk):
    project = _get_project(request, pk)
    tasks = project.tasks.select_related("assigned_to")
    columns = [
        (value, label, [t for t in tasks if t.status == value])
        for value, label in Task.Status.choices
    ]
    context = {
        "project": project,
        "columns": columns,
        "task_form": TaskForm(project=project),
        "member_form": MemberForm(),
        "is_owner": project.owner_id == request.user.id,
        "statuses": Task.Status.choices,
    }
    return render(request, "web/project_detail.html", context)


@login_required
@require_POST
def project_delete(request, pk):
    project = _get_project(request, pk)
    if project.owner_id != request.user.id:
        return HttpResponseForbidden("Solo el dueño puede borrar el proyecto.")
    project.delete()
    messages.success(request, "Proyecto eliminado.")
    return redirect("web:dashboard")


@login_required
@require_POST
def project_add_member(request, pk):
    project = _get_project(request, pk)
    if project.owner_id != request.user.id:
        return HttpResponseForbidden("Solo el dueño puede agregar miembros.")
    form = MemberForm(request.POST)
    if form.is_valid():
        project.members.add(form.cleaned_data["username"])
        messages.success(request, "Miembro agregado.")
    else:
        messages.error(request, form.errors["username"][0])
    return redirect("web:project_detail", pk=pk)


@login_required
@require_POST
def task_create(request, pk):
    project = _get_project(request, pk)
    form = TaskForm(request.POST, project=project)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        task.save()
        messages.success(request, "Tarea creada.")
    else:
        messages.error(request, "Revisá los datos de la tarea.")
    return redirect("web:project_detail", pk=pk)


def _get_task(request, pk):
    return get_object_or_404(
        Task.objects.filter(project__in=Project.objects.for_user(request.user)).select_related(
            "project", "assigned_to", "created_by"
        ),
        pk=pk,
    )


@login_required
@require_POST
def task_status(request, pk):
    task = _get_task(request, pk)
    new_status = request.POST.get("status")
    if new_status in Task.Status.values:
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])
    return redirect("web:project_detail", pk=task.project_id)


@login_required
@require_POST
def task_delete(request, pk):
    task = _get_task(request, pk)
    if request.user.id not in (task.created_by_id, task.project.owner_id):
        return HttpResponseForbidden("No tenés permiso para borrar esta tarea.")
    project_id = task.project_id
    task.delete()
    messages.success(request, "Tarea eliminada.")
    return redirect("web:project_detail", pk=project_id)


@login_required
def task_detail(request, pk):
    task = _get_task(request, pk)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        return redirect("web:task_detail", pk=pk)
    comments = task.comments.select_related("author")
    return render(request, "web/task_detail.html", {"task": task, "comments": comments, "form": form})
