"""剧本审稿驾驶舱聚合口径：列表与看板共用同一份汇总数据。

列表视图和看板视图都只能从 list_scripts 取数，避免两个视图各自拼装导致
显示口径不一致；详情页在同一份剧本基础信息上再挂审稿记录与阶段变更。
旧剧本、已定稿与已归档剧本都照常返回，不做任何隐藏或覆盖。
"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "script"
REVIEW_MODULE = "_script_review"
STAGE_LOG_MODULE = "_script_stage_log"

# 推进阶段顺序与剧本管理服务保持一致；未知阶段排到最后，保证顺序稳定
STAGE_ORDER = ["创作中", "待审稿", "已定稿", "已归档"]


def _stage_index(stage: Any) -> int:
    try:
        return STAGE_ORDER.index(str(stage))
    except ValueError:
        return len(STAGE_ORDER)


def _reviews_for(code: str) -> list[dict[str, Any]]:
    rows = [row for row in store.rows(REVIEW_MODULE) if row.get("剧本编号") == code]
    # 审稿时间和编号同源，按 id 排即可保证先提交的在前
    return sorted(rows, key=lambda row: int(row.get("id", 0)))


def _stage_logs_for(code: str) -> list[dict[str, Any]]:
    rows = [row for row in store.rows(STAGE_LOG_MODULE) if row.get("剧本编号") == code]
    return sorted(rows, key=lambda row: (str(row.get("变更时间", "")), int(row.get("id", 0))))


def _build_summary(row: dict[str, Any]) -> dict[str, Any]:
    """概览卡片字段：题材类型、总集数、当前版本、定稿日期都在这里统一取数。"""
    code = str(row.get("剧本编号", ""))
    reviews = _reviews_for(code)
    return {
        "id": int(row.get("id", 0)),
        "剧本编号": code,
        "剧本名称": row.get("剧本名称"),
        "题材类型": row.get("题材类型"),
        "总集数": row.get("总集数"),
        "当前版本": row.get("当前版本"),
        # 驾驶舱口径把剧本表的「终稿日期」展示为「定稿日期」，原始数据不改动
        "定稿日期": row.get("终稿日期"),
        "版权归属": row.get("版权归属"),
        "编剧姓名": row.get("编剧姓名"),
        "推进阶段": row.get("status"),
        "审稿记录数": len(reviews),
        "最新审稿状态": reviews[-1].get("审片状态") if reviews else None,
    }


class CockpitService:
    def list_scripts(
        self,
        *,
        stage: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        """按推进阶段顺序返回剧本概览；列表与看板唯一的数据入口。"""
        rows = store.rows(MODULE)
        if stage:
            rows = [row for row in rows if row.get("status") == stage]
        if keyword:
            rows = [
                row
                for row in rows
                if keyword in str(row.get("剧本编号", ""))
                or keyword in str(row.get("剧本名称", ""))
            ]
        items = [_build_summary(row) for row in rows]
        items.sort(key=lambda item: (_stage_index(item["推进阶段"]), item["id"]))
        return items

    def get_detail(self, script_id: int) -> dict[str, Any] | None:
        """剧本详情：基础信息与概览同口径，另附审稿记录、版权归属、阶段变更时间。"""
        row = store.find(MODULE, script_id)
        if row is None:
            return None
        summary = _build_summary(row)
        code = summary["剧本编号"]
        summary["审稿记录"] = _reviews_for(code)
        summary["阶段变更"] = _stage_logs_for(code)
        return summary
