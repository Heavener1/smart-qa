<template>
  <section class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">Overview</p>
        <h2>系统总览</h2>
      </div>
      <button class="ghost" @click="load">刷新数据</button>
    </div>

    <div class="stats-grid">
      <article class="stat-card" v-for="item in cards" :key="item.label">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>

    <div class="grid two">
      <section class="panel">
        <h3>场景会话统计</h3>
        <div class="list">
          <div class="list-row" v-for="item in dashboard.scene_stats || []" :key="item.id">
            <span>{{ item.name }}</span>
            <strong>{{ item.session_total }}</strong>
          </div>
        </div>
      </section>
      <section class="panel">
        <h3>最近日志</h3>
        <div class="list">
          <div class="list-row" v-for="log in dashboard.recent_logs || []" :key="log.id">
            <span>{{ log.action }}</span>
            <small>{{ log.detail || "无详情" }}</small>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive } from "vue";
import { fetchDashboard } from "../api";

const dashboard = reactive({});

const cards = computed(() => [
  { label: "知识库", value: dashboard.knowledge_base_count || 0 },
  { label: "文档", value: dashboard.document_count || 0 },
  { label: "场景", value: dashboard.scene_count || 0 },
  { label: "FAQ", value: dashboard.faq_count || 0 },
  { label: "会话", value: dashboard.session_count || 0 },
  { label: "消息", value: dashboard.message_count || 0 },
]);

async function load() {
  const { data } = await fetchDashboard();
  Object.assign(dashboard, data);
}

onMounted(load);
</script>
