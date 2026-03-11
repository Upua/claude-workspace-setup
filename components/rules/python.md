---
globs: ["*.py"]
---

# Python Rules

- Run `ruff check .` and `ruff format --check .` before staging Python files.
- Use type hints on all function signatures.
- Prefer `pathlib.Path` over `os.path` for path manipulation.
- Use f-strings, not `.format()` or `%`.
- For projects with a `.venv/`: check `cortex_environment` to confirm the right venv is active before installing packages.
