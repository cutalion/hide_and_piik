import json
import os
import sys
from openai import BadRequestError, OpenAI
from pydantic import BaseModel, Field

def _extract_responses_text(response):
    """Turn a Responses API response into plain text content."""
    try:
        return response.output[0].content[0].text
    except Exception:
        pass
    if hasattr(response, "output_text"):
        return response.output_text
    raise RuntimeError("Unexpected responses payload; cannot parse text.")

CHAT_TEMPERATURE = 1.0


class PIIConfigModel(BaseModel):
    __root__: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping between JSON paths and uppercase PII labels.",
    )

    class Config:
        schema_extra = {
            "type": "object",
            "properties": {},
            "additionalProperties": {
                "type": "string",
                "description": "Uppercase PII label such as FULL_NAME or EMAIL.",
            },
        }

    def to_dict(self):
        return self.__root__


def get_pii_config(analysis_data, api_key, base_url, model, reasoning_effort="low"):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    system_prompt = """You are a Data Privacy and PII (Personally Identifiable Information) detection expert.
Your goal is to analyze a list of JSON paths and their sample values to identify which ones contain PII.

The sample values have been masked:
- Letters are replaced with 'L'
- Digits are replaced with 'D'
- Punctuation and other characters are preserved.

Input Format:
A JSON list of objects, each containing "path" and "samples".

Output Format:
Return ONLY a valid JSON object (no markdown formatting, no explanations).
The keys must be the exact paths from the input that contain PII.
The values must be the specific PII type (uppercase string).

Common PII Types to detect:
- FULL_NAME (e.g., "LLLLL LLL L.")
- EMAIL
- PHONE
- PASSPORT_NUMBER, PASSPORT_SERIES
- INN (Tax ID), KPP, OGRN (Company IDs)
- DATE_OF_BIRTH, DATE_OF_ISSUE, DOCUMENT_DATE
- ADDRESS
- CREDIT_CARD
- IP_ADDRESS

You may invent new PII types if none of the above fit (e.g. DRIVER_LICENSE, SOCIAL_MEDIA_HANDLE), but prefer standard ones if possible.

If a path does not contain PII (e.g., boolean flags, internal IDs, timestamps, types), DO NOT include it in the output.
"""

    user_prompt = f"""Analyze these paths and samples and generate the PII configuration JSON:

{json.dumps(analysis_data, indent=2, ensure_ascii=False)}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    use_responses_api = model.startswith("gpt-5")
    reasoning_effort = (reasoning_effort or "").strip()
    reasoning_params = {"effort": reasoning_effort} if reasoning_effort else None

    try:
        if use_responses_api:
            try:
                response = client.responses.parse(
                    model=model,
                    input=messages,
                    text_format=PIIConfigModel,
                    reasoning=reasoning_params,
                )
                parsed = response.output_parsed
                if parsed is not None:
                    return parsed.to_dict()
                content = _extract_responses_text(response)
                return json.loads(content)
            except BadRequestError as err:
                if "Unsupported response_format type" not in str(err):
                    raise
                response = client.responses.create(
                    model=model,
                    input=messages,
                    reasoning=reasoning_params,
                )
                content = _extract_responses_text(response)
                return json.loads(content)
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=CHAT_TEMPERATURE
            )
            content = response.choices[0].message.content
            return json.loads(content)
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python classify.py <analysis_output.json> [output_config.json]")
        print("\nEnvironment variables required:")
        print("  LLM_API_KEY")
        print("  LLM_BASE_URL (optional, default: https://api.openai.com/v1)")
        print("  LLM_MODEL (optional, default: gpt-4o)")
        print("  LLM_REASONING_EFFORT (optional, default: low; applies to gpt-5*)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "pii_config.json"

    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY environment variable is not set.")
        sys.exit(1)
    
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-5-codex")
    reasoning_effort = os.environ.get("LLM_REASONING_EFFORT", "low")

    print(f"Reading analysis from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    print(f"Calling LLM ({model}) to classify PII...")
    pii_config = get_pii_config(analysis_data, api_key, base_url, model, reasoning_effort)

    print(f"Saving config to {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pii_config, f, indent=2, ensure_ascii=False)
        print("Done.")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
