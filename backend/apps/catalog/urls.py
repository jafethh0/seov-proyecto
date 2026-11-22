from django.urls import path

from . import views

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department-list"),
    path("careers/", views.CareerListView.as_view(), name="career-list"),
    path("careers/<int:pk>/", views.CareerDetailView.as_view(), name="career-detail"),
]