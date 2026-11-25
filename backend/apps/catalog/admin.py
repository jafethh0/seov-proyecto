from django.contrib import admin

from .models import (
    Campus,
    CareerCategory,
    CareerDimension,
    CareerProgram,
    Department,
    Institution,
    ProgramOffering,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "acronym", "sector", "is_active")
    list_filter = ("sector", "is_active")
    search_fields = ("name", "acronym")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "department", "city", "is_active")
    list_filter = ("department", "institution", "is_active")
    search_fields = ("name", "institution__name", "city")
    list_select_related = ("institution", "department")


@admin.register(CareerCategory)
class CareerCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class CareerDimensionInline(admin.TabularInline):
    model = CareerDimension
    extra = 0


@admin.register(CareerProgram)
class CareerProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "program_type", "category", "is_active")
    list_filter = ("program_type", "category", "is_active")
    search_fields = ("name",)
    list_select_related = ("category",)
    inlines = [CareerDimensionInline]


@admin.register(ProgramOffering)
class ProgramOfferingAdmin(admin.ModelAdmin):
    list_display = (
        "official_name",
        "program",
        "campus",
        "modality",
        "verified_at",
        "verification_status",
        "is_active",
    )
    list_filter = (
        "is_active",
        "verification_status",
        "modality",
        "campus__department",
        "campus__institution",
        "program__program_type",
    )
    search_fields = ("official_name", "program__name", "campus__name")
    autocomplete_fields = ("program", "campus")
    list_select_related = ("program", "campus__institution", "campus__department")