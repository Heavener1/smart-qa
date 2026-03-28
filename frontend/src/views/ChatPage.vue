<template>
  <section class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">Workspace</p>
        <h2>智能问答工作台</h2>
      </div>
      <button class="ghost" @click="bootstrap">刷新会话</button>
    </div>

    <div class="grid chat-layout reverse-chat-layout">
      <section class="panel session-panel wide-session-panel">
        <div class="panel-head">
          <h3>会话记录</h3>
          <button class="ghost" @click="createNewSession">新建会话</button>
        </div>
        <div class="session-list scroller">
          <button
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: sessionId === session.id }"
            @click="selectSession(session)"
          >
            <strong>{{ session.title || `会话 #${session.id}` }}</strong>
            <span>{{ session.scene_detail?.name || "未命名场景" }}</span>
          </button>
        </div>
      </section>

      <section class="panel chat-panel">
        <div class="panel-head">
          <h3>{{ currentSessionTitle }}</h3>
          <span class="badge" v-if="providerStatus">{{ providerStatus }}</span>
        </div>

        <div class="messages scroller">
          <article
            class="message"
            :class="message.role === 'user' ? 'message-user' : 'message-assistant'"
            v-for="message in messages"
            :key="message.id"
          >
            <span class="role">{{ message.role === "user" ? "我" : "助手" }}</span>
            <p>{{ message.content }}</p>
            <small v-if="message.sources?.length">来源：{{ formatSources(message.sources) }}</small>
          </article>
          <article class="message message-assistant thinking" v-if="isThinking">
            <span class="role">助手</span>
            <p>正在思考中...</p>
          </article>
        </div>

        <form class="chat-form" @submit.prevent="submit">
          <div class="composer-toolbar">
            <select class="scene-select small" v-model="sceneId">
              <option value="">请选择场景</option>
              <option v-for="scene in scenes" :key="scene.id" :value="scene.id">{{ scene.name }}</option>
            </select>
            <span class="muted current-scene">当前场景：{{ currentSceneName }}</span>
          </div>
          <textarea v-model="question" rows="4" placeholder="请输入你的问题"></textarea>
          <button type="submit" :disabled="isThinking">发送问题</button>
        </form>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { askQuestion, fetchScenes, fetchSessions } from "../api";

const scenes = ref([]);
const sessions = ref([]);
const sceneId = ref("");
const sessionId = ref(null);
const question = ref("");
const messages = ref([]);
const providerStatus = ref("");
const isThinking = ref(false);

const currentSessionTitle = computed(() => {
  const current = sessions.value.find((item) => item.id === sessionId.value);
  return current?.title || "新会话";
});

const currentSceneName = computed(() => {
  const current = scenes.value.find((item) => item.id === sceneId.value);
  return current?.name || "未选择";
});

function formatSources(sources) {
  return sources.map((item) => item.title || item).join("、");
}

async function bootstrap() {
  const [sceneRes, sessionRes] = await Promise.all([fetchScenes(), fetchSessions()]);
  scenes.value = sceneRes.data.results || sceneRes.data;
  sessions.value = sessionRes.data.results || sessionRes.data;
  if (!sceneId.value && scenes.value.length) {
    sceneId.value = scenes.value[0].id;
  }
}

function createNewSession() {
  sessionId.value = null;
  messages.value = [];
  providerStatus.value = "";
  isThinking.value = false;
}

function selectSession(session) {
  sessionId.value = session.id;
  sceneId.value = session.scene;
  providerStatus.value = "";
  messages.value = (session.messages || []).map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
    sources: item.sources,
  }));
}

async function submit() {
  if (!sceneId.value || !question.value.trim() || isThinking.value) return;

  const currentQuestion = question.value.trim();
  messages.value.push({ id: `${Date.now()}-u`, role: "user", content: currentQuestion });
  isThinking.value = true;

  try {
    const payload = {
      scene_id: sceneId.value,
      question: currentQuestion,
      client_id: "web-console",
    };
    if (sessionId.value) {
      payload.session_id = sessionId.value;
    }

    const { data } = await askQuestion(payload);
    sessionId.value = data.session_id;
    providerStatus.value = data.provider_status || "";
    messages.value.push({
      id: `${Date.now()}-a`,
      role: "assistant",
      content: data.answer,
      sources: data.sources,
    });
    question.value = "";
    await bootstrap();
  } finally {
    isThinking.value = false;
  }
}

onMounted(bootstrap);
</script>
