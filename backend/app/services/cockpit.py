"""剧本审稿驾驶舱业务规则：概览的排序口径与单部剧本的审稿明细都收在这里。

列表视图与看板视图必须看到同一份数据，所以排序、关联审稿记录的口径只在
这里定义一次，接口层不做二次加工。
"""
from __future__ import annotations

from typing import Any

from app.services.script import STATUS_ORDER
from app.store import store

SCRIPT_MODULE = "script"
REVIEW_MODULE = "review"


def _review_rows(script_code: str) -> list[dict[str, Any]]:
    """按剧本编号收集审稿记录；概览里的计数与详情里的列表共用这一份口径。"""
    return [row for row in store.rows(REVIEW_MODULE) if str(row.get("剧本编号", "")) == script_code]


def _stage_rank(row: dict[str, Any]) -> tuple[int, int]:
    """推进阶段排序键：按状态序列排，未知状态排最后，同阶段按登记先后（id）排。"""
    status = str(row.get("status", ""))
    rank = STATUS_ORDER.index(status) if status in STATUS_ORDER else len(STATUS_ORDER)
    return rank, int(row.get("id", 0))


def _script_summary(row: dict[str, Any]) -> dict[str, Any]:
    """驾驶舱卡片/列表行共用的剧本摘要：题材、集数、版本、定稿日期与版权归属。"""
    code = str(row.get("剧本编号", ""))
    return {
        "id": row.get("id"),
        "剧本编号": code,
        "剧本名称": row.get("剧本名称"),
        "题材类型": row.get("题材类型"),
        "总集数": row.get("总集数"),
        "当前版本": row.get("当前版本"),
        "终稿日期": row.get("终稿日期"),
        "版权归属": row.get("版权归属"),
        "status": row.get("status"),
        "stage_history": list(row.get("stage_history") or []),
        "review_count": len(_review_rows(code)),
    }


class CockpitService:
    def overview(self) -> dict[str, Any]:
        """驾驶舱概览：全部剧本（含旧剧本与已归档）按推进阶段顺序排列。"""
        rows = sorted(store.rows(SCRIPT_MODULE), key=_stage_rank)
        scripts = [_script_summary(row) for row in rows]
        return {"stages": list(STATUS_ORDER), "scripts": scripts, "total": len(scripts)}

    def detail(self, script_id: int) -> dict[str, Any] | None:
        """单部剧本明细：审稿记录、版权归属与阶段变更时间；已归档剧本同样可查。"""
        row = store.find(SCRIPT_MODULE, script_id)
        if row is None:
            return None
        reviews = _review_rows(str(row.get("剧本编号", "")))
        return {
            "script": _script_summary(row),
            "reviews": reviews,
            "review_total": len(reviews),
        }
