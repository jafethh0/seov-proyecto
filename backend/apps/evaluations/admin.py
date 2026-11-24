# Register your models here.
from django.contrib import admin

from .models import Answer, Evaluation


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    can_delete = False
    readonly_fields = ("question", "option", "answered_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Solo lectura: las evaluaciones son historial y no se editan desde el panel."""

    list_display = ("id", "user", "questionnaire", "status", "started_at", "submitted_at")
    list_filter = ("status", "questionnaire")
    search_fields = ("user__email",)
    list_select_related = ("user", "questionnaire")
    readonly_fields = ("user", "questionnaire", "status", "started_at", "updated_at", "submitted_at")
    inlines = [AnswerInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False