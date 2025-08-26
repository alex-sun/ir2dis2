# Rule: Keep Python dependencies inside the project (readable by the agent)

## Goal
Ensure all Python dependencies are installed **inside the repository**, **not** into Docker layers or global/user sites, and that the agent can **read their source files**.

## Terms
- **VENDOR_DIR**: `./.python_packages` 
- **LOCK_FILES**: `requirements.txt`

## Installing dependencies (project-only, not inside Docker)
- Use `make install` to install dependencies

## Benefits
- You can now access sources of installed dependencies. Please remember it and use it when needed