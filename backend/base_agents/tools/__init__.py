"""工具系统

当前项目主要使用 MCPTool。其他扩展工具按需懒加载，避免导入
base_agents.tools 时提前要求安装记忆、RAG、评估或训练相关依赖。
"""

from .base import Tool, ToolParameter
from .registry import ToolRegistry, global_registry
from .builtin.search import SearchTool
from .builtin.calculator import CalculatorTool
from .builtin.protocol_tools import MCPTool, A2ATool, ANPTool
from .chain import ToolChain, ToolChainManager, create_research_chain, create_simple_chain
from .async_executor import (
    AsyncToolExecutor,
    run_parallel_tools,
    run_batch_tool,
    run_parallel_tools_sync,
    run_batch_tool_sync,
)

_LAZY_EXPORTS = {
    "MemoryTool": ".builtin.memory_tool",
    "RAGTool": ".builtin.rag_tool",
    "NoteTool": ".builtin.note_tool",
    "TerminalTool": ".builtin.terminal_tool",
    "BFCLEvaluationTool": ".builtin.bfcl_evaluation_tool",
    "GAIAEvaluationTool": ".builtin.gaia_evaluation_tool",
    "LLMJudgeTool": ".builtin.llm_judge_tool",
    "WinRateTool": ".builtin.win_rate_tool",
    "RLTrainingTool": ".builtin.rl_training_tool",
}


def __getattr__(name):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(_LAZY_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

__all__ = [
    # 基础工具系统
    "Tool",
    "ToolParameter",
    "ToolRegistry",
    "global_registry",

    # 内置工具
    "SearchTool",
    "CalculatorTool",
    "MemoryTool",
    "RAGTool",
    "NoteTool",
    "TerminalTool",

    # 协议工具
    "MCPTool",
    "A2ATool",
    "ANPTool",

    # 评估工具
    "BFCLEvaluationTool",
    "GAIAEvaluationTool",
    "LLMJudgeTool",
    "WinRateTool",

    # RL训练工具
    "RLTrainingTool",

    # 工具链功能
    "ToolChain",
    "ToolChainManager",
    "create_research_chain",
    "create_simple_chain",

    # 异步执行功能
    "AsyncToolExecutor",
    "run_parallel_tools",
    "run_batch_tool",
    "run_parallel_tools_sync",
    "run_batch_tool_sync",
]
