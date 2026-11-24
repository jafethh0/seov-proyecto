from django.urls import path

from . import views

urlpatterns = [
    path(
        "questionnaires/active/",
        views.ActiveQuestionnaireView.as_view(),
        name="questionnaire-active",
    ),
]