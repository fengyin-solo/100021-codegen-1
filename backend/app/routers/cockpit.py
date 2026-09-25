"""剧本审稿驾驶舱接口：按推进阶段汇总剧本，并提供单部剧本的审稿明细。

独立于剧本管理、审片意见既有接口，新增视图不改动旧接口的行为与数据。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.cockpit import CockpitService

router = APIRouter(prefix="/api/cockpit", tags=["剧本审稿驾驶舱"])

service = CockpitService()


@router.get("", response_model=dict)
def cockpit_overview() -> dict[str, Any]:
    """驾驶舱概览：全部剧本（含已归档）按推进阶段排列，列表与看板共用同一份口径。"""
    return service.overview()


@router.get("/{script_id}", response_model=dict)
def cockpit_detail(script_id: int) -> dict[str, Any]:
    """单部剧本的审稿明细：审稿记录、版权归属与阶段变更时间；没有审稿记录时返回空列表。"""
    detail = service.detail(script_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"剧本 {script_id} 不存在")
    return detail
