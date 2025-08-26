# Rule: Keep Python packages local to the project

## Scope
Applies to any Python work in this workspace unless the user explicitly asks to use a virtualenv/Conda/Poetry.

## Installation target
- Always install dependencies into `./.python_packages/` using pip’s **--target**.
- Never call `pip install ...` without `--target` (avoid global/site installs).

### Canonical install command
```bash
python -m pip install --upgrade -r requirements.txt --target ./.python_packages --no-warn-script-location
