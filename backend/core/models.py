from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class KnowledgeBase(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    embedding_model = models.CharField(max_length=120, default="simple-keyword")
    chunk_size = models.PositiveIntegerField(default=1000)
    chunk_overlap = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class KnowledgeDocument(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PROCESSED = "processed", "已处理"
        FAILED = "failed", "失败"

    knowledge_base = models.ForeignKey(
        KnowledgeBase, related_name="documents", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    object_name = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ModelProvider(TimeStampedModel):
    class ProviderType(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        OLLAMA = "ollama", "Ollama"
        CUSTOM = "custom", "自定义"

    name = models.CharField(max_length=120, unique=True)
    provider_type = models.CharField(max_length=20, choices=ProviderType.choices)
    model_name = models.CharField(max_length=120)
    api_base = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    context_window = models.PositiveIntegerField(default=16000)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.30)
    max_tokens = models.PositiveIntegerField(default=1024)
    is_active = models.BooleanField(default=True)
    extra_config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FAQSet(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    similarity_threshold = models.DecimalField(max_digits=4, decimal_places=2, default=0.75)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FAQItem(TimeStampedModel):
    faq_set = models.ForeignKey(FAQSet, related_name="items", on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    alternate_questions = models.JSONField(default=list, blank=True)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["question"]

    def __str__(self):
        return self.question


class SensitiveWordSet(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SensitiveWord(TimeStampedModel):
    word_set = models.ForeignKey(
        SensitiveWordSet, related_name="words", on_delete=models.CASCADE
    )
    word = models.CharField(max_length=120)
    replace_with = models.CharField(max_length=120, blank=True)
    reject_directly = models.BooleanField(default=False)

    class Meta:
        unique_together = ("word_set", "word")
        ordering = ["word"]

    def __str__(self):
        return self.word


class Plugin(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=120, unique=True)
    parameters = models.JSONField(default=list, blank=True)
    is_builtin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Scene(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    system_prompt = models.TextField(
        default="你是企业知识库助手，请仅根据提供的知识库上下文作答；如果没有相关信息，请明确说明。"
    )
    knowledge_bases = models.ManyToManyField(KnowledgeBase, blank=True, related_name="scenes")
    model_provider = models.ForeignKey(
        ModelProvider,
        related_name="scenes",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    faq_set = models.ForeignKey(
        FAQSet, related_name="scenes", on_delete=models.SET_NULL, blank=True, null=True
    )
    sensitive_word_set = models.ForeignKey(
        SensitiveWordSet,
        related_name="scenes",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    plugins = models.ManyToManyField(Plugin, blank=True, related_name="scenes")
    enable_rerank = models.BooleanField(default=False)
    top_k = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ChatSession(TimeStampedModel):
    scene = models.ForeignKey(Scene, related_name="sessions", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    client_id = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"{self.scene.name}-{self.pk}"


class ChatMessage(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "用户"
        ASSISTANT = "assistant", "助手"
        SYSTEM = "system", "系统"

    session = models.ForeignKey(ChatSession, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]


class OperationLog(TimeStampedModel):
    level = models.CharField(max_length=20, default="info")
    action = models.CharField(max_length=120)
    detail = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
