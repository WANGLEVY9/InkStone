import { createRouter, createWebHistory } from "vue-router";

import TaskManagementView from "./views/TaskManagementView.vue";
import ConfigView from "./views/ConfigView.vue";
import ResultsView from "./views/ResultsView.vue";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: "/", redirect: "/tasks" },
        { path: "/tasks", component: TaskManagementView },
        { path: "/config", component: ConfigView },
        { path: "/results", component: ResultsView },
        { path: "/mode/realtime", redirect: "/tasks" },
        { path: "/mode/offline-trace", redirect: "/tasks" },
        { path: "/mode/dataset-batch", redirect: "/tasks" },
    ],
});

export default router;
