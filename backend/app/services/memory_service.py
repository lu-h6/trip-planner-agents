"""旅行记忆服务.

基于 base_agents 内置的 SQLiteDocumentStore 实现轻量长期记忆。
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from base_agents.memory.storage.document_store import SQLiteDocumentStore

from ..config import get_settings
from ..models.schemas import TripPlan, TripRequest


class TravelMemoryService:
    """面向旅行规划业务的记忆封装."""

    def __init__(self, storage_path: Optional[str] = None):
        memory_dir = (
            Path(storage_path)
            if storage_path
            else get_settings().get_memory_data_dir()
        )
        memory_dir.mkdir(parents=True, exist_ok=True)
        self.store = SQLiteDocumentStore(str(memory_dir / "travel_memory.db"))

    def build_context(self, request: TripRequest, limit: int = 8) -> str:
        """为一次旅行规划构建可注入 prompt 的记忆上下文."""
        if not request.memory_enabled:
            return "本次请求未启用历史记忆。"

        query_parts = [
            request.city,
            request.transportation,
            request.accommodation,
            " ".join(request.preferences or []),
            request.free_text_input or "",
        ]
        query = " ".join(part for part in query_parts if part).strip()
        memories = self.search_memories(request.user_id, query=query, limit=limit)

        if not memories:
            return "暂无可用历史记忆。"

        lines = []
        for memory in memories:
            content = memory["content"].replace("\n", " ").strip()
            lines.append(f"- {content}")
        return "\n".join(lines)

    def search_memories(self, user_id: str, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """按用户检索记忆,并用轻量文本相关性重排."""
        candidates = self.store.search_memories(user_id=user_id, limit=100)
        if not query:
            return candidates[:limit]

        query_tokens = self._tokenize(query)
        scored = []
        for memory in candidates:
            content = memory.get("content", "")
            content_tokens = self._tokenize(content)
            overlap = len(query_tokens.intersection(content_tokens))
            exact_bonus = 2 if query and query in content else 0
            importance = float(memory.get("importance", 0.5))
            score = overlap + exact_bonus + importance
            if score > 0:
                scored.append((score, memory))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [memory for _, memory in scored[:limit]]

    def list_memories(
        self,
        user_id: str,
        limit: int = 20,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列出用户记忆."""
        return self.store.search_memories(
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
        )

    def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "travel_preference",
        importance: float = 0.7,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加一条旅行记忆."""
        memory_id = str(uuid.uuid4())
        return self.store.add_memory(
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            timestamp=int(time.time()),
            importance=importance,
            properties=properties or {},
        )

    def save_trip_memory(self, request: TripRequest, trip_plan: TripPlan) -> None:
        """保存本次旅行请求和规划摘要."""
        if not request.memory_enabled:
            return

        preferences = "、".join(request.preferences) if request.preferences else "无明确偏好"
        self.add_memory(
            user_id=request.user_id,
            memory_type="travel_preference",
            importance=0.82,
            content=(
                f"用户偏好: 去{request.city}旅行时选择{request.transportation}, "
                f"住宿偏好为{request.accommodation}, 旅行偏好为{preferences}。"
            ),
            properties={
                "city": request.city,
                "transportation": request.transportation,
                "accommodation": request.accommodation,
                "preferences": request.preferences,
            },
        )

        if request.free_text_input:
            self.add_memory(
                user_id=request.user_id,
                memory_type="user_requirement",
                importance=0.9,
                content=f"用户额外要求: {request.free_text_input}",
                properties={"city": request.city},
            )

        attraction_names = []
        for day in trip_plan.days:
            attraction_names.extend(attraction.name for attraction in day.attractions[:3])

        budget_text = ""
        if trip_plan.budget:
            budget_text = f", 预算约{trip_plan.budget.total}元"

        self.add_memory(
            user_id=request.user_id,
            memory_type="trip_history",
            importance=0.74,
            content=(
                f"历史行程: {request.start_date}至{request.end_date}规划过"
                f"{request.city}{request.travel_days}日游{budget_text}; "
                f"重点景点包括{self._join_preview(attraction_names)}。"
            ),
            properties={
                "city": request.city,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "travel_days": request.travel_days,
                "budget": trip_plan.budget.model_dump() if trip_plan.budget else None,
            },
        )

    def delete_memory(self, memory_id: str) -> bool:
        """删除单条记忆."""
        return self.store.delete_memory(memory_id)

    def clear_user_memories(self, user_id: str) -> int:
        """删除某个用户的全部记忆."""
        memories = self.store.search_memories(user_id=user_id, limit=10000)
        deleted = 0
        for memory in memories:
            if self.store.delete_memory(memory["memory_id"]):
                deleted += 1
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """获取底层存储统计."""
        return self.store.get_database_stats()

    def _tokenize(self, text: str) -> set[str]:
        normalized = text.lower().replace(",", " ").replace("，", " ")
        tokens = {token for token in normalized.split() if token}
        for keyword in ["历史文化", "自然风光", "美食", "购物", "艺术", "休闲", "公共交通", "自驾", "步行"]:
            if keyword in text:
                tokens.add(keyword.lower())
        return tokens

    def _join_preview(self, values: List[str], limit: int = 8) -> str:
        if not values:
            return "暂无"
        preview = values[:limit]
        suffix = "等" if len(values) > limit else ""
        return "、".join(preview) + suffix


_memory_service = None


def get_memory_service() -> TravelMemoryService:
    """获取旅行记忆服务单例."""
    global _memory_service
    if _memory_service is None:
        _memory_service = TravelMemoryService()
    return _memory_service
