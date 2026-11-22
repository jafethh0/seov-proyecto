# Register your models here.
from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "education_level", "preferred_department", "created_at")
    list_filter = ("education_level", "preferred_department")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_select_related = ("user", "preferred_department")