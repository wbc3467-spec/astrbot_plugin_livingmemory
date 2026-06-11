"""供 Agent 主动遗忘长期记忆的工具。"""

import asyncio
import json
from dataclasses import field
from typing import Any

from pydantic.dataclasses import dataclass

from astrbot.api import logger
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


def _json_result(data: dict[str, Any]) -> str:
    """将工具结果稳定序列化为 JSON 文本。"""
    return json.dumps(data, ensure_ascii=False, default=str)


@dataclass
class MemoryForgetTool(FunctionTool[AstrAgentContext]):
    """长期记忆遗忘工具。"""

    __pydantic_config__ = {"arbitrary_types_allowed": True}

    context: Any = None
    memory_engine: Any = None

    name: str = "forget_long_term_memory"
    description: str = (
        "Forget a long-term memory by memory ID. "
        "Use when you need to forget an existing memory, use with caution"
    )

    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to forget.",
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for forgetting the memory.",
                    "default": "",
                },
            },
            "required": ["memory_id"],
        }
    )

    async def call(
        self,
        context: ContextWrapper[AstrAgentContext],
        memory_id: int,
        reason: str = "",
    ) -> ToolExecResult:
        """执行长期记忆遗忘。"""

        if memory_id <= 0:
            return _json_result(
                {
                    "forgotten": False,
                    "error": "invalid memory_id",
                }
            )

        if self.memory_engine is None:
            return _json_result(
                {
                    "forgotten": False,
                    "error": "memory engine is not initialized",
                }
            )

        try:
            success = await self.memory_engine.delete_memory(memory_id)

            if not success:
                return _json_result(
                    {
                        "forgotten": False,
                        "memory_id": memory_id,
                        "error": "memory not found or forget failed",
                    }
                )

            return _json_result(
                {
                    "forgotten": True,
                    "memory_id": memory_id,
                    "reason": (reason or "").strip(),
                }
            )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"记忆遗忘工具执行失败: {e}", exc_info=True)
            return _json_result(
                {
                    "forgotten": False,
                    "memory_id": memory_id,
                    "error": "internal_error",
                }
            )
