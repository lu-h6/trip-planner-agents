"""旅行记忆API路由."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.memory_service import get_memory_service

router = APIRouter(prefix="/memory", tags=["旅行记忆"])


class MemoryCreateRequest(BaseModel):
    """手动添加记忆请求."""

    content: str = Field(..., description="记忆内容")
    memory_type: str = Field(default="travel_preference", description="记忆类型")
    importance: float = Field(default=0.7, ge=0, le=1, description="重要性,范围0-1")


@router.get(
    "/{user_id}",
    summary="列出用户旅行记忆",
    description="查看指定用户的旅行偏好、历史行程和额外要求记忆"
)
async def list_memories(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    memory_type: Optional[str] = Query(None)
):
    try:
        service = get_memory_service()
        memories = service.list_memories(user_id=user_id, limit=limit, memory_type=memory_type)
        return {
            "success": True,
            "message": "获取记忆成功",
            "data": memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆失败: {str(e)}")


@router.get(
    "/{user_id}/context",
    summary="获取规划用记忆上下文",
    description="按查询词重排用户记忆,返回可注入Agent提示词的上下文"
)
async def get_memory_context(
    user_id: str,
    query: str = Query("", description="检索查询"),
    limit: int = Query(8, ge=1, le=30)
):
    try:
        service = get_memory_service()
        memories = service.search_memories(user_id=user_id, query=query, limit=limit)
        context = "\n".join(f"- {memory['content']}" for memory in memories) if memories else "暂无可用历史记忆。"
        return {
            "success": True,
            "message": "获取记忆上下文成功",
            "data": {
                "context": context,
                "memories": memories
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆上下文失败: {str(e)}")


@router.post(
    "/{user_id}",
    summary="手动添加旅行记忆",
    description="为指定用户手动添加偏好、限制或历史经验"
)
async def add_memory(user_id: str, request: MemoryCreateRequest):
    try:
        service = get_memory_service()
        memory_id = service.add_memory(
            user_id=user_id,
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            properties={"source": "manual"},
        )
        return {
            "success": True,
            "message": "添加记忆成功",
            "data": {"memory_id": memory_id}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加记忆失败: {str(e)}")


@router.delete(
    "/{user_id}",
    summary="清空用户旅行记忆",
    description="删除指定用户的所有旅行记忆"
)
async def clear_user_memories(user_id: str):
    try:
        service = get_memory_service()
        deleted = service.clear_user_memories(user_id)
        return {
            "success": True,
            "message": "清空记忆成功",
            "data": {"deleted": deleted}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空记忆失败: {str(e)}")


@router.delete(
    "/{user_id}/{memory_id}",
    summary="删除单条旅行记忆",
    description="删除指定用户的一条旅行记忆"
)
async def delete_memory(user_id: str, memory_id: str):
    try:
        service = get_memory_service()
        memories = service.list_memories(user_id=user_id, limit=10000)
        if not any(memory["memory_id"] == memory_id for memory in memories):
            raise HTTPException(status_code=404, detail="记忆不存在")

        deleted = service.delete_memory(memory_id)
        return {
            "success": deleted,
            "message": "删除记忆成功" if deleted else "记忆未删除",
            "data": {"memory_id": memory_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记忆失败: {str(e)}")


@router.get(
    "/system/stats",
    summary="获取记忆系统统计",
    description="查看底层SQLite记忆库统计信息"
)
async def get_memory_stats():
    try:
        service = get_memory_service()
        return {
            "success": True,
            "message": "获取记忆统计成功",
            "data": service.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")
