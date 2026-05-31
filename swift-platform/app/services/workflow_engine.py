"""流程运行引擎（简化版 MVP）

目标：
- 支持从流程定义发起实例
- 支持审批任务通过/驳回
- 根据 LogicFlow graph_data 的连线顺序推进（当前实现：单分支）

说明：
- v1.1 文档里包含更完整的条件节点、并行等设计；此处先实现"主要功能"可跑通。
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sys_user import SysUser
from app.models.wf_definition import WfDefinition
from app.models.wf_history import WfHistory
from app.models.wf_instance import WfInstance
from app.models.wf_task import WfTask


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class WorkflowEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------
    # graph helpers
    # -------------------------

    @staticmethod
    def _node_type(node: dict) -> str:
        t = (node.get("type") or "").lower()
        if t in {"start", "start-node", "startnode"}:
            return "start"
        if t in {"end", "end-node", "endnode"}:
            return "end"
        # 兜底：LogicFlow 的节点 type 可能是自定义的，如 approval/condition/cc/webhook
        return t or "unknown"

    @staticmethod
    def _edges(graph_data: dict) -> list[dict]:
        return list(graph_data.get("edges") or [])

    @staticmethod
    def _nodes(graph_data: dict) -> list[dict]:
        return list(graph_data.get("nodes") or [])

    def _find_start_node(self, graph_data: dict) -> dict:
        for n in self._nodes(graph_data):
            if self._node_type(n) == "start":
                return n
        raise HTTPException(status_code=400, detail="流程图缺少开始节点")

    def _find_next_node_id(self, graph_data: dict, from_node_id: str) -> str | None:
        """当前实现：取第一条出边"""
        for e in self._edges(graph_data):
            src = e.get("sourceNodeId") or e.get("source") or e.get("sourceNode")
            tgt = e.get("targetNodeId") or e.get("target") or e.get("targetNode")
            if src == from_node_id:
                return tgt
        return None

    def _get_node(self, graph_data: dict, node_id: str) -> dict | None:
        for n in self._nodes(graph_data):
            if n.get("id") == node_id:
                return n
        return None

    @staticmethod
    def _node_name(node: dict) -> str:
        # LogicFlow 可能是 {"text": {"value": "xxx"}} 或 {"text": "xxx"}
        text = node.get("text")
        if isinstance(text, dict):
            return str(text.get("value") or "")
        return str(text or "")

    @staticmethod
    def _pick_assignee_id(
        definition: WfDefinition, node_id: str, default_user_id: int
    ) -> int:
        cfg = definition.node_config or {}
        node_cfg = cfg.get(node_id) if isinstance(cfg, dict) else None
        if isinstance(node_cfg, dict):
            # 支持 assignee_id / assignee_ids 两种写法
            if node_cfg.get("assignee_id"):
                return int(node_cfg["assignee_id"])
            if node_cfg.get("assignee_ids"):
                ids = node_cfg["assignee_ids"]
                if isinstance(ids, list) and ids:
                    return int(ids[0])
        return default_user_id

    # -------------------------
    # engine
    # -------------------------

    async def start_instance(
        self,
        current_user: SysUser,
        definition_id: int,
        title: str,
        business_key: str,
        form_data: dict,
    ) -> WfInstance:
        definition = await self.db.get(WfDefinition, definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail="流程定义不存在")
        if definition.status != 1:
            raise HTTPException(status_code=400, detail="流程未发布或已停用")

        graph = definition.graph_data or {}
        start_node = self._find_start_node(graph)
        next_node_id = self._find_next_node_id(graph, start_node["id"])
        if not next_node_id:
            raise HTTPException(status_code=400, detail="流程图开始节点未连线")

        inst = WfInstance(
            definition_id=definition.id,
            title=title,
            business_key=business_key,
            form_data=form_data or {},
            initiator_id=current_user.id,
            current_node=next_node_id,
            status=0,
            started_at=_now(),
        )
        self.db.add(inst)
        await self.db.flush()  # 拿到 inst.id

        await self._create_history(
            inst.id,
            node_id=start_node["id"],
            node_name="开始",
            operator_id=current_user.id,
            action="start",
            comment="发起流程",
            form_snapshot=form_data or {},
        )

        await self._advance_to_node(inst, definition, next_node_id, current_user.id)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def approve_task(
        self, current_user: SysUser, task_id: int, action: str, comment: str
    ):
        task = await self.db.get(WfTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        if task.status != 0:
            raise HTTPException(status_code=400, detail="任务已处理")
        if task.assignee_id and task.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权处理该任务")

        inst = await self.db.get(WfInstance, task.instance_id)
        if not inst:
            raise HTTPException(status_code=404, detail="流程实例不存在")
        if inst.status != 0:
            raise HTTPException(status_code=400, detail="流程实例已结束")

        definition = await self.db.get(WfDefinition, inst.definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail="流程定义不存在")

        action = (action or "").lower()
        if action not in {"approve", "reject"}:
            raise HTTPException(status_code=400, detail="action 仅支持 approve/reject")

        task.status = 1 if action == "approve" else 2
        task.action = action
        task.comment = comment or ""
        task.processed_at = _now()

        await self._create_history(
            inst.id,
            node_id=task.node_id,
            node_name=task.node_name,
            operator_id=current_user.id,
            action=action,
            comment=comment or "",
            form_snapshot=inst.form_data or {},
        )

        if action == "reject":
            inst.status = 2
            inst.finished_at = _now()
            await self.db.commit()
            return

        graph = definition.graph_data or {}
        next_node_id = self._find_next_node_id(graph, task.node_id)
        if not next_node_id:
            # 没有后续节点，认为结束
            inst.status = 1
            inst.finished_at = _now()
            await self.db.commit()
            return

        inst.current_node = next_node_id
        await self._advance_to_node(inst, definition, next_node_id, current_user.id)
        await self.db.commit()

    async def _advance_to_node(
        self, inst: WfInstance, definition: WfDefinition, node_id: str, operator_id: int
    ):
        graph = definition.graph_data or {}
        node = self._get_node(graph, node_id)
        if not node:
            raise HTTPException(status_code=400, detail=f"流程图节点不存在: {node_id}")

        ntype = self._node_type(node)
        if ntype == "end":
            inst.status = 1
            inst.finished_at = _now()
            await self._create_history(
                inst.id,
                node_id=node_id,
                node_name="结束",
                operator_id=operator_id,
                action="end",
                comment="流程结束",
                form_snapshot=inst.form_data or {},
            )
            return

        # 默认把非 end 节点都当作需要人工处理的审批节点
        assignee_id = self._pick_assignee_id(
            definition, node_id, default_user_id=inst.initiator_id
        )
        t = WfTask(
            instance_id=inst.id,
            node_id=node_id,
            node_name=self._node_name(node) or node_id,
            node_type=ntype or "approval",
            assignee_id=assignee_id,
            status=0,
        )
        self.db.add(t)

    async def _create_history(
        self,
        instance_id: int,
        node_id: str,
        node_name: str,
        operator_id: int | None,
        action: str,
        comment: str,
        form_snapshot: dict,
    ):
        h = WfHistory(
            instance_id=instance_id,
            node_id=node_id,
            node_name=node_name or "",
            operator_id=operator_id,
            action=action,
            comment=comment or "",
            form_snapshot=form_snapshot or {},
        )
        self.db.add(h)
