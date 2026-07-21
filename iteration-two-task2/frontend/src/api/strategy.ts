import client from "./client";

export interface StrategyEntity {
    id?: number;
    name: string;
    weights: Record<string, number>;
    metrics: string[];
    description?: string;
    dimension_weights?: Record<string, number>;
}

export const listStrategies = async () => {
    const { data } = await client.get<StrategyEntity[]>("/strategies/");
    return data;
};

export const saveStrategy = async (payload: StrategyEntity) => {
    const { data } = await client.post<StrategyEntity>("/strategies/", payload);
    return data;
};
