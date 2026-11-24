from rest_framework import serializers

from .models import Evaluation


class EvaluationSummarySerializer(serializers.ModelSerializer):
    questionnaire_version = serializers.CharField(source="questionnaire.version", read_only=True)

    class Meta:
        model = Evaluation
        fields = ("id", "status", "questionnaire_version", "started_at", "submitted_at")


class AnswerItemSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    option = serializers.IntegerField(allow_null=True)


class SaveAnswersSerializer(serializers.Serializer):
    answers = AnswerItemSerializer(many=True, allow_empty=False, max_length=200)

    def validate_answers(self, value):
        questions = [item["question"] for item in value]
        if len(questions) != len(set(questions)):
            raise serializers.ValidationError("Hay preguntas repetidas en la solicitud.")
        return value