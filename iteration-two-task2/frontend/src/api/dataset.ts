import client from "./client";

export interface DatasetEntity {
    id: number;
    dataset_id: string;
    name: string;
    filename: string;
    content_type: string;
    parser_summary: Record<string, any>;
    note?: string;
    created_at: string;
    updated_at: string;
}

export interface DatasetListResponse {
    total: number;
    items: DatasetEntity[];
}

export interface DatasetUploadResponse {
    dataset: DatasetEntity;
    parsed_metrics: string[];
    recommended_task_payload: Record<string, any>;
}

export interface DatasetRealtimeAnalysis {
    dataset_id: string;
    timeline: Array<Record<string, number | string>>;
    live_metrics: Record<string, number>;
    findings: string[];
}

export interface DatasetPreviewResponse {
    dataset_id: string;
    total: number;
    items: Array<Record<string, unknown>>;
}

export const listDatasets = async () => {
    const { data } = await client.get<DatasetListResponse>("/datasets/");
    return data;
};

export const uploadDataset = async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await client.post<DatasetUploadResponse>("/datasets/upload", form, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });
    return data;
};

export const getDatasetAnalysis = async (datasetId: string) => {
    const { data } = await client.get<DatasetRealtimeAnalysis>(`/datasets/${datasetId}/analysis`);
    return data;
};

export const previewDataset = async (datasetId: string, limit = 20) => {
    const { data } = await client.get<DatasetPreviewResponse>(`/datasets/${datasetId}/preview?limit=${limit}`);
    return data;
};

export const deleteDataset = async (datasetId: string) => {
    const { data } = await client.delete(`/datasets/${datasetId}`);
    return data;
};
