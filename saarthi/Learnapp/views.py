from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny
from .models import Module, UserModule, TestAttempt, Feedback, DiagnosticTestResult
from .serializers import (
    ModuleSerializer,
    UserModuleSerializer,
    TestAttemptSerializer,
    FeedbackSerializer,
    DiagnosticTestResultSerializer
)

from django.conf import settings
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_tokens_for_user(user):
    try:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    except Exception as e:
        raise Exception(f"Error generating tokens: {str(e)}")

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserModuleViewSet(viewsets.ModelViewSet):
    queryset = UserModule.objects.all()
    serializer_class = UserModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserModule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate_module(self, request):
        concept = request.data.get('concept')
        level = request.data.get('level')

        if not concept or not level:
            return Response({"error": "Concept and level are required."}, status=status.HTTP_400_BAD_REQUEST)

        if level not in ['beginner', 'intermediate', 'advanced']:
            return Response({"error": "Level must be 'beginner', 'intermediate', or 'advanced'."}, status=status.HTTP_400_BAD_REQUEST)

        module_prompt = f"Create a {level} level educational module on the topic of '{concept}', including theory, examples, and exercises."
        test_prompt = f"Create a {level} level test with questions and answers based on the topic '{concept}'."

        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')

            module_response = model.generate_content(module_prompt)
            module_content = module_response.text.strip()

            test_response = model.generate_content(test_prompt)
            test_content = test_response.text.strip()

            user_module = UserModule.objects.create(
                user=request.user,
                concept=concept,
                level=level,
                module_content=module_content,
                test_content=test_content
            )

            return Response({
                "module_content": module_content,
                "test_content": test_content
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TestAttemptViewSet(viewsets.ModelViewSet):
    queryset = TestAttempt.objects.all()
    serializer_class = TestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestAttempt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_explanation(request):
    concept = request.data.get("concept")
    difficulty = request.data.get("difficulty", "intermediate")
    prompt = f"Explain the concept of '{concept}' at a {difficulty} level."

    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        explanation = response.text.strip()
        return Response({"explanation": explanation})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def simplify_text(request):
    text = request.data.get("text")
    prompt = f"Simplify the following text for a high school student:\n\n{text}"

    try:
        model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        simplified = response.text.strip()
        return Response({"simplified_text": simplified})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_diagnostic_test(request):
    score = request.data.get("score")

    if score is None:
        return Response({"error": "Score is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        score = float(score)
    except ValueError:
        return Response({"error": "Score must be a number."}, status=status.HTTP_400_BAD_REQUEST)

    if score < 40:
        level = 'beginner'
    elif score < 70:
        level = 'intermediate'
    else:
        level = 'advanced'

    diagnostic, created = DiagnosticTestResult.objects.update_or_create(
        user=request.user,
        defaults={'score': score, 'recommended_level': level}
    )

    return Response({
        "message": "Diagnostic test submitted.",
        "score": score,
        "recommended_level": level
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")

    if not username or not password or not email:
        return Response({"error": "Username, password, and email are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    tokens = get_tokens_for_user(user)

    return Response({
        "message": "User registered successfully.",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "refresh": tokens['refresh'],
        "access": tokens['access'],
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    tokens = get_tokens_for_user(user)

    return Response({
        'message': 'Login successful',
        'user_id': user.id,
        'username': user.username,
        'access': tokens['access'],
        'refresh': tokens['refresh'],
    }, status=status.HTTP_200_OK)
