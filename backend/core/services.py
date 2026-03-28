import math
import re
import time
import uuid
from typing import Iterable

import requests
from django.conf import settings
from minio import Minio
from minio.error import S3Error
from openai import BadRequestError, OpenAI
from urllib3 import PoolManager
from urllib3.exceptions import HTTPError

from .models import ChatSession, FAQItem, KnowledgeDocument, ModelProvider, OperationLog, Scene, SensitiveWord


def create_operation_log(action: str, detail: str = "", payload: dict | None = None, level: str = "info"):
    OperationLog.objects.create(action=action, detail=detail, payload=payload or {}, level=level)


def get_minio_client() -> Minio | None:
    if not settings.MINIO_ENDPOINT:
        return None
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        http_client=PoolManager(timeout=3.0),
    )


def ensure_bucket(bucket_name: str):
    client = get_minio_client()
    if not client:
        return
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_file_to_minio(file_obj, filename: str) -> tuple[str, str]:
    client = get_minio_client()
    if not client:
        return "", "minio_not_configured"
    try:
        ensure_bucket(settings.MINIO_RAW_BUCKET)
        object_name = f"{uuid.uuid4()}-{filename}"
        file_obj.seek(0)
        client.put_object(
            settings.MINIO_RAW_BUCKET,
            object_name,
            file_obj,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=getattr(file_obj, "content_type", "application/octet-stream"),
        )
        return object_name, "uploaded"
    except (S3Error, HTTPError, OSError, TimeoutError, Exception) as exc:
        return "", f"minio_unavailable:{exc.__class__.__name__}"


def read_file_text(uploaded_file) -> str:
    uploaded_file.seek(0)
    data = uploaded_file.read()
    if isinstance(data, str):
        return data
    for encoding in ("utf-8", "gbk", "gb18030", "latin1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def simple_score(question: str, text: str) -> float:
    tokens = [token for token in re.split(r"[\s,，。！？；:：/]+", question.lower()) if token]
    if not tokens:
        return 0.0
    text_lower = text.lower()
    hit_count = sum(1 for token in tokens if token in text_lower)
    return hit_count / len(tokens)


def filter_sensitive(text: str, words: Iterable[SensitiveWord]) -> tuple[bool, str, list[str]]:
    blocked = []
    filtered = text
    for item in words:
        if item.word and item.word in filtered:
            blocked.append(item.word)
            if item.reject_directly:
                return True, filtered, blocked
            filtered = filtered.replace(item.word, item.replace_with or "***")
    return False, filtered, blocked


def match_faq(scene: Scene, question: str):
    faq_set = scene.faq_set
    if not faq_set:
        return None
    threshold = float(faq_set.similarity_threshold)
    best_item = None
    best_score = 0.0
    for item in FAQItem.objects.filter(faq_set=faq_set, is_active=True):
        questions = [item.question, *item.alternate_questions]
        score = max(simple_score(question, candidate) for candidate in questions if candidate)
        if score > best_score:
            best_score = score
            best_item = item
    if best_item and best_score >= threshold:
        return {"answer": best_item.answer, "score": round(best_score, 2), "sources": ["FAQ"]}
    return None


def retrieve_documents(scene: Scene, question: str) -> list[dict]:
    docs = (
        KnowledgeDocument.objects.filter(knowledge_base__in=scene.knowledge_bases.all(), status="processed")
        .select_related("knowledge_base")
        .distinct()
    )
    ranked = []
    for doc in docs:
        score = simple_score(question, doc.content or "")
        if score > 0:
            ranked.append(
                {
                    "id": doc.id,
                    "title": doc.title,
                    "knowledge_base": doc.knowledge_base.name,
                    "score": round(score, 4),
                    "content": (doc.content or "")[:1600],
                }
            )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[: scene.top_k]


def build_context(scene: Scene, question: str, hits: list[dict]) -> str:
    if not hits:
        return (
            f"场景：{scene.name}\n"
            f"用户问题：{question}\n"
            "当前没有检索到相关知识库片段。请明确说明无法从现有资料中找到答案，不要编造。"
        )
    chunks = []
    for index, hit in enumerate(hits, start=1):
        chunks.append(
            f"[资料{index}] 知识库：{hit['knowledge_base']}；标题：{hit['title']}；内容：{hit['content']}"
        )
    return (
        f"场景：{scene.name}\n"
        f"用户问题：{question}\n\n"
        "你只能依据下面检索到的资料回答，并在必要时说明依据不足：\n"
        + "\n\n".join(chunks)
    )


def build_message_history(session: ChatSession | None) -> list[dict]:
    if not session:
        return []
    history = []
    for message in session.messages.all().order_by("created_at")[:12]:
        if message.role not in {"user", "assistant"}:
            continue
        history.append({"role": message.role, "content": message.content})
    return history


def create_openai_completion(client: OpenAI, provider: ModelProvider, messages: list[dict], temperature: float):
    return client.chat.completions.create(
        model=provider.model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=provider.max_tokens,
    )


def build_fallback_answer(question: str, hits: list[dict]) -> tuple[str, list[dict]]:
    if not hits:
        return "抱歉，我暂时无法在现有资料中找到答案。", []
    snippets = [f"[{hit['knowledge_base']}/{hit['title']}] {hit['content'][:220]}" for hit in hits]
    answer = (
        f"基于当前知识库，我找到 {len(hits)} 条相关内容。\n\n"
        f"问题：{question}\n\n"
        "参考摘要：\n"
        + "\n".join(f"{idx + 1}. {text}" for idx, text in enumerate(snippets))
        + "\n\n建议你优先核对以上资料原文；如果需要，我可以继续针对某一条资料展开。"
    )
    return answer, hits


def resolve_provider_endpoint(provider: ModelProvider) -> str:
    base = (provider.api_base or "").rstrip("/")
    if provider.provider_type in ("openai", "custom"):
        return f"{base}/chat/completions" if not base.endswith("/chat/completions") else base
    if provider.provider_type == "ollama":
        return f"{base}/api/generate" if not base.endswith("/api/generate") else base
    return base


def call_openai_compatible(
    provider: ModelProvider, scene: Scene, question: str, hits: list[dict], session: ChatSession | None
) -> str:
    base_url = (provider.api_base or "").rstrip("/")
    if not base_url:
        raise ValueError("模型未配置 API Base URL")
    if not provider.api_key:
        raise ValueError("模型未配置 API Key")

    client = OpenAI(api_key=provider.api_key, base_url=base_url)
    messages = [{"role": "system", "content": scene.system_prompt}]
    messages.extend(build_message_history(session))
    messages.append({"role": "user", "content": build_context(scene, question, hits)})
    temperature = float(provider.temperature)
    try:
        completion = create_openai_completion(client, provider, messages, temperature)
    except BadRequestError as exc:
        error_text = str(exc)
        if "invalid temperature" in error_text and "only 1 is allowed" in error_text:
            completion = create_openai_completion(client, provider, messages, 1.0)
        else:
            raise
    return completion.choices[0].message.content.strip()


def call_ollama(
    provider: ModelProvider, scene: Scene, question: str, hits: list[dict], session: ChatSession | None
) -> str:
    endpoint = resolve_provider_endpoint(provider)
    if not endpoint:
        raise ValueError("模型未配置 Ollama 地址")
    history_text = []
    for message in build_message_history(session):
        role = "用户" if message["role"] == "user" else "助手"
        history_text.append(f"{role}: {message['content']}")
    prompt = (
        f"{scene.system_prompt}\n\n"
        + ("\n".join(history_text) + "\n\n" if history_text else "")
        + build_context(scene, question, hits)
    )
    payload = {
        "model": provider.model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(provider.temperature),
            "num_predict": provider.max_tokens,
        },
    }
    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def generate_llm_answer(
    scene: Scene, question: str, hits: list[dict], session: ChatSession | None
) -> tuple[str | None, str | None]:
    provider = scene.model_provider
    if not provider or not provider.is_active:
        return None, "no_model_provider"
    try:
        if provider.provider_type == "ollama":
            return call_ollama(provider, scene, question, hits, session), None
        return call_openai_compatible(provider, scene, question, hits, session), None
    except requests.RequestException as exc:
        return None, f"llm_request_error:{exc.__class__.__name__}"
    except Exception as exc:
        return None, f"llm_config_error:{exc}"


def process_chat(scene: Scene, question: str, session: ChatSession | None = None) -> dict:
    start = time.perf_counter()
    blocked_words = []

    if scene.sensitive_word_set:
        blocked, filtered_question, blocked_words = filter_sensitive(
            question, SensitiveWord.objects.filter(word_set=scene.sensitive_word_set)
        )
        if blocked:
            return {
                "answer": "当前问题包含敏感内容，系统已拒绝处理。",
                "sources": [],
                "latency_ms": math.ceil((time.perf_counter() - start) * 1000),
                "blocked_words": blocked_words,
                "provider_status": "blocked_by_sensitive_words",
            }
        question = filtered_question

    faq_result = match_faq(scene, question)
    if faq_result:
        faq_result["latency_ms"] = math.ceil((time.perf_counter() - start) * 1000)
        faq_result["blocked_words"] = blocked_words
        faq_result["provider_status"] = "faq"
        return faq_result

    hits = retrieve_documents(scene, question)
    answer, provider_status = generate_llm_answer(scene, question, hits, session)
    if not answer:
        answer, _ = build_fallback_answer(question, hits)

    if scene.sensitive_word_set:
        blocked, filtered_answer, output_blocked = filter_sensitive(
            answer, SensitiveWord.objects.filter(word_set=scene.sensitive_word_set)
        )
        blocked_words.extend(output_blocked)
        answer = "系统回答包含敏感内容，已被拦截。" if blocked else filtered_answer

    return {
        "answer": answer,
        "sources": hits,
        "latency_ms": math.ceil((time.perf_counter() - start) * 1000),
        "blocked_words": blocked_words,
        "provider_status": provider_status or "llm",
    }
