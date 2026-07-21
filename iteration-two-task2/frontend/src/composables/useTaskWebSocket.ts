import { ref } from "vue";

type EventHandler = (data: any) => void;

export function useTaskWebSocket() {
    const connected = ref(false);
    const lastError = ref<string | null>(null);

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let currentTaskId: number | null = null;
    const listeners = new Map<string, EventHandler[]>();

    const on = (event: string, cb: EventHandler) => {
        if (!listeners.has(event)) {
            listeners.set(event, []);
        }
        listeners.get(event)!.push(cb);
    };

    const off = (event: string, cb: EventHandler) => {
        const cbs = listeners.get(event);
        if (!cbs) return;
        const idx = cbs.indexOf(cb);
        if (idx >= 0) cbs.splice(idx, 1);
    };

    const dispatch = (event: string, data: any) => {
        const cbs = listeners.get(event);
        if (!cbs) return;
        cbs.forEach((cb) => cb(data));
    };

    const wsUrl = (taskId: number) => {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";
        const host = window.location.host;
        const path = baseUrl.startsWith("/") ? baseUrl : `/${baseUrl}`;
        return `${protocol}//${host}${path}/tasks/${taskId}/ws`;
    };

    const clearPing = () => {
        if (pingTimer) {
            clearInterval(pingTimer);
            pingTimer = null;
        }
    };

    const clearReconnect = () => {
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    };

    const scheduleReconnect = () => {
        clearReconnect();
        if (currentTaskId === null) return;
        reconnectTimer = setTimeout(() => connect(currentTaskId!), 2500);
    };

    const connect = (taskId: number) => {
        disconnect();
        currentTaskId = taskId;
        try {
            ws = new WebSocket(wsUrl(taskId));
        } catch (error) {
            lastError.value = String(error);
            scheduleReconnect();
            return;
        }

        ws.onopen = () => {
            connected.value = true;
            lastError.value = null;
            pingTimer = setInterval(() => {
                if (ws?.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: "ping" }));
                }
            }, 25000);
        };

        ws.onmessage = (message) => {
            try {
                const payload = JSON.parse(message.data);
                if (payload?.event) {
                    dispatch(payload.event, payload.data ?? {});
                }
            } catch {
                // ignore invalid frames
            }
        };

        ws.onclose = () => {
            connected.value = false;
            clearPing();
            if (currentTaskId !== null) scheduleReconnect();
        };

        ws.onerror = () => {
            lastError.value = "task websocket error";
        };
    };

    const disconnect = () => {
        clearPing();
        clearReconnect();
        if (ws) {
            ws.onclose = null;
            ws.close();
            ws = null;
        }
        connected.value = false;
        currentTaskId = null;
    };

    return { connected, lastError, connect, disconnect, on, off };
}
