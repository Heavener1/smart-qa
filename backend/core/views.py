from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ChatMessage,
    ChatSession,
    FAQItem,
    FAQSet,
    KnowledgeBase,
    KnowledgeDocument,
    ModelProvider,
    OperationLog,
    Plugin,
    Scene,
    SensitiveWord,
    SensitiveWordSet,
)
from .serializers import (
    ChatRequestSerializer,
    ChatSessionSerializer,
    FAQItemSerializer,
    FAQSetSerializer,
    KnowledgeBaseSerializer,
    KnowledgeDocumentSerializer,
    ModelProviderSerializer,
    OperationLogSerializer,
    PluginSerializer,
    SceneSerializer,
    SensitiveWordSerializer,
    SensitiveWordSetSerializer,
)
from .services import create_operation_log, process_chat, read_file_text, upload_file_to_minio


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer

    @action(detail=True, methods=["post"], url_path="upload")
    def upload(self, request, pk=None):
        knowledge_base = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "请上传文件。"}, status=status.HTTP_400_BAD_REQUEST)

        content = read_file_text(file_obj)
        object_name, storage_status = upload_file_to_minio(file_obj, file_obj.name)
        document = KnowledgeDocument.objects.create(
            knowledge_base=knowledge_base,
            title=request.data.get("title") or file_obj.name,
            file_name=file_obj.name,
            object_name=object_name,
            content=content,
            summary=(content[:200] + "...") if len(content) > 200 else content,
            status="processed" if content else "failed",
            metadata={
                "size": file_obj.size,
                "content_type": file_obj.content_type,
                "storage_status": storage_status,
            },
        )
        create_operation_log(
            "knowledge.upload",
            f"上传知识文档 {document.title}",
            {"document_id": document.id, "storage_status": storage_status},
            level="warning" if storage_status != "uploaded" else "info",
        )
        return Response(KnowledgeDocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class KnowledgeDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KnowledgeDocument.objects.select_related("knowledge_base").all()
    serializer_class = KnowledgeDocumentSerializer


class ModelProviderViewSet(viewsets.ModelViewSet):
    queryset = ModelProvider.objects.all()
    serializer_class = ModelProviderSerializer


class FAQSetViewSet(viewsets.ModelViewSet):
    queryset = FAQSet.objects.all()
    serializer_class = FAQSetSerializer


class FAQItemViewSet(viewsets.ModelViewSet):
    queryset = FAQItem.objects.select_related("faq_set").all()
    serializer_class = FAQItemSerializer


class SensitiveWordSetViewSet(viewsets.ModelViewSet):
    queryset = SensitiveWordSet.objects.all()
    serializer_class = SensitiveWordSetSerializer


class SensitiveWordViewSet(viewsets.ModelViewSet):
    queryset = SensitiveWord.objects.select_related("word_set").all()
    serializer_class = SensitiveWordSerializer


class PluginViewSet(viewsets.ModelViewSet):
    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer


class SceneViewSet(viewsets.ModelViewSet):
    queryset = Scene.objects.prefetch_related("knowledge_bases", "plugins").all()
    serializer_class = SceneSerializer


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatSession.objects.select_related("scene").prefetch_related("messages").all()
    serializer_class = ChatSessionSerializer


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer


class DashboardAPIView(APIView):
    def get(self, request):
        data = {
            "knowledge_base_count": KnowledgeBase.objects.count(),
            "document_count": KnowledgeDocument.objects.count(),
            "scene_count": Scene.objects.count(),
            "faq_count": FAQItem.objects.count(),
            "session_count": ChatSession.objects.count(),
            "message_count": ChatMessage.objects.count(),
            "recent_logs": OperationLogSerializer(OperationLog.objects.all()[:8], many=True).data,
            "scene_stats": list(
                Scene.objects.annotate(session_total=Count("sessions")).values("id", "name", "session_total")
            ),
        }
        return Response(data)


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        scene = Scene.objects.get(pk=data["scene_id"])
        session = ChatSession.objects.filter(pk=data.get("session_id")).first()
        if not session:
            session = ChatSession.objects.create(
                scene=scene,
                title=data["question"][:30],
                client_id=data.get("client_id", ""),
            )

        ChatMessage.objects.create(session=session, role="user", content=data["question"])
        result = process_chat(scene, data["question"], session)
        assistant_message = ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=result["answer"],
            sources=result["sources"],
            latency_ms=result["latency_ms"],
        )
        create_operation_log(
            "chat.answer",
            f"场景 {scene.name} 完成一次问答",
            {
                "session_id": session.id,
                "message_id": assistant_message.id,
                "provider_status": result.get("provider_status"),
            },
        )
        return Response(
            {
                "session_id": session.id,
                "answer": result["answer"],
                "sources": result["sources"],
                "latency_ms": result["latency_ms"],
                "blocked_words": result["blocked_words"],
                "provider_status": result.get("provider_status"),
            }
        )
