# Local BaseAgent Source

This directory vendors the `base_agents` package source used by the backend.

- Source path copied from: `E:/PythonProjects/HowtoCook/.venv/Lib/site-packages/base_agents`
- Package version: `0.2.7`
- The backend imports this local package directly when started from `backend/`.
- Runtime dependencies are declared in `backend/requirements.txt`; do not install `base-agent` separately for this project.

The package code is kept local so `base-agent-trip-planner` can run as a complete project without depending on another virtual environment.
