"""agent-prompt-vars: simple {{variable}} substitution for prompt templates."""

from .core import PromptTemplate, PromptVarsError, fill

__all__ = ["PromptTemplate", "PromptVarsError", "fill"]
