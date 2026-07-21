import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent import Agent
from app.schemas.agent import (
    AgentConnectivityTestResponse,
    AgentCreate,
    AgentRead,
    AgentUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[AgentRead])
def list_agents(db: Session = Depends(get_db)) -> list[AgentRead]:
    items = db.scalars(select(Agent).order_by(Agent.id.desc())).all()
    return [AgentRead.model_validate(item) for item in items]


@router.post("/", response_model=AgentRead)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> AgentRead:
    agent = Agent(
        name=payload.name,
        description=payload.description,
        endpoint=payload.endpoint,
        auth_type=payload.auth_type,
        auth_config=payload.auth_config,
        timeout_ms=payload.timeout_ms,
        metadata_json=payload.metadata,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, db: Session = Depends(get_db)) -> AgentRead:
    item = db.get(Agent, agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return AgentRead.model_validate(item)


@router.put("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)
) -> AgentRead:
    item = db.get(Agent, agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent not found")

    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "metadata":
            item.metadata_json = value
        else:
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return AgentRead.model_validate(item)


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(Agent, agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent not found")
    db.delete(item)
    db.commit()
    return {"message": "deleted"}


@router.post("/{agent_id}/test", response_model=AgentConnectivityTestResponse)
def test_agent_connectivity(
    agent_id: int, db: Session = Depends(get_db)
) -> AgentConnectivityTestResponse:
    item = db.get(Agent, agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent not found")

    headers: dict[str, str] = {}
    if item.auth_type == "bearer":
        token = str((item.auth_config or {}).get("token") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    if item.auth_type == "api_key":
        key_name = str((item.auth_config or {}).get("key_name") or "X-API-Key")
        key_value = str((item.auth_config or {}).get("key_value") or "")
        if key_value:
            headers[key_name] = key_value

    try:
        response = httpx.get(item.endpoint, timeout=max(item.timeout_ms, 1000) / 1000.0, headers=headers)
        return AgentConnectivityTestResponse(
            ok=response.status_code < 500,
            message="reachable",
            status_code=response.status_code,
        )
    except Exception as exc:
        return AgentConnectivityTestResponse(
            ok=False,
            message=str(exc),
            status_code=None,
        )
