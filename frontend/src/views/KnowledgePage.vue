<template>
  <section class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">Knowledge</p>
        <h2>知识库管理</h2>
      </div>
      <div class="action-row">
        <button class="ghost" @click="load">刷新</button>
        <button @click="openCreateModal">新增知识库</button>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3>知识库列表</h3>
        <span class="muted">点开即看全部，新增和编辑都通过弹窗完成</span>
      </div>
      <div class="data-list">
        <article class="data-card" v-for="item in knowledgeBases" :key="item.id">
          <div class="card-main">
            <div>
              <h4>{{ item.name }}</h4>
              <p class="muted">{{ item.description || "暂无描述" }}</p>
            </div>
            <div class="badge-row">
              <span class="badge">文档 {{ item.document_count || item.documents?.length || 0 }}</span>
              <span class="badge">{{ item.embedding_model }}</span>
            </div>
          </div>
          <div class="meta-block">
            <strong>文档概览</strong>
            <p class="muted">
              {{
                (item.documents || [])
                  .slice(0, 2)
                  .map((doc) => `${doc.title}（${doc.metadata?.storage_status || "未标记"}）`)
                  .join("；") || "当前还没有上传文档"
              }}
            </p>
          </div>
          <div class="action-row">
            <button class="ghost" @click="openEditModal(item)">修改</button>
            <button class="ghost" @click="openUploadModal(item)">上传文档</button>
            <button class="ghost danger" @click="removeKb(item)">删除</button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="showFormModal" class="modal-mask" @click.self="closeFormModal">
      <div class="modal">
        <div class="panel-head">
          <h3>{{ editingId ? "修改知识库" : "新增知识库" }}</h3>
          <button class="ghost" @click="closeFormModal">关闭</button>
        </div>
        <form class="form" @submit.prevent="submitKb">
          <input v-model="form.name" placeholder="知识库名称" required />
          <textarea v-model="form.description" rows="4" placeholder="知识库描述"></textarea>
          <button type="submit">{{ editingId ? "保存修改" : "创建知识库" }}</button>
        </form>
      </div>
    </div>

    <div v-if="showUploadModal" class="modal-mask" @click.self="closeUploadModal">
      <div class="modal">
        <div class="panel-head">
          <h3>上传文档到 {{ upload.knowledgeBaseName }}</h3>
          <button class="ghost" @click="closeUploadModal">关闭</button>
        </div>
        <p class="note">MinIO 不可用时，系统会自动降级为仅保存文本内容和元数据。</p>
        <form class="form" @submit.prevent="submitUpload">
          <input v-model="upload.title" placeholder="文档标题，可选" />
          <input type="file" @change="onFileChange" required />
          <button type="submit">开始上传</button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  fetchKnowledgeBases,
  updateKnowledgeBase,
  uploadKnowledgeFile,
} from "../api";

const knowledgeBases = ref([]);
const editingId = ref(null);
const showFormModal = ref(false);
const showUploadModal = ref(false);
const form = ref({ name: "", description: "" });
const upload = ref({ knowledgeBaseId: "", knowledgeBaseName: "", title: "", file: null });

async function load() {
  const { data } = await fetchKnowledgeBases();
  knowledgeBases.value = data.results || data;
}

function openCreateModal() {
  editingId.value = null;
  form.value = { name: "", description: "" };
  showFormModal.value = true;
}

function openEditModal(item) {
  editingId.value = item.id;
  form.value = { name: item.name, description: item.description || "" };
  showFormModal.value = true;
}

function closeFormModal() {
  showFormModal.value = false;
}

function openUploadModal(item) {
  upload.value = {
    knowledgeBaseId: item.id,
    knowledgeBaseName: item.name,
    title: "",
    file: null,
  };
  showUploadModal.value = true;
}

function closeUploadModal() {
  showUploadModal.value = false;
}

async function submitKb() {
  if (editingId.value) {
    await updateKnowledgeBase(editingId.value, form.value);
  } else {
    await createKnowledgeBase(form.value);
  }
  closeFormModal();
  await load();
}

async function removeKb(item) {
  if (!window.confirm(`确认删除知识库“${item.name}”吗？`)) return;
  await deleteKnowledgeBase(item.id);
  await load();
}

function onFileChange(event) {
  upload.value.file = event.target.files[0];
}

async function submitUpload() {
  const formData = new FormData();
  formData.append("title", upload.value.title);
  formData.append("file", upload.value.file);
  await uploadKnowledgeFile(upload.value.knowledgeBaseId, formData);
  closeUploadModal();
  await load();
}

onMounted(load);
</script>
