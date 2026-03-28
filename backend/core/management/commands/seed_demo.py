from django.core.management.base import BaseCommand

from core.models import FAQItem, FAQSet, KnowledgeBase, ModelProvider, Plugin, Scene, SensitiveWord, SensitiveWordSet


class Command(BaseCommand):
    help = "初始化演示数据"

    def handle(self, *args, **options):
        kb, _ = KnowledgeBase.objects.get_or_create(
            name="企业通用知识库",
            defaults={"description": "用于演示的默认知识库"},
        )
        model, _ = ModelProvider.objects.get_or_create(
            name="默认模型",
            defaults={
                "provider_type": "custom",
                "model_name": "simple-rag",
                "api_base": "",
                "api_key": "",
            },
        )
        faq_set, _ = FAQSet.objects.get_or_create(
            name="基础FAQ",
            defaults={"description": "常见问题库"},
        )
        FAQItem.objects.get_or_create(
            faq_set=faq_set,
            question="系统支持哪些文件格式？",
            defaults={
                "alternate_questions": ["可以上传什么文件", "知识库支持哪些文档"],
                "answer": "当前初版支持 TXT/Markdown 文本直传，后续可扩展 PDF、Word、PPT、图片 OCR。",
            },
        )
        word_set, _ = SensitiveWordSet.objects.get_or_create(
            name="默认敏感词库",
            defaults={"description": "演示用"},
        )
        SensitiveWord.objects.get_or_create(
            word_set=word_set,
            word="机密",
            defaults={"replace_with": "***", "reject_directly": False},
        )
        plugin, _ = Plugin.objects.get_or_create(
            code="weather_query",
            defaults={
                "name": "天气查询插件",
                "description": "预留的天气查询插件占位",
                "parameters": [{"name": "city", "type": "string", "required": True}],
                "is_builtin": True,
            },
        )
        scene, created = Scene.objects.get_or_create(
            name="IT助手",
            defaults={
                "description": "用于演示企业 IT 支持场景",
                "model_provider": model,
                "faq_set": faq_set,
                "sensitive_word_set": word_set,
                "top_k": 5,
            },
        )
        scene.knowledge_bases.add(kb)
        scene.plugins.add(plugin)
        message = "演示数据已初始化" if created else "演示数据已补齐"
        self.stdout.write(self.style.SUCCESS(message))
