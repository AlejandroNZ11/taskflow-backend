from django.contrib import admin

from .models import Comment, Project, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ["title", "status", "priority", "assigned_to", "due_date"]


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    search_fields = ["name", "description", "owner__username"]
    filter_horizontal = ["members"]
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "priority", "assigned_to", "due_date"]
    list_filter = ["status", "priority", "project"]
    search_fields = ["title", "description"]
    list_editable = ["status"]
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["task", "author", "created_at"]
    search_fields = ["text"]
