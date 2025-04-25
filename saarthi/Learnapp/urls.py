from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ModuleViewSet,
    UserModuleViewSet,
    TestAttemptViewSet,
    FeedbackViewSet,
    register,
    login_user,
    get_explanation,
    simplify_text,
    submit_diagnostic_test
)

router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'user-modules', UserModuleViewSet)
router.register(r'test-attempts', TestAttemptViewSet)
router.register(r'feedback', FeedbackViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/register/', register, name='register'),
    path('api/login/', login_user, name='login'),
    path('api/get-explanation/', get_explanation),
    path('api/simplify-text/', simplify_text),
    path('api/diagnostic/', submit_diagnostic_test),
]
