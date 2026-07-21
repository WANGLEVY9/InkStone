from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetRead,
    DatasetRealtimeAnalysisResponse,
    DatasetUploadResponse,
)
from app.services.dataset_parser_service import DatasetParserService

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=DatasetListResponse)
def list_datasets(db: Session = Depends(get_db)) -> DatasetListResponse:
    items = DatasetParserService.list_assets(db)
    return DatasetListResponse(total=len(items), items=[DatasetRead.model_validate(item) for item in items])


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DatasetUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="invalid file")

    allowed = (".json", ".jsonl", ".csv")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail="only json/jsonl/csv are supported")

    asset = await DatasetParserService.save_upload(db, file, settings.upload_dir)
    summary = asset.parser_summary or {}
    return DatasetUploadResponse(
        dataset=DatasetRead.model_validate(asset),
        parsed_metrics=summary.get("parsed_metrics") or [],
        recommended_task_payload=summary.get("recommended_task_payload") or {},
    )


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> DatasetRead:
    asset = DatasetParserService.get_asset_by_dataset_id(db, dataset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return DatasetRead.model_validate(asset)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    asset = DatasetParserService.get_asset_by_dataset_id(db, dataset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    rows = DatasetParserService.load_asset_rows(asset)
    safe_limit = max(1, min(limit, 200))
    return DatasetPreviewResponse(
        dataset_id=dataset_id,
        total=len(rows),
        items=rows[:safe_limit],
    )


@router.get("/{dataset_id}/analysis", response_model=DatasetRealtimeAnalysisResponse)
def get_dataset_realtime_analysis(dataset_id: str, db: Session = Depends(get_db)) -> DatasetRealtimeAnalysisResponse:
    asset = DatasetParserService.get_asset_by_dataset_id(db, dataset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    data = DatasetParserService.build_realtime_analysis(asset)
    return DatasetRealtimeAnalysisResponse(**data)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    asset = DatasetParserService.get_asset_by_dataset_id(db, dataset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    DatasetParserService.delete_asset(db, asset)
    return {"message": "deleted"}
