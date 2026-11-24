# Register your models here.
from django.contrib import admin

from .models import AnswerOption, Dimension, Question, QuestionDimension, Questionnaire


@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name")


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("title", "version", "is_active", "created_at")
    list_filter = ("is_active",)


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 0


class QuestionDimensionInline(admin.TabularInline):
    model = QuestionDimension
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("code", "questionnaire", "section", "kind", "order", "is_active")
    list_filter = ("questionnaire", "section", "kind", "is_active")
    search_fields = ("code", "text")
    inlines = [QuestionDimensionInline, AnswerOptionInline]
    list_select_related = ("questionnaire",)