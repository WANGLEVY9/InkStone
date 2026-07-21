import client from "./client";

export interface ResultEntity {
    id: number;
    task_id: number;
    scores: Record<string, number>;
    raw_data: Record<string, unknown>;
    stats: Record<string, unknown>;
}

export interface SeedResult {
    message: string;
    seeded: number;
    tasks: string[];
}

export const listTaskResults = async (taskId: number) => {
    const { data } = await client.get<ResultEntity[]>(`/results/task/${taskId}`);
    return data;
};

export const compareResults = async (taskIds: number[]) => {
    const { data } = await client.post("/tasks/compare", { task_ids: taskIds });
    return data;
};

export const updateResultLabel = async (resultId: number, humanLabel: Record<string, unknown>) => {
    const { data } = await client.patch<ResultEntity>(`/results/${resultId}/label`, {
        human_label: humanLabel,
    });
    return data;
};

export const seedDemoData = async () => {
    const { data } = await client.post<SeedResult>("/demo/seed");
    return data;
};

export interface LlmJudgeReport {
    _id: string;
    ref_type: string;
    ref_id: string;
    context: Record<string, unknown>;
    assessment: {
        overall_score: number;
        dimension_scores: Record<string, number>;
        analysis: string;
        strengths: string[];
        weaknesses: string[];
        recommendations: string[];
        confidence: string;
    };
    created_at: string;
}

export const triggerLlmJudge = async (taskId: number) => {
    const { data } = await client.post<{ message: string }>(`/llm-judge/judge/task/${taskId}`);
    return data;
};

export const getLlmJudgeResult = async (refType: string, refId: string | number) => {
    const { data } = await client.get<LlmJudgeReport>(`/llm-judge/judge/result/${refType}/${refId}`);
    return data;
};
