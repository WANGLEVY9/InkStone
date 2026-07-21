import { defineStore } from "pinia";
import { ref } from "vue";

import {
    cancelTask as cancelTaskApi,
    cloneTask as cloneTaskApi,
    createTask,
    deleteTask,
    listTasks,
    runTask as runTaskApi,
    TaskEntity,
    updateTask,
} from "../api/task";

export const useTaskStore = defineStore("task", () => {
    const tasks = ref<TaskEntity[]>([]);
    const loading = ref(false);

    const refresh = async () => {
        loading.value = true;
        try {
            const data = await listTasks();
            tasks.value = data.items;
        } finally {
            loading.value = false;
        }
    };

    const addTask = async (payload: Partial<TaskEntity>) => {
        await createTask(payload);
        await refresh();
    };

    const editTask = async (taskId: number, payload: Partial<TaskEntity>) => {
        await updateTask(taskId, payload);
        await refresh();
    };

    const removeTask = async (taskId: number) => {
        await deleteTask(taskId);
        await refresh();
    };

    const runTask = async (taskId: number) => {
        await runTaskApi(taskId);
        await refresh();
    };

    const cancelTask = async (taskId: number) => {
        await cancelTaskApi(taskId);
        await refresh();
    };

    const cloneTask = async (taskId: number) => {
        await cloneTaskApi(taskId);
        await refresh();
    };

    return { tasks, loading, refresh, addTask, editTask, removeTask, runTask, cancelTask, cloneTask };
});
