import client from "./client";

export interface MetricEntity {
    id: number;
    name: string;
    metric_type: string;
    logic_type: string;
    ragas_config: Record<string, unknown>;
    description?: string;
    created_at: string;
    updated_at: string;
}

export const listMetrics = async () => {
    const { data } = await client.get<MetricEntity[]>("/metrics/");
    return data;
};

export const createMetric = async (payload: Partial<MetricEntity> & { name: string }) => {
    const { data } = await client.post<MetricEntity>("/metrics/", payload);
    return data;
};

export const deleteMetric = async (metricId: number) => {
    await client.delete(`/metrics/${metricId}`);
};
