# Smart QA 架构说明

## 后端

- 技术栈：Django + Django REST Framework
- 核心实体：知识库、知识文档、模型配置、FAQ、敏感词库、插件、场景、会话、消息、操作日志
- 关键接口：
  - `GET /api/dashboard/`
  - `POST /api/chat/`
  - `POST /api/knowledge-bases/{id}/upload/`
  - 其余资源均提供标准 RESTful CRUD

## 前端

- 技术栈：Vue 3 + Vite + Vue Router + Axios
- 页面：
  - 总览
  - 知识库管理
  - 场景配置
  - 智能问答工作台

## 当前 RAG 策略

- 初版使用轻量关键词匹配完成 FAQ 优先与知识库检索
- 文档上传后会原文入库，并尝试上传至 MinIO
- 后续可将 `core/services.py` 替换为向量检索、重排序和真实 LLM 调用
