"""Tests for agent-prompt-vars.

Uses only the Python standard library (``unittest``) so the suite runs with::

    python3 -m unittest discover -s tests

No third-party test dependencies are required.
"""

import os
import sys
import unittest

# Make the package importable when running from a checkout without installing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from agent_prompt_vars import PromptTemplate, PromptVarsError, fill


class TestFillDoubleBrace(unittest.TestCase):
    """fill() with the default {{var}} syntax."""

    def test_fill_basic(self):
        self.assertEqual(fill("Hello, {{name}}!", name="World"), "Hello, World!")

    def test_fill_multiple(self):
        self.assertEqual(
            fill("{{greeting}}, {{name}}!", greeting="Hi", name="Alice"),
            "Hi, Alice!",
        )

    def test_fill_repeated_var(self):
        self.assertEqual(fill("{{a}} and {{a}} again", a="X"), "X and X again")

    def test_fill_no_vars(self):
        self.assertEqual(fill("No variables here."), "No variables here.")

    def test_fill_int_value(self):
        self.assertEqual(fill("Count: {{n}}", n=42), "Count: 42")

    def test_fill_zero_value(self):
        # 0 is falsy but must still be substituted.
        self.assertEqual(fill("Count: {{n}}", n=0), "Count: 0")

    def test_fill_none_value(self):
        self.assertEqual(fill("Value: {{x}}", x=None), "Value: None")

    def test_fill_missing_raises(self):
        with self.assertRaisesRegex(PromptVarsError, "missing variable"):
            fill("Hello, {{name}}!")  # no name provided

    def test_fill_not_strict_preserves_placeholder(self):
        result = fill("Hello, {{name}}!", strict=False)
        self.assertIn("{{name}}", result)  # placeholder preserved

    def test_fill_not_strict_mixed(self):
        # Known vars filled, unknown ones left untouched.
        self.assertEqual(
            fill("Hello {{name}}, {{missing}}", name="X", strict=False),
            "Hello X, {{missing}}",
        )

    def test_fill_whitespace_in_placeholder(self):
        self.assertEqual(fill("Hello, {{ name }}!", name="World"), "Hello, World!")

    def test_fill_dotted_var(self):
        self.assertEqual(fill("{{user.name}}", **{"user.name": "Bob"}), "Bob")

    def test_fill_single_pass_no_reexpansion(self):
        # A value that itself looks like a placeholder is NOT expanded again.
        self.assertEqual(fill("{{a}}", a="{{b}}"), "{{b}}")

    def test_fill_extra_kwargs_ignored(self):
        # fill() does not validate unknown kwargs (unlike strict render()).
        self.assertEqual(fill("{{a}}", a="1", zzz="2"), "1")


class TestFillSingleBrace(unittest.TestCase):
    """fill() with the {var} (single-brace) syntax."""

    def test_fill_single_brace(self):
        self.assertEqual(
            fill("Hello, {name}!", double_brace=False, name="World"),
            "Hello, World!",
        )

    def test_fill_single_brace_missing_raises(self):
        with self.assertRaisesRegex(PromptVarsError, "missing variable"):
            fill("Hello, {name}!", double_brace=False)


class TestPromptTemplate(unittest.TestCase):
    def test_render(self):
        tmpl = PromptTemplate("You are a {{role}}.")
        self.assertEqual(tmpl.render(role="researcher"), "You are a researcher.")

    def test_required_vars_sorted_unique(self):
        tmpl = PromptTemplate("{{a}} and {{b}} and {{a}}")
        self.assertEqual(tmpl.required_vars, ["a", "b"])

    def test_variables_order_with_duplicates(self):
        tmpl = PromptTemplate("{{a}} then {{b}} then {{a}}")
        self.assertEqual(tmpl.variables(), ["a", "b", "a"])

    def test_render_missing_raises(self):
        tmpl = PromptTemplate("{{a}} and {{b}}")
        with self.assertRaisesRegex(PromptVarsError, "missing variable"):
            tmpl.render(a="x")  # b missing

    def test_render_unknown_raises(self):
        tmpl = PromptTemplate("{{a}}")
        with self.assertRaisesRegex(PromptVarsError, "unknown variable"):
            tmpl.render(a="x", b="y")  # b not in template

    def test_not_strict_unknown_ok(self):
        tmpl = PromptTemplate("{{a}}", strict=False)
        self.assertEqual(tmpl.render(a="x", b="y"), "x")

    def test_not_strict_missing_preserved(self):
        tmpl = PromptTemplate("{{a}} {{b}}", strict=False)
        self.assertEqual(tmpl.render(a="x"), "x {{b}}")

    def test_single_brace(self):
        tmpl = PromptTemplate("Hello, {name}!", double_brace=False)
        self.assertEqual(tmpl.render(name="World"), "Hello, World!")

    def test_no_vars(self):
        tmpl = PromptTemplate("No placeholders.")
        self.assertEqual(tmpl.required_vars, [])
        self.assertEqual(tmpl.render(), "No placeholders.")


class TestRenderPartial(unittest.TestCase):
    def test_fills_some_keeps_rest(self):
        tmpl = PromptTemplate("{{greeting}}, {{name}}! Your task: {{task}}")
        partial = tmpl.render_partial(greeting="Hello", name="Alice")
        self.assertIn("Hello", str(partial))
        self.assertIn("Alice", str(partial))
        self.assertIn("{{task}}", str(partial))

    def test_returns_template(self):
        tmpl = PromptTemplate("{{a}} {{b}}")
        result = tmpl.render_partial(a="x")
        self.assertIsInstance(result, PromptTemplate)

    def test_remaining_required_vars(self):
        tmpl = PromptTemplate("{{a}} {{b}}")
        partial = tmpl.render_partial(a="x")
        self.assertEqual(partial.required_vars, ["b"])

    def test_then_render(self):
        tmpl = PromptTemplate("{{greeting}}, {{name}}!")
        partial = tmpl.render_partial(greeting="Hi")
        self.assertEqual(partial.render(name="World"), "Hi, World!")

    def test_preserves_brace_style(self):
        tmpl = PromptTemplate("Hello, {name}!", double_brace=False)
        partial = tmpl.render_partial()
        self.assertFalse(partial.double_brace)
        self.assertEqual(partial.render(name="World"), "Hello, World!")


class TestIntrospection(unittest.TestCase):
    def test_is_complete_true(self):
        tmpl = PromptTemplate("{{a}} and {{b}}")
        self.assertTrue(tmpl.is_complete(a="x", b="y"))

    def test_is_complete_false(self):
        tmpl = PromptTemplate("{{a}} and {{b}}")
        self.assertFalse(tmpl.is_complete(a="x"))

    def test_is_complete_no_vars(self):
        tmpl = PromptTemplate("no vars")
        self.assertTrue(tmpl.is_complete())

    def test_is_complete_extra_ok(self):
        tmpl = PromptTemplate("{{a}}")
        self.assertTrue(tmpl.is_complete(a="x", b="extra"))

    def test_missing_vars(self):
        tmpl = PromptTemplate("{{a}} and {{b}}")
        self.assertEqual(tmpl.missing_vars(a="x"), ["b"])

    def test_missing_vars_none(self):
        tmpl = PromptTemplate("{{a}}")
        self.assertEqual(tmpl.missing_vars(a="x"), [])


class TestEdgeCases(unittest.TestCase):
    def test_empty_template(self):
        self.assertEqual(fill(""), "")

    def test_multiline_template(self):
        tmpl = PromptTemplate("Line 1: {{a}}\nLine 2: {{b}}")
        self.assertEqual(
            tmpl.render(a="hello", b="world"), "Line 1: hello\nLine 2: world"
        )

    def test_repr(self):
        tmpl = PromptTemplate("{{a}} {{b}}")
        r = repr(tmpl)
        self.assertIn("PromptTemplate", r)
        self.assertIn("a", r)

    def test_str(self):
        tmpl = PromptTemplate("Hello, {{name}}!")
        self.assertEqual(str(tmpl), "Hello, {{name}}!")

    def test_error_lists_all_missing_sorted(self):
        with self.assertRaisesRegex(PromptVarsError, "b, c"):
            fill("{{c}} {{b}}")  # both missing, reported sorted


if __name__ == "__main__":
    unittest.main()
