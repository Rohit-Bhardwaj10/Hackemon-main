from rest_framework import serializers
from .models import Module, UserModule, TestAttempt, Feedback, DiagnosticTestResult

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class UserModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModule
        fields = '__all__'
        read_only_fields = ['user']

class TestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAttempt
        fields = '__all__'
        read_only_fields = ['user']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['user']

class DiagnosticTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTestResult
        fields = '__all__'
        read_only_fields = ['user', 'recommended_level', 'taken_at']
