import client from "./client";

export interface RealtimeSession {
    session_id: string;
    status: string;
    agent_name: string;
    task: string;
    started_at: string;
    ended_at?: string;
    step_count: number;
    tool_call_count: number;
    consecutive_same_action: number;
    node_switch_count: number;
    event_count: number;
    current_node?: string;
    current_agent_type?: string;
    latest_decision: string;
    alert_count: number;
}

export interface RealtimeAlert {
    id: string;
    session_id: string;
    rule: string;
    severity: string;
    message: string;
    decision: string;
    created_at: string;
}

export interface RealtimeStreamToolCall {
    name: string;
    params?: Record<string, unknown>;
    dangerous?: boolean;
}

export interface RealtimeStreamEvent {
    id: string;
    session_id: string;
    event_type: string;
    node: string;
    agent_type: string;
    step: number;
    thought: string;
    message: string;
    next_agent: string;
    tool_calls: RealtimeStreamToolCall[];
    state: Record<string, unknown>;
    duration_sec: number;
    decision: string;
    reason: string;
    source: string;
    created_at: string;
}

export interface RealtimeEventIngestResponse {
    session: RealtimeSession;
    event: RealtimeStreamEvent;
    decision: string;
    reason: string;
    should_stop: boolean;
}

export interface OfflineEvalReport {
    session_id: string;
    task: string;
    success: boolean;
    scores: Record<string, number>;
    metrics: Record<string, number>;
    root_cause: string;
    recommendations: string[];
}

export interface OfflineEvalJob {
    job_id: string;
    status: string;
    created_at: string;
    updated_at: string;
    error?: string;
    report?: OfflineEvalReport;
}

export interface BatchEvalSummary {
    dataset_id: string;
    total_traces: number;
    success_rate: number;
    average_scores: Record<string, number>;
    root_cause_distribution: Record<string, number>;
    sample_reports: OfflineEvalReport[];
}

export interface BatchEvalJob {
    job_id: string;
    status: string;
    created_at: string;
    updated_at: string;
    error?: string;
    summary?: BatchEvalSummary;
    progress?: { processed: number; total: number };
    eval_task_id?: number;
}

export const startRealtimeSession = async (payload: {
    session_id?: string;
    agent_name: string;
    task: string;
    thresholds?: Record<string, number>;
}) => {
    const { data } = await client.post<RealtimeSession>("/mode-realtime/sessions/start", payload);
    return data;
};

export const realtimeStepStart = async (sessionId: string, payload: { step?: number; thought?: string; action?: string }) => {
    const { data } = await client.post<RealtimeSession>(`/mode-realtime/sessions/${sessionId}/step-start`, payload);
    return data;
};

export const realtimeToolCall = async (sessionId: string, payload: { tool_name: string; params?: Record<string, unknown>; dangerous?: boolean }) => {
    const { data } = await client.post<RealtimeSession>(`/mode-realtime/sessions/${sessionId}/tool-call`, payload);
    return data;
};

export const realtimeStepEnd = async (sessionId: string, payload: { step?: number; action?: string; duration_sec?: number; step_result?: string }) => {
    const { data } = await client.post<RealtimeSession>(`/mode-realtime/sessions/${sessionId}/step-end`, payload);
    return data;
};

export const endRealtimeSession = async (sessionId: string) => {
    const { data } = await client.post<RealtimeSession>(`/mode-realtime/sessions/${sessionId}/end`);
    return data;
};

export const listRealtimeSessions = async () => {
    const { data } = await client.get<{ total: number; items: RealtimeSession[] }>("/mode-realtime/sessions");
    return data;
};

export const getRealtimeSessionDetail = async (sessionId: string) => {
    const { data } = await client.get<{ session: RealtimeSession; latest_alerts: RealtimeAlert[]; latest_events: RealtimeStreamEvent[] }>(`/mode-realtime/sessions/${sessionId}`);
    return data;
};

export const ingestRealtimeStreamEvent = async (
    sessionId: string,
    payload: {
        event_type?: string;
        node: string;
        agent_type?: string;
        step?: number;
        thought?: string;
        message?: string;
        next_agent?: string;
        tool_calls?: RealtimeStreamToolCall[];
        state?: Record<string, unknown>;
        duration_sec?: number;
        timestamp?: string;
        source?: string;
    }
) => {
    const { data } = await client.post<RealtimeEventIngestResponse>(`/mode-realtime/sessions/${sessionId}/events`, payload);
    return data;
};

export const submitOfflineEval = async (trace: Record<string, unknown>) => {
    const { data } = await client.post<OfflineEvalJob>("/mode-offline/jobs/submit", { trace });
    return data;
};

export const listOfflineJobs = async () => {
    const { data } = await client.get<{ total: number; items: OfflineEvalJob[] }>("/mode-offline/jobs");
    return data;
};

export const getOfflineJob = async (jobId: string) => {
    const { data } = await client.get<OfflineEvalJob>(`/mode-offline/jobs/${jobId}`);
    return data;
};

export const runBatchEval = async (datasetId: string, strategyName?: string) => {
    const payload: Record<string, unknown> = { dataset_id: datasetId };
    if (strategyName) payload.strategy_name = strategyName;
    const { data } = await client.post<BatchEvalJob>("/mode-batch/jobs/run", payload);
    return data;
};

export const listBatchJobs = async () => {
    const { data } = await client.get<{ total: number; items: BatchEvalJob[] }>("/mode-batch/jobs");
    return data;
};

export const getBatchJob = async (jobId: string) => {
    const { data } = await client.get<BatchEvalJob>(`/mode-batch/jobs/${jobId}`);
    return data;
};
