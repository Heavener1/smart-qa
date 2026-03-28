<template>
  <section class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">Configuration</p>
        <h2>场景、大模型与规则配置</h2>
      </div>
      <div class="action-row">
        <button class="ghost" @click="bootstrap">刷新</button>
        <button @click="openModelModal()">新增大模型</button>
        <button @click="openSceneModal()">新增场景</button>
      </div>
    </div>

    <div class="grid two">
      <section class="panel">
        <div class="panel-head">
          <h3>大模型列表</h3>
          <span class="muted">已配模型直接展示，修改走弹窗</span>
        </div>
        <div class="data-list">
          <article class="data-card" v-for="model in models" :key="model.id">
            <div class="card-main">
              <div>
                <h4>{{ model.name }}</h4>
                <p class="muted">{{ model.provider_type }} / {{ model.model_name }}</p>
              </div>
              <div class="badge-row">
                <span class="badge">{{ model.api_base || "未配置 API Base" }}</span>
                <span class="badge">{{ model.api_key ? "已配置 API Key" : "未配置 API Key" }}</span>
              </div>
            </div>
            <div class="action-row">
              <button class="ghost" @click="openModelModal(model)">修改</button>
              <button class="ghost danger" @click="removeModel(model)">删除</button>
            </div>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>场景列表</h3>
          <span class="muted">已配场景直接展示，修改走弹窗</span>
        </div>
        <div class="data-list">
          <article class="data-card" v-for="scene in scenes" :key="scene.id">
            <div class="card-main">
              <div>
                <h4>{{ scene.name }}</h4>
                <p class="muted">{{ scene.description || "暂无描述" }}</p>
              </div>
              <div class="badge-row">
                <span class="badge">{{ scene.model_provider_detail?.name || "未绑定模型" }}</span>
                <span class="badge">Top K {{ scene.top_k }}</span>
              </div>
            </div>
            <div class="meta-block">
              <strong>关联知识库</strong>
              <p class="muted">{{ formatKnowledge(scene) }}</p>
            </div>
            <div class="action-row">
              <button class="ghost" @click="openSceneModal(scene)">修改</button>
              <button class="ghost danger" @click="removeScene(scene)">删除</button>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div class="grid two">
      <section class="panel">
        <div class="panel-head">
          <h3>FAQ 库</h3>
          <button @click="submitFaq">新增 FAQ 库</button>
        </div>
        <div class="action-row form-inline">
          <input v-model="faqForm.name" placeholder="FAQ 库名称" />
          <input v-model="faqForm.description" placeholder="FAQ 描述" />
        </div>
        <div class="data-list">
          <article class="data-card" v-for="item in faqSets" :key="`faq-${item.id}`">
            <div class="card-main">
              <div>
                <h4>{{ item.name }}</h4>
                <p class="muted">{{ item.description || "暂无描述" }}</p>
              </div>
              <div class="badge-row">
                <span class="badge">阈值 {{ item.similarity_threshold }}</span>
                <span class="badge">{{ item.is_active ? "启用中" : "已停用" }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3>敏感词库</h3>
          <button @click="submitWords">新增敏感词库</button>
        </div>
        <div class="action-row form-inline">
          <input v-model="wordForm.name" placeholder="敏感词库名称" />
          <input v-model="wordForm.description" placeholder="敏感词库描述" />
        </div>
        <div class="data-list">
          <article class="data-card" v-for="item in wordSets" :key="`word-${item.id}`">
            <div class="card-main">
              <div>
                <h4>{{ item.name }}</h4>
                <p class="muted">{{ item.description || "暂无描述" }}</p>
              </div>
              <div class="badge-row">
                <span class="badge">{{ item.is_active ? "启用中" : "已停用" }}</span>
                <span class="badge">词条 {{ item.words?.length || 0 }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-if="showModelModal" class="modal-mask" @click.self="closeModelModal">
      <div class="modal">
        <div class="panel-head">
          <h3>{{ editingModelId ? "修改大模型" : "新增大模型" }}</h3>
          <button class="ghost" @click="closeModelModal">关闭</button>
        </div>
        <form class="form" @submit.prevent="submitModel">
          <input v-model="modelForm.name" placeholder="模型名称" required />
          <select v-model="modelForm.provider_type">
            <option value="custom">自定义</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
          <input v-model="modelForm.model_name" placeholder="模型 ID，例如 kimi-k2.5" required />
          <input v-model="modelForm.api_base" placeholder="API Base URL" />
          <input v-model="modelForm.api_key" placeholder="API Key" />
          <div class="grid two compact-grid">
            <input v-model.number="modelForm.context_window" type="number" min="1" placeholder="上下文窗口" />
            <input v-model.number="modelForm.max_tokens" type="number" min="1" placeholder="最大输出 Token" />
          </div>
          <input v-model.number="modelForm.temperature" type="number" step="0.1" min="0" max="1" placeholder="温度" />
          <p class="note">问答后端会优先用这里配置的模型发起真实调用，建议把 `base_url` 和 `api_key` 配完整。</p>
          <button type="submit">{{ editingModelId ? "保存修改" : "创建模型" }}</button>
        </form>
      </div>
    </div>

    <div v-if="showSceneModal" class="modal-mask" @click.self="closeSceneModal">
      <div class="modal large">
        <div class="panel-head">
          <h3>{{ editingSceneId ? "修改场景" : "新增场景" }}</h3>
          <button class="ghost" @click="closeSceneModal">关闭</button>
        </div>
        <form class="form" @submit.prevent="submitScene">
          <div class="grid two">
            <input v-model="sceneForm.name" placeholder="场景名称" required />
            <input v-model="sceneForm.description" placeholder="场景描述" />
          </div>
          <textarea v-model="sceneForm.system_prompt" rows="5" placeholder="系统提示词"></textarea>
          <div class="grid three">
            <select v-model="sceneForm.model_provider">
              <option :value="null">选择模型</option>
              <option v-for="item in models" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
            <select v-model="sceneForm.faq_set">
              <option :value="null">选择 FAQ 库</option>
              <option v-for="item in faqSets" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
            <select v-model="sceneForm.sensitive_word_set">
              <option :value="null">选择敏感词库</option>
              <option v-for="item in wordSets" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <label class="stack">
            <span>关联知识库</span>
            <select v-model="sceneForm.knowledge_bases" multiple size="5">
              <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </label>
          <div class="grid two compact-grid">
            <label class="inline-option">
              <input v-model="sceneForm.enable_rerank" type="checkbox" />
              <span>启用重排占位配置</span>
            </label>
            <input v-model.number="sceneForm.top_k" type="number" min="1" placeholder="Top K" />
          </div>
          <button type="submit">{{ editingSceneId ? "保存修改" : "创建场景" }}</button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import {
  createFaqSet,
  createModel,
  createScene,
  createSensitiveWordSet,
  deleteModel,
  deleteScene,
  fetchFaqSets,
  fetchKnowledgeBases,
  fetchModels,
  fetchScenes,
  fetchSensitiveWordSets,
  updateModel,
  updateScene,
} from "../api";

const knowledgeBases = ref([]);
const models = ref([]);
const faqSets = ref([]);
const wordSets = ref([]);
const scenes = ref([]);

const editingModelId = ref(null);
const editingSceneId = ref(null);
const showModelModal = ref(false);
const showSceneModal = ref(false);

const createDefaultModelForm = () => ({
  name: "",
  provider_type: "custom",
  model_name: "",
  api_base: "",
  api_key: "",
  context_window: 16000,
  temperature: 0.3,
  max_tokens: 1024,
});

const createDefaultSceneForm = () => ({
  name: "",
  description: "",
  system_prompt: "你是企业知识库助手，请仅根据提供的知识库上下文作答；如果没有相关信息，请明确说明。",
  model_provider: null,
  faq_set: null,
  sensitive_word_set: null,
  knowledge_bases: [],
  plugins: [],
  top_k: 5,
  enable_rerank: false,
  is_active: true,
});

const modelForm = ref(createDefaultModelForm());
const sceneForm = ref(createDefaultSceneForm());
const faqForm = ref({ name: "", description: "" });
const wordForm = ref({ name: "", description: "" });

async function bootstrap() {
  const [kbRes, modelRes, faqRes, wordRes, sceneRes] = await Promise.all([
    fetchKnowledgeBases(),
    fetchModels(),
    fetchFaqSets(),
    fetchSensitiveWordSets(),
    fetchScenes(),
  ]);
  knowledgeBases.value = kbRes.data.results || kbRes.data;
  models.value = modelRes.data.results || modelRes.data;
  faqSets.value = faqRes.data.results || faqRes.data;
  wordSets.value = wordRes.data.results || wordRes.data;
  scenes.value = sceneRes.data.results || sceneRes.data;
}

function openModelModal(model = null) {
  editingModelId.value = model?.id || null;
  modelForm.value = model
    ? {
        name: model.name,
        provider_type: model.provider_type,
        model_name: model.model_name,
        api_base: model.api_base || "",
        api_key: model.api_key || "",
        context_window: model.context_window || 16000,
        temperature: Number(model.temperature ?? 0.3),
        max_tokens: model.max_tokens || 1024,
      }
    : createDefaultModelForm();
  showModelModal.value = true;
}

function closeModelModal() {
  showModelModal.value = false;
}

function openSceneModal(scene = null) {
  editingSceneId.value = scene?.id || null;
  sceneForm.value = scene
    ? {
        name: scene.name,
        description: scene.description || "",
        system_prompt: scene.system_prompt || "",
        model_provider: scene.model_provider,
        faq_set: scene.faq_set,
        sensitive_word_set: scene.sensitive_word_set,
        knowledge_bases: scene.knowledge_bases || [],
        plugins: scene.plugins || [],
        top_k: scene.top_k || 5,
        enable_rerank: scene.enable_rerank,
        is_active: scene.is_active,
      }
    : createDefaultSceneForm();
  showSceneModal.value = true;
}

function closeSceneModal() {
  showSceneModal.value = false;
}

async function submitModel() {
  if (editingModelId.value) {
    await updateModel(editingModelId.value, modelForm.value);
  } else {
    await createModel(modelForm.value);
  }
  closeModelModal();
  await bootstrap();
}

async function removeModel(model) {
  if (!window.confirm(`确认删除模型“${model.name}”吗？`)) return;
  await deleteModel(model.id);
  await bootstrap();
}

async function submitScene() {
  if (editingSceneId.value) {
    await updateScene(editingSceneId.value, sceneForm.value);
  } else {
    await createScene(sceneForm.value);
  }
  closeSceneModal();
  await bootstrap();
}

async function removeScene(scene) {
  if (!window.confirm(`确认删除场景“${scene.name}”吗？`)) return;
  await deleteScene(scene.id);
  await bootstrap();
}

async function submitFaq() {
  if (!faqForm.value.name.trim()) return;
  await createFaqSet(faqForm.value);
  faqForm.value = { name: "", description: "" };
  await bootstrap();
}

async function submitWords() {
  if (!wordForm.value.name.trim()) return;
  await createSensitiveWordSet(wordForm.value);
  wordForm.value = { name: "", description: "" };
  await bootstrap();
}

function formatKnowledge(scene) {
  return (scene.knowledge_bases_detail || []).map((item) => item.name).join("、") || "未关联知识库";
}

onMounted(bootstrap);
</script>
