import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api",
});

export const fetchDashboard = () => api.get("/dashboard/");

export const fetchKnowledgeBases = () => api.get("/knowledge-bases/");
export const createKnowledgeBase = (payload) => api.post("/knowledge-bases/", payload);
export const updateKnowledgeBase = (id, payload) => api.patch(`/knowledge-bases/${id}/`, payload);
export const deleteKnowledgeBase = (id) => api.delete(`/knowledge-bases/${id}/`);
export const uploadKnowledgeFile = (id, formData) =>
  api.post(`/knowledge-bases/${id}/upload/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const fetchScenes = () => api.get("/scenes/");
export const createScene = (payload) => api.post("/scenes/", payload);
export const updateScene = (id, payload) => api.patch(`/scenes/${id}/`, payload);
export const deleteScene = (id) => api.delete(`/scenes/${id}/`);

export const fetchModels = () => api.get("/models/");
export const createModel = (payload) => api.post("/models/", payload);
export const updateModel = (id, payload) => api.patch(`/models/${id}/`, payload);
export const deleteModel = (id) => api.delete(`/models/${id}/`);

export const fetchFaqSets = () => api.get("/faq-sets/");
export const createFaqSet = (payload) => api.post("/faq-sets/", payload);
export const fetchSensitiveWordSets = () => api.get("/sensitive-word-sets/");
export const createSensitiveWordSet = (payload) => api.post("/sensitive-word-sets/", payload);
export const fetchSessions = () => api.get("/sessions/");
export const askQuestion = (payload) => api.post("/chat/", payload);
