"""Tests for agent-prompt-vars."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import pytest
from agent_prompt_vars import PromptTemplate, PromptVarsError, fill


# ---------------------------------------------------------------------------
# fill() — double brace syntax
# ---------------------------------------------------------------------------

def test_fill_basic():
    result = fill("Hello, {{name}}!", name="World")
    assert result == "Hello, World!"

def test_fill_multiple():
    result = fill("{{greeting}}, {{name}}!", greeting="Hi", name="Alice")
    assert result == "Hi, Alice!"

def test_fill_repeated_var():
    result = fill("{{a}} and {{a}} again", a="X")
    assert result == "X and X again"

def test_fill_no_vars():
    result = fill("No variables here.")
    assert result == "No variables here."

def test_fill_int_value():
    result = fill("Count: {{n}}", n=42)
    assert result == "Count: 42"

def test_fill_missing_raises():
    with pytest.raises(PromptVarsError, match="missing variable"):
        fill("Hello, {{name}}!")  # no name provided

def test_fill_not_strict():
    result = fill("Hello, {{name}}!", strict=False)
    assert "{{name}}" in result  # placeholder preserved

def test_fill_single_brace():
    result = fill("Hello, {name}!", double_brace=False, name="World")
    assert result == "Hello, World!"

def test_fill_whitespace_in_placeholder():
    result = fill("Hello, {{ name }}!", name="World")
    assert result == "Hello, World!"


# ---------------------------------------------------------------------------
# PromptTemplate
# ---------------------------------------------------------------------------

def test_template_render():
    tmpl = PromptTemplate("You are a {{role}}.")
    assert tmpl.render(role="researcher") == "You are a researcher."

def test_template_required_vars():
    tmpl = PromptTemplate("{{a}} and {{b}} and {{a}}")
    assert tmpl.required_vars == ["a", "b"]  # sorted, unique

def test_template_variables():
    tmpl = PromptTemplate("{{a}} then {{b}} then {{a}}")
    assert tmpl.variables() == ["a", "b", "a"]  # in order with duplicates

def test_template_render_missing_raises():
    tmpl = PromptTemplate("{{a}} and {{b}}")
    with pytest.raises(PromptVarsError, match="missing variable"):
        tmpl.render(a="x")  # b missing

def test_template_render_unknown_raises():
    tmpl = PromptTemplate("{{a}}")
    with pytest.raises(PromptVarsError, match="unknown variable"):
        tmpl.render(a="x", b="y")  # b not in template

def test_template_not_strict_unknown_ok():
    tmpl = PromptTemplate("{{a}}", strict=False)
    result = tmpl.render(a="x", b="y")
    assert result == "x"

def test_template_single_brace():
    tmpl = PromptTemplate("Hello, {name}!", double_brace=False)
    assert tmpl.render(name="World") == "Hello, World!"

def test_template_no_vars():
    tmpl = PromptTemplate("No placeholders.")
    assert tmpl.required_vars == []
    assert tmpl.render() == "No placeholders."


# ---------------------------------------------------------------------------
# PromptTemplate.render_partial
# ---------------------------------------------------------------------------

def test_render_partial_fills_some():
    tmpl = PromptTemplate("{{greeting}}, {{name}}! Your task: {{task}}")
    partial = tmpl.render_partial(greeting="Hello", name="Alice")
    # task still a placeholder
    assert "Hello" in str(partial)
    assert "Alice" in str(partial)
    assert "{{task}}" in str(partial)

def test_render_partial_then_render():
    tmpl = PromptTemplate("{{greeting}}, {{name}}!")
    partial = tmpl.render_partial(greeting="Hi")
    final = partial.render(name="World")
    assert final == "Hi, World!"

def test_render_partial_returns_template():
    tmpl = PromptTemplate("{{a}} {{b}}")
    result = tmpl.render_partial(a="x")
    assert isinstance(result, PromptTemplate)


# ---------------------------------------------------------------------------
# is_complete / missing_vars
# ---------------------------------------------------------------------------

def test_is_complete_true():
    tmpl = PromptTemplate("{{a}} and {{b}}")
    assert tmpl.is_complete(a="x", b="y") is True

def test_is_complete_false():
    tmpl = PromptTemplate("{{a}} and {{b}}")
    assert tmpl.is_complete(a="x") is False

def test_missing_vars():
    tmpl = PromptTemplate("{{a}} and {{b}}")
    assert tmpl.missing_vars(a="x") == ["b"]

def test_missing_vars_none():
    tmpl = PromptTemplate("{{a}}")
    assert tmpl.missing_vars(a="x") == []

def test_is_complete_extra_ok():
    tmpl = PromptTemplate("{{a}}")
    # Extra kwargs are ignored in is_complete
    assert tmpl.is_complete(a="x", b="extra") is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_template():
    result = fill("")
    assert result == ""

def test_multiline_template():
    tmpl = PromptTemplate("Line 1: {{a}}\nLine 2: {{b}}")
    result = tmpl.render(a="hello", b="world")
    assert result == "Line 1: hello\nLine 2: world"

def test_repr():
    tmpl = PromptTemplate("{{a}} {{b}}")
    r = repr(tmpl)
    assert "PromptTemplate" in r
    assert "a" in r

def test_str():
    tmpl = PromptTemplate("Hello, {{name}}!")
    assert str(tmpl) == "Hello, {{name}}!"
