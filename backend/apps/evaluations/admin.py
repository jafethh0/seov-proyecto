# Register your models here.
from django.contrib import admin

from .models import Answer, Evaluation, EvaluationResult, ResultDimensionScore, ResultInference


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

class ScoreInline(admin.TabularInline):
    model = ResultDimensionScore
    extra = 0
    can_delete = False
    readonly_fields = ("dimension", "score", "level", "answered", "total", "required", "is_valid")

    def has_add_permission(self, request, obj=None):
        return False


class InferenceInline(admin.StackedInline):
    model = ResultInference
    extra = 0
    can_delete = False
    readonly_fields = ("rules_version", "facts", "summary", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ("id", "evaluation", "scoring_version", "created_at")
    readonly_fields = ("evaluation", "scoring_version", "config", "created_at")
    iinlines = [ScoreInline, InferenceInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False