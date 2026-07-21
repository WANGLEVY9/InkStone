import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.v1.endpoints.ws_manager import broadcast, connect, disconnect
from app.schemas.mode_eval import (
    RealtimeAlertsResponse,
    RealtimeEventIngestResponse,
    RealtimeSessionDetailResponse,
    RealtimeSessionListResponse,
    RealtimeSessionRead,
    RealtimeSessionStartRequest,
    RealtimeStepEndRequest,
    RealtimeStepStartRequest,
    RealtimeStreamEventRequest,
    RealtimeToolCallRequest,
)
from app.services.mode_eval_service import ModeEvalService

router = APIRouter()


# ------------------------------------------------------------------
# REST endpoints
# ------------------------------------------------------------------


@router.post("/sessions/start", response_model=RealtimeSessionRead)
async def on_agent_start(payload: RealtimeSessionStartRequest) -> RealtimeSessionRead:
    data = ModeEvalService.start_realtime_session(payload.model_dump())
    await broadcast(
        data["session_id"],
        "session_created",
        {"session": data},
    )
    return RealtimeSessionRead(**data)


@router.post("/sessions/{session_id}/step-start", response_model=RealtimeSessionRead)
async def on_step_start(session_id: str, payload: RealtimeStepStartRequest) -> RealtimeSessionRead:
    try:
        data = ModeEvalService.on_step_start(session_id, payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    await broadcast(session_id, "step_start", {"session": data})
    return RealtimeSessionRead(**data)


@router.post("/sessions/{session_id}/tool-call", response_model=RealtimeSessionRead)
async def on_tool_call(session_id: str, payload: RealtimeToolCallRequest) -> RealtimeSessionRead:
    try:
        data = ModeEvalService.on_tool_call(session_id, payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    await broadcast(session_id, "tool_call", {"session": data})
    return RealtimeSessionRead(**data)


@router.post("/sessions/{session_id}/step-end", response_model=RealtimeSessionRead)
async def on_step_end(session_id: str, payload: RealtimeStepEndRequest) -> RealtimeSessionRead:
    try:
        data = ModeEvalService.on_step_end(session_id, payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    await broadcast(session_id, "step_end", {"session": data})
    return RealtimeSessionRead(**data)


@router.post("/sessions/{session_id}/events", response_model=RealtimeEventIngestResponse)
async def ingest_langgraph_stream_event(session_id: str, payload: RealtimeStreamEventRequest) -> RealtimeEventIngestResponse:
    try:
        data = ModeEvalService.ingest_stream_event(session_id, payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Broadcast event and any decision
    await broadcast(session_id, "stream_event", data)
    if data["should_stop"]:
        await broadcast(session_id, "session_stopped", data)

    return RealtimeEventIngestResponse(**data)


@router.post("/sessions/{session_id}/end", response_model=RealtimeSessionRead)
async def on_agent_end(session_id: str) -> RealtimeSessionRead:
    try:
        data = ModeEvalService.end_realtime_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    await broadcast(session_id, "session_ended", {"session": data})
    return RealtimeSessionRead(**data)


@router.get("/sessions", response_model=RealtimeSessionListResponse)
def list_sessions() -> RealtimeSessionListResponse:
    items = ModeEvalService.list_realtime_sessions()
    return RealtimeSessionListResponse(total=len(items), items=[RealtimeSessionRead(**item) for item in items])


@router.get("/sessions/{session_id}", response_model=RealtimeSessionDetailResponse)
def get_session_detail(session_id: str) -> RealtimeSessionDetailResponse:
    try:
        data = ModeEvalService.get_realtime_session_detail(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    return RealtimeSessionDetailResponse(**data)


@router.get("/sessions/{session_id}/alerts", response_model=RealtimeAlertsResponse)
def list_session_alerts(session_id: str) -> RealtimeAlertsResponse:
    try:
        items = ModeEvalService.list_realtime_alerts(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    return RealtimeAlertsResponse(session_id=session_id, total=len(items), items=items)


# ------------------------------------------------------------------
# WebSocket endpoint
# ------------------------------------------------------------------


@router.websocket("/ws/sessions/{session_id}")
async def realtime_session_ws(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for real-time session monitoring.

    Pushes session state updates, new events, and alerts as they happen.
    Clients receive JSON messages: {"event": "<event_type>", "data": {...}}
    """
    await connect(session_id, websocket)
    try:
        # Send initial session state
        try:
            detail = ModeEvalService.get_realtime_session_detail(session_id)
            await websocket.send_text(
                json.dumps(
                    {"event": "session_init", "data": json.loads(RealtimeSessionDetailResponse(**detail).model_dump_json())},
                    default=str,
                )
            )
        except KeyError:
            await websocket.send_text(
                json.dumps({"event": "error", "data": {"message": "session not found"}})
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Keep connection alive, listen for client pings
        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except (ValueError, KeyError):
                pass
    except WebSocketDisconnect:
        pass
    finally:
        disconnect(session_id, websocket)
