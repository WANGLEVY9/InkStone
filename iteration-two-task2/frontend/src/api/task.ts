import client from "./client";

export interface TaskConfig {
    metrics: string[];
    strategy: string;
    enable_process_trace: boolean;
}

export interface TaskEntity {
    id: number;
    name: string;
    description?: string;
    agent_id?: number | null;
    agent_version: string;
    dataset_id: string;
    mode: string;
    eval_mode?: string;
    method: string;
    dimension: string;
    status: string;
    config: TaskConfig;
    judge_config?: Record<string, unknown>;
    run_config?: Record<string, unknown>;
    metrics?: string[];
    input_payload: Record<string, unknown>;
    progress?: number;
    total_samples?: number;
    completed_samples?: number;
    failed_samples?: number;
    started_at?: string | null;
    finished_at?: string | null;
    error_message?: string | null;
    note?: string;
    created_at: string;
    updated_at: string;
}

export interface TaskListResponse {
    total: number;
    page: number;
    page_size: number;
    items: TaskEntity[];
}

export const listTasks = async () => {
    const { data } = await client.get<TaskListResponse>("/tasks/", { params: { page_size: 200 } });
    return data;
};

export const createTask = async (payload: Partial<TaskEntity>) => {
    const { data } = await client.post<TaskEntity>("/tasks/", payload);
    return data;
};

export const updateTask = async (taskId: number, payload: Partial<TaskEntity>) => {
    const { data } = await client.put<TaskEntity>(`/tasks/${taskId}`, payload);
    return data;
};

export const deleteTask = async (taskId: number) => {
    await client.delete(`/tasks/${taskId}`);
};

export const executeTask = async (taskId: number) => {
    const { data } = await client.post(`/tasks/${taskId}/execute`);
    return data;
};

export const runTask = async (taskId: number) => {
    const { data } = await client.post(`/tasks/${taskId}/run`);
    return data;
};

export const cancelTask = async (taskId: number) => {
    const { data } = await client.post(`/tasks/${taskId}/cancel`);
    return data;
};

export const cloneTask = async (taskId: number) => {
    const { data } = await client.post<TaskEntity>(`/tasks/${taskId}/clone`);
    return data;
};

export const compareTasks = async (taskIds: number[]) => {
    const { data } = await client.post("/tasks/compare", { task_ids: taskIds });
    return data;
};

export const exportTaskResults = async (taskId: number) => {
    const { data } = await client.get<string>(`/tasks/${taskId}/results/export?format=csv`);
    return data;
};
