# Repository Guidelines

## Project Structure & Module Organization
- Core scripts live at the repo root: `analyze.py` (path extraction), `classify.py` (LLM-driven PII labelling), `redact.py` (apply replacements), and `hidepiik` (CLI wrapper wiring the three stages).
- Sample data and expected outputs are in `examples/` (`input.json`, `analysis.json`, `config.json`, `clean.json`) and are safe to use for local checks.
- Keep new helper modules co-located with the current scripts unless you introduce a clear package boundary; prefer small, single-purpose functions.

## Build, Test, and Development Commands
- Run from the repo root with Python 3.11+:  
  ```bash
  python hidepiik analyze examples/input.json > analysis.json
  python hidepiik classify analysis.json pii_config.json
  python hidepiik redact examples/input.json examples/config.json > clean.json
  python hidepiik clean examples/input.json --save-intermediates
  ```
- `LLM_API_KEY` is required for `classify`/`clean`; optionally set `LLM_BASE_URL` and `LLM_MODEL` (defaults: `https://api.openai.com/v1`, `gpt-4o`).
- Capture stderr messages when debugging; the CLI prints progress and prompts there.

## Coding Style & Naming Conventions
- Python, 4-space indentation, `snake_case` for functions/variables, and descriptive names for CLI flags.
- Keep I/O in `hidepiik`; keep pure transformations in the helper modules to ease testing.
- Avoid committing secrets; read configuration from environment variables rather than hardcoding.

## Testing Guidelines
- No automated test suite yet; validate changes with the `examples/` fixtures and compare `clean.json` diffs.
- When adding tests, create a `tests/` folder and use `pytest`; name files `test_*.py` and cover `traverse`, `get_pii_config` prompt shaping (mock the client), and `traverse_and_redact`.
- For regression checks, add minimal JSON fixtures that isolate the edge case you are fixing (e.g., nested lists of primitives).

## Commit & Pull Request Guidelines
- Existing history favors short, imperative messages (e.g., `Add examples`, `Add hidepiik CLI wrapper`); follow the same style.
- In PRs, include: what changed, why, reproduction steps or commands run, and before/after snippets if output changes.
- Link related issues and mention any env vars or external services needed to verify the change; never attach real PII in samples.

## Security & Configuration Tips
- Keep API keys in your shell environment or `.envrc`; do not commit them or include them in logs.
- Prefer redacting or synthesizing data in new fixtures; treat anything resembling real user data as sensitive.
- If adjusting prompts or schema handling, note any new PII labels introduced so downstream consumers can update allowlists.
