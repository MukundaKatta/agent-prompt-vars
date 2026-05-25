# agent-prompt-vars

Simple `{{variable}}` substitution for prompt templates — no Jinja2, no dependencies.

Zero dependencies. Python 3.10+. MIT.

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

## License

MIT
