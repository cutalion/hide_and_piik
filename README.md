# PII Redactor

A tool to safely redact Personally Identifiable Information (PII) from JSON files using an LLM for schema classification.

## How it works

1.  **Analyze**: The tool scans your JSON file, extracts unique paths, and generates masked samples (e.g., `Ivan` -> `LLLL`, `123` -> `DDD`).
2.  **Classify**: It sends *only* the paths and masked samples to an LLM (via OpenAI-compatible API) to identify which fields contain PII.
3.  **Redact**: It uses the LLM-generated config to redact the PII from the original file, replacing values with placeholders like `<FULL_NAME>`, `<INN>`, etc.

## Installation

```bash
pip install openai
```

## Usage

### 1. Analyze the Data
Extract paths and masked samples.

```bash
python3 pii_redactor/analyze.py input.json > analysis.json
```

### 2. Classify PII (using LLM)
Send the schema to the LLM to generate a redaction config.

```bash
export LLM_API_KEY="your-api-key"
# Optional:
# export LLM_BASE_URL="https://api.openai.com/v1"
# export LLM_MODEL="gpt-4o"
# (gpt-5* models are supported automatically via the Responses API)

python3 pii_redactor/classify.py analysis.json pii_config.json
```

### 3. Redact the File
Apply the redaction config to the original file.

```bash
python3 pii_redactor/redact.py input.json pii_config.json > clean.json
```

## Files

- `analyze.py`: Extracts paths and generates masked samples.
- `classify.py`: Interacts with LLM to identify PII fields.
- `redact.py`: Applies the redaction rules.
