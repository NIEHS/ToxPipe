# Agent Skills
[Read more at Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

Agent Skills are a framework developed by Anthropic for creating reusable, standardized instructions and context to better inform a model with domain-specific capabilities. The benefits of using Skills include:
- Providing organizational or domain knowledge to an agent
- Making agent performance more consistent by referencing the same set of Skills each time
- Reusing a Skill since they are not ephemeral and exist as files on the filesystem
- Updating Skills at runtime to improve/change behavior
- Allowing emergent behavior from composing multiple Skills together

Skills exist as Markdown (`.md`) files on the filesystem. Each Skill file is typically named `SKILL.md` and is located at a location like: `/skills-folder/skill-name/SKILL.md`

An example skill for best practices for developing Python code is provided below:

```
---
name: python-code
description: Write idiomatic, production-quality Python following project conventions, type hints, and testing standards
license: MIT
compatibility: opencode
metadata:
  language: Python 3.9+
---

## What I do

Guide the writing of idiomatic, readable, and maintainable Python code — from scripts and data pipelines to web APIs and Shiny/Dash applications — including conventions, patterns, and common pitfalls to avoid.

## When to use me

Load this skill at step 1 (Write) of the agent workflow whenever the target language is Python. Also useful during step 5 (Implement improvements) when adding Python code.

---

## Environment & tooling assumptions

Unless the project specifies otherwise, assume:
- Python 3.9+ (use `from __future__ import annotations` only if 3.7/3.8 support is needed)
- Dependencies managed via `requirements.txt` or `pyproject.toml` (prefer `pyproject.toml` for new projects)
- Formatter: `black` (88-char line length default)
- Linter: `ruff` or `flake8`
- Type checker: `mypy` or `pyright`
- Testing: `pytest`

If the project already has config files (`setup.cfg`, `pyproject.toml`, `.flake8`, `mypy.ini`), read them first and follow whatever they define.

---

## Style & conventions

### Typing
- Use type hints on all function signatures and class attributes.
- Prefer built-in generics (`list[str]`, `dict[str, int]`) over `typing.List`, `typing.Dict` (Python 3.9+).
- Use `Optional[X]` → prefer `X | None` (Python 3.10+) or `Optional[X]` for 3.9.
- Return `None` explicitly when a function has no meaningful return value.

### Naming
- `snake_case` for variables, functions, modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for module-level constants.
- Prefix private attributes/methods with a single underscore `_`.

### Functions & classes
- One function = one responsibility. If it needs a paragraph to describe, split it.
- Prefer pure functions; isolate side effects (I/O, state mutation) at the edges.
- Use dataclasses or Pydantic models for structured data instead of plain dicts.
- Use `__slots__` on performance-sensitive classes.

### Error handling
- Catch specific exceptions, never bare `except:` or `except Exception:` without re-raising or logging.
- Use custom exception classes for domain errors; inherit from the closest built-in.
- Fail fast: validate inputs at function entry, not deep inside logic.

### Imports
- Standard library → third-party → local (one blank line between groups).
- Absolute imports over relative where possible.
- Never `import *`.

---

## Common patterns

### Data processing (pandas / polars)
- Prefer `polars` for new code (faster, better type safety). Use `pandas` when the project already depends on it.
- Never iterate rows with a Python loop — use vectorized operations or `apply` sparingly.
- Chain operations rather than assigning intermediate DataFrames unless readability suffers.

### Web / API (FastAPI / Flask)
- Use FastAPI for new APIs: automatic docs, type validation via Pydantic, async support.
- Define Pydantic request/response models; never return raw `dict` from endpoints.
- Use dependency injection for database sessions, auth, and config.
- Always set appropriate HTTP status codes; use `HTTPException` for error responses.

### Shiny for Python
- Use `@reactive.calc` for derived values; `@reactive.effect` for side effects.
- Avoid putting computation inside render functions — delegate to reactive calcs.
- Use module pattern (`ui.nav_panel`, `module.ui`/`module.server`) for reusable components.
- For accessibility: ensure all inputs have labels, use `class_` for screen-reader-friendly markup additions.

### Async
- Use `asyncio` + `async/await`; never mix sync blocking I/O inside async functions.
- Use `httpx.AsyncClient` (not `requests`) for async HTTP.
- Use `asyncio.gather` for concurrent independent tasks.

---

## Testing conventions

- One test file per module: `tests/test_<module>.py`.
- Use `pytest` fixtures for reusable setup.
- Name tests `test_<behavior>_when_<condition>`.
- Aim for tests that are: fast, isolated (no real network/DB without fixtures), and deterministic.
- Use `pytest.mark.parametrize` for data-driven tests.
- Mock external dependencies with `unittest.mock.patch` or `pytest-mock`.
- Test coverage target: ≥ 80% on new code.

---

## Pitfalls to avoid

- Mutable default arguments: `def f(x=[])` → use `def f(x=None): if x is None: x = []`.
- Late binding in closures inside loops: capture with `default=val` in lambda args.
- Swallowing exceptions silently.
- Using `assert` for input validation in production code (stripped by `-O` flag).
- `os.path` over `pathlib.Path` — prefer `pathlib`.
- Hardcoded file paths; use `pathlib.Path(__file__).parent` or config.
- `print()` debugging left in committed code; use the `logging` module.

```
