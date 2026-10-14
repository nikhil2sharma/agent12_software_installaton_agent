# agent12 - Latest Version Checker

## Nayi machine pe chalao
1. uv install karo:
   - Linux/Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows:   `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. `cd agent12`
3. `uv sync`
4. `.env.example` ko `.env`
5. `uv run agent12.py`

Result folder `latest_versions.csv`
