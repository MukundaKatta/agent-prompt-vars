# agent-prompt-vars

Simple `{{variable}}` substitution for prompt templates — no Jinja2, no dependencies.

Zero dependencies. Python 3.10+. MIT.

It does exactly one thing: replace `{{name}}` placeholders in a string with values
you supply. Unlike a full template engine, it adds nothing you don't need — no loops,
no conditionals, no filters, no autoescaping — which makes it predictable for building
LLM prompts where you want every character to be intentional. On top of plain
substitution it adds three things that matter when prompts get assembled in stages:

- **missing-variable detection** (`missing_vars`, `is_complete`) so you can validate
  before sending a prompt to a model,
- **strict vs. lenient** behaviour — raise on missing/unknown variables, or leave
  placeholders untouched,
- **partial fill** (`render_partial`) for multi-stage assembly where some values are
  known now and others later.

## Install

```bash
pip install agent-prompt-vars
```

## Usage

```python
from agent_prompt_vars import fill

prompt = fill(
    "You are a {{role}}.\n\nUser: {{question}}",
    role="research assistant",
    question="What is quantum entanglement?",
)
```

## PromptTemplate

```python
from agent_prompt_vars import PromptTemplate

tmpl = PromptTemplate(
    "You are a {{role}}.\n\nResearch topic: {{topic}}\n\nUser: {{question}}"
)

# Inspect variables
tmpl.required_vars   # ["question", "role", "topic"]
tmpl.missing_vars(role="researcher")  # ["question", "topic"]
tmpl.is_complete(role="r", topic="t", question="q")  # True

# Render
prompt = tmpl.render(role="researcher", topic="ML", question="What is backprop?")
```

## Partial fill

```python
# Fill some variables now, the rest later
partial = tmpl.render_partial(role="researcher", topic="ML")
# partial is a new PromptTemplate — {{question}} still a placeholder

final = partial.render(question="What is backprop?")
```

## Single-brace syntax

```python
tmpl = PromptTemplate("Hello, {name}!", double_brace=False)
result = tmpl.render(name="World")
```

## Lenient mode

```python
# Leave unknown placeholders unchanged instead of raising
result = fill("Hello, {{name}}!", strict=False)
# "Hello, {{name}}!"
```

## API reference

### `fill(template, *, double_brace=True, strict=True, **kwargs) -> str`

One-shot substitution. Returns the rendered string.

- `template` — the string containing placeholders.
- `double_brace` — `True` uses `{{var}}`; `False` uses `{var}`.
- `strict` — `True` raises `PromptVarsError` listing any unfilled variables;
  `False` leaves unknown placeholders untouched.
- `**kwargs` — variable values keyed by name. Extra kwargs that don't appear in the
  template are ignored.

Variable names may contain word characters and dots (e.g. `{{user.name}}` filled with
`fill(tmpl, **{"user.name": "Bob"})`). Substitution is single-pass: a value that itself
looks like a placeholder is **not** expanded again.

### `class PromptTemplate(template, *, double_brace=True, strict=True)`

A reusable, pre-parsed template. Construction scans the placeholders once.

| Member | Description |
| --- | --- |
| `template` | The original template string. |
| `required_vars` | Sorted, de-duplicated list of variable names in the template. |
| `variables()` | Variable names in order of first appearance, **including** duplicates. |
| `render(**kwargs) -> str` | Render the template. When `strict=True`, raises `PromptVarsError` on missing **or** unknown variables. |
| `render_partial(**kwargs) -> PromptTemplate` | Fill the variables you have now; return a **new** `PromptTemplate` for the rest (preserves `double_brace`/`strict`). |
| `is_complete(**kwargs) -> bool` | `True` if every required variable is supplied (extra kwargs are ignored). |
| `missing_vars(**kwargs) -> list[str]` | Required variables not present in `kwargs`. |
| `str(tmpl)` | The template string. |
| `repr(tmpl)` | e.g. `PromptTemplate(vars=['question', 'role'])`. |

### `class PromptVarsError(Exception)`

Raised on template errors: missing variables (strict mode) and, for
`PromptTemplate.render`, unknown variables. The message lists the offending names
sorted alphabetically.

## Development

The package has no runtime dependencies. Run the test suite with the standard library
only — no pytest, no installation required:

```bash
python3 -m unittest discover -s tests
```

CI runs the same command across Python 3.10–3.13.

## License

MIT
