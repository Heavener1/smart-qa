from rest_framework.routers import DefaultRouter

from .views import (
    ChatSessionViewSet,
    FAQItemViewSet,
    FAQSetViewSet,
    KnowledgeBaseViewSet,
    KnowledgeDocumentViewSet,
    ModelProviderViewSet,
    OperationLogViewSet,
    PluginViewSet,
    SceneViewSet,
    SensitiveWordSetViewSet,
    SensitiveWordViewSet,
)

router = DefaultRouter()
router.register("knowledge-bases", KnowledgeBaseViewSet)
router.register("documents", KnowledgeDocumentViewSet)
router.register("models", ModelProviderViewSet)
router.register("faq-sets", FAQSetViewSet)
router.register("faq-items", FAQItemViewSet)
router.register("sensitive-word-sets", SensitiveWordSetViewSet)
router.register("sensitive-words", SensitiveWordViewSet)
router.register("plugins", PluginViewSet)
router.register("scenes", SceneViewSet)
router.register("sessions", ChatSessionViewSet)
router.register("logs", OperationLogViewSet)

urlpatterns = router.urls
