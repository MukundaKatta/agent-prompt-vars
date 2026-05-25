"""Simple {{variable}} substitution for prompt templates.

No external dependencies — uses re from the standard library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class PromptVarsError(Exception):
    """Raised on template errors (missing vars, unknown vars, etc.)."""


# Default delimiters: {{var}} and {var}
_DOUBLE_BRACE = re.compile(r"\{\{(\s*[\w.]+\s*)\}\}")
_SINGLE_BRACE = re.compile(r"\{(\s*[\w.]+\s*)\}")


def _find_vars(template: str, double_brace: bool) -> list[str]:
    pat = _DOUBLE_BRACE if double_brace else _SINGLE_BRACE
    return [m.group(1).strip() for m in pat.finditer(template)]


def _substitute(
    template: str,
    variables: dict[str, Any],
    *,
    double_brace: bool,
    strict: bool,
    allow_partial: bool,
) -> str:
    pat = _DOUBLE_BRACE if double_brace else _SINGLE_BRACE

    missing: list[str] = []

    def replacer(match: re.Match) -> str:
        var = match.group(1).strip()
        if var in variables:
            return str(variables[var])
        if allow_partial:
            return match.group(0)  # leave placeholder as-is
        missing.append(var)
        return match.group(0)

    result = pat.sub(replacer, template)

    if strict and missing:
        raise PromptVarsError(
            f"missing variable(s): {', '.join(sorted(missing))}"
        )

    return result


class PromptTemplate:
    """A reusable prompt template with {{variable}} placeholders.

    Args:
        template: the template string containing ``{{variable}}`` placeholders.
        double_brace: if True (default), use ``{{var}}`` syntax. If False, use ``{var}``.
        strict: if True (default), raise PromptVarsError on missing variables.
            If False, leave unknown placeholders unchanged.

    Example::

        tmpl = PromptTemplate(
            "You are a {{role}}.\\n\\nUser: {{question}}"
        )
        prompt = tmpl.render(role="researcher", question="What is DNA?")
    """

    def __init__(
        self,
        template: str,
        *,
        double_brace: bool = True,
        strict: bool = True,
    ) -> None:
        self.template = template
        self.double_brace = double_brace
        self.strict = strict
        self._vars: list[str] = _find_vars(template, double_brace)

    @property
    def required_vars(self) -> list[str]:
        """All variable names found in the template (sorted, unique)."""
        return sorted(set(self._vars))

    def render(self, **kwargs: Any) -> str:
        """Substitute variables and return the rendered string.

        Args:
            **kwargs: variable values keyed by name.

        Returns:
            Rendered prompt string.

        Raises:
            PromptVarsError: if strict=True and a variable is missing.
        """
        if self.strict:
            unknown = set(kwargs) - set(self._vars)
            if unknown:
                raise PromptVarsError(
                    f"unknown variable(s): {', '.join(sorted(unknown))}"
                )
        return _substitute(
            self.template,
            kwargs,
            double_brace=self.double_brace,
            strict=self.strict,
            allow_partial=False,
        )

    def render_partial(self, **kwargs: Any) -> "PromptTemplate":
        """Substitute available variables; return a new template with remaining ones.

        Useful for multi-stage filling where some variables are known now and
        others will be filled later.
        """
        filled = _substitute(
            self.template,
            kwargs,
            double_brace=self.double_brace,
            strict=False,
            allow_partial=True,
        )
        return PromptTemplate(filled, double_brace=self.double_brace, strict=self.strict)

    def variables(self) -> list[str]:
        """Return all variable names in order of first appearance (with duplicates)."""
        return list(self._vars)

    def is_complete(self, **kwargs: Any) -> bool:
        """Return True if all template variables are covered by kwargs."""
        return set(self.required_vars) <= set(kwargs)

    def missing_vars(self, **kwargs: Any) -> list[str]:
        """Return variable names not present in kwargs."""
        return [v for v in self.required_vars if v not in kwargs]

    def __str__(self) -> str:
        return self.template

    def __repr__(self) -> str:
        return f"PromptTemplate(vars={self.required_vars!r})"


def fill(
    template: str,
    *,
    double_brace: bool = True,
    strict: bool = True,
    **kwargs: Any,
) -> str:
    """One-shot substitution of variables in a template string.

    Args:
        template: template string with ``{{variable}}`` placeholders.
        double_brace: if True (default), use ``{{var}}`` syntax; else ``{var}``.
        strict: if True (default), raise on missing variables.
        **kwargs: variable values.

    Returns:
        Rendered string.

    Example::

        prompt = fill("Hello, {{name}}!", name="World")
    """
    return _substitute(
        template,
        kwargs,
        double_brace=double_brace,
        strict=strict,
        allow_partial=not strict,
    )
