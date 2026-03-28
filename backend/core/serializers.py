from rest_framework import serializers

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


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = "__all__"


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    documents = KnowledgeDocumentSerializer(many=True, read_only=True)
    document_count = serializers.IntegerField(source="documents.count", read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = "__all__"


class ModelProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProvider
        fields = "__all__"


class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = "__all__"


class FAQSetSerializer(serializers.ModelSerializer):
    items = FAQItemSerializer(many=True, read_only=True)

    class Meta:
        model = FAQSet
        fields = "__all__"


class SensitiveWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensitiveWord
        fields = "__all__"


class SensitiveWordSetSerializer(serializers.ModelSerializer):
    words = SensitiveWordSerializer(many=True, read_only=True)

    class Meta:
        model = SensitiveWordSet
        fields = "__all__"


class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = "__all__"


class SceneSerializer(serializers.ModelSerializer):
    knowledge_bases_detail = KnowledgeBaseSerializer(source="knowledge_bases", many=True, read_only=True)
    model_provider_detail = ModelProviderSerializer(source="model_provider", read_only=True)
    faq_set_detail = FAQSetSerializer(source="faq_set", read_only=True)
    sensitive_word_set_detail = SensitiveWordSetSerializer(source="sensitive_word_set", read_only=True)
    plugins_detail = PluginSerializer(source="plugins", many=True, read_only=True)

    class Meta:
        model = Scene
        fields = "__all__"


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    scene_detail = SceneSerializer(source="scene", read_only=True)

    class Meta:
        model = ChatSession
        fields = "__all__"


class OperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationLog
        fields = "__all__"


class ChatRequestSerializer(serializers.Serializer):
    scene_id = serializers.IntegerField()
    question = serializers.CharField()
    session_id = serializers.IntegerField(required=False, allow_null=True)
    client_id = serializers.CharField(required=False, allow_blank=True)
