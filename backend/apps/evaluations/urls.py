from django.urls import path

from . import views

urlpatterns = [
    path("evaluations/", views.EvaluationListCreateView.as_view(), name="evaluation-list"),
    path("evaluations/<int:pk>/", views.EvaluationDetailView.as_view(), name="evaluation-detail"),
    path(
        "evaluations/<int:pk>/answers/",
        views.EvaluationAnswersView.as_view(),
        name="evaluation-answers",
    ),
    path(
        "evaluations/<int:pk>/submit/",
        views.EvaluationSubmitView.as_view(),
        name="evaluation-submit",
    ),
]