"""
Serializers públicos del cuestionario.

IMPORTANTE: no exponen puntos, criterios, justificaciones ni dimensiones, para no
revelar cuál es la respuesta correcta durante la evaluación.
"""
from rest_framework import serializers

from .models import AnswerOption, Question


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ("id", "text")


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "kind", "text", "passage", "options")