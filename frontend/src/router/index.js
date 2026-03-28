import { createRouter, createWebHistory } from "vue-router";

import ChatPage from "../views/ChatPage.vue";
import DashboardPage from "../views/DashboardPage.vue";
import KnowledgePage from "../views/KnowledgePage.vue";
import ScenePage from "../views/ScenePage.vue";

const routes = [
  { path: "/", component: DashboardPage },
  { path: "/knowledge", component: KnowledgePage },
  { path: "/scenes", component: ScenePage },
  { path: "/chat", component: ChatPage },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
