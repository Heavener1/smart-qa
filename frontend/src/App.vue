<template>
  <div class="shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Django + Vue</p>
        <h1>智能问答系统</h1>
        <p class="muted">知识库、场景配置、FAQ、敏感词与对话工作台</p>
      </div>
      <nav class="nav">
        <RouterLink to="/">总览</RouterLink>
        <RouterLink to="/knowledge">知识库</RouterLink>
        <RouterLink to="/scenes">场景配置</RouterLink>
        <RouterLink to="/chat">智能问答</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <span>MySQL / MinIO / Redis 已预置环境变量</span>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
</script>
