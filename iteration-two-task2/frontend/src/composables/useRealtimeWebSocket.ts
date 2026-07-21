import { ref, type Ref } from "vue";

export interface WsMessage {
    event: string;
    data: Record<string, unknown>;
}

type EventHandler = (data: any) => void;

/**
 * WebSocket composable for realtime session monitoring.
 * Automatically reconnects on disconnect.
 */
export function useRealtimeWebSocket() {
    const connected = ref(false);
    const lastError = ref<string | null>(null);

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let currentSessionId: string | null = null;

    const listeners = new Map<string, EventHandler[]>();

    function on(event: string, cb: EventHandler) {
        if (!listeners.has(event)) {
            listeners.set(event, []);
        }
        listeners.get(event)!.push(cb);
    }

    function off(event: string, cb: EventHandler) {
        const cbs = listeners.get(event);
        if (cbs) {
            const idx = cbs.indexOf(cb);
            if (idx >= 0) cbs.splice(idx, 1);
        }
    }

    function _dispatch(event: string, data: any) {
        const cbs = listeners.get(event);
        if (cbs) {
            cbs.forEach((cb) => cb(data));
        }
    }

    function _getWsUrl(sid: string): string {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";
        const host = window.location.host;
        const path = baseUrl.startsWith("/") ? baseUrl : `/${baseUrl}`;
        return `${protocol}//${host}${path}/mode-realtime/ws/sessions/${sid}`;
    }

    function connect(sid: string) {
        disconnect();
        currentSessionId = sid;

        const url = _getWsUrl(sid);
        try {
            ws = new WebSocket(url);
        } catch (e) {
            lastError.value = `WebSocket connection failed: ${e}`;
            _scheduleReconnect();
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

        ws.onmessage = (event: MessageEvent) => {
            try {
                const msg: WsMessage = JSON.parse(event.data);
                _dispatch(msg.event, msg.data);
            } catch {
                // ignore malformed messages
            }
        };

        ws.onclose = () => {
            connected.value = false;
            _clearPing();
            if (currentSessionId) {
                _scheduleReconnect();
            }
        };

        ws.onerror = () => {
            lastError.value = "WebSocket error";
        };
    }

    function disconnect() {
        _clearPing();
        _clearReconnect();
        if (ws) {
            ws.onclose = null;
            ws.close();
            ws = null;
        }
        connected.value = false;
        currentSessionId = null;
    }

    function _scheduleReconnect() {
        _clearReconnect();
        if (!currentSessionId) return;
        reconnectTimer = setTimeout(() => {
            if (currentSessionId) connect(currentSessionId);
        }, 3000);
    }

    function _clearReconnect() {
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    }

    function _clearPing() {
        if (pingTimer) {
            clearInterval(pingTimer);
            pingTimer = null;
        }
    }

    return { connected, lastError, connect, disconnect, on, off };
}
