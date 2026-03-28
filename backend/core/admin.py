from django.contrib import admin

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

for model in (
    KnowledgeBase,
    KnowledgeDocument,
    ModelProvider,
    FAQSet,
    FAQItem,
    SensitiveWordSet,
    SensitiveWord,
    Plugin,
    Scene,
    ChatSession,
    ChatMessage,
    OperationLog,
):
    admin.site.register(model)
