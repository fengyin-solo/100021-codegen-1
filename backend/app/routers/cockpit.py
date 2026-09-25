"""剧本审稿驾驶舱接口：只读，不改动剧本管理、审片意见等既有模块的数据。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.cockpit import STAGE_ORDER, CockpitService

router = APIRouter(prefix="/api/cockpit", tags=["剧本审稿驾驶舱"])

service = CockpitService()


@router.get("/scripts")
def list_scripts(
    stage: str | None = Query(default=None, description="创作中、待审稿、已定稿、已归档"),
    keyword: str | None = Query(default=None, description="按剧本编号或名称检索"),
) -> dict[str, object]:
    """驾驶舱概览：列表与看板共用该返回，按推进阶段排列。

    不做分页：驾驶舱需要看到全部剧本（含已归档），总量一般在几十部以内。
    """
    items = service.list_scripts(stage=stage, keyword=keyword)
    return {
        "stages": list(STAGE_ORDER),
        "total": len(items),
        "items": items,
    }


@router.get("/scripts/{script_id}")
def get_script(script_id: int) -> dict[str, object]:
    """单部剧本的审稿驾驶舱详情：审稿记录、版权归属与阶段变更时间。"""
    detail = service.get_detail(script_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"剧本 {script_id} 不存在")
    return detail
