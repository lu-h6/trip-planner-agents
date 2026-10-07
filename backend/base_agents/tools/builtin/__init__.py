"""内置工具模块"""

from .search import SearchTool
from .calculator import CalculatorTool
from .protocol_tools import MCPTool, A2ATool, ANPTool

_LAZY_EXPORTS = {
    "MemoryTool": ".memory_tool",
    "RAGTool": ".rag_tool",
    "NoteTool": ".note_tool",
    "TerminalTool": ".terminal_tool",
    "BFCLEvaluationTool": ".bfcl_evaluation_tool",
    "GAIAEvaluationTool": ".gaia_evaluation_tool",
    "LLMJudgeTool": ".llm_judge_tool",
    "WinRateTool": ".win_rate_tool",
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
    "SearchTool",
    "CalculatorTool",
    "MemoryTool",
    "RAGTool",
    "NoteTool",
    "TerminalTool",
    "MCPTool",
    "A2ATool",
    "ANPTool",
    "BFCLEvaluationTool",
    "GAIAEvaluationTool",
    "LLMJudgeTool",
    "WinRateTool",
]
