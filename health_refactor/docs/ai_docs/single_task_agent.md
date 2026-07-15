# Single-Task LLM Agent

A **single-task agent** is one LLM call: system prompt + optional message history + user
message → response. No tool loop. Use it for extraction, classification, summarisation,
or follow-up turns with prior context.

Three call modes exist on every registered provider:

| Method | Input | Output |
|--------|--------|--------|
| `run` | `SingleTaskAgentRequest` | Plain text (`content`) |
| `stream` | `SingleTaskAgentRequest` (`stream=True`) | Token chunks |
| `run_structured` | `StructuredSingleTaskAgentRequest` + `JsonOutputFormat` | Parsed JSON (`data`) + raw (`raw`) |

`run_structured` **always calls the real LLM**. The model returns `<json>...</json>`; our
parser extracts and `json.loads` the payload. `raw` is exactly what the model wrote;
`data` is the parsed dict.

---

## Architecture

```
Application                    Domain                         Infrastructure
─────────────────────────────────────────────────────────────────────────────
SingleTaskAgentRunner    →     ISingleTaskAgentProvider  →   OpenAISingleTaskAgentProvider
  .run / .stream /              types, JsonOutputFormat         (extends BaseSingleTaskAgentProvider)
  .run_structured               structured_prompt, json_parser
                                structured.py
```

### Key files

| Path | Role |
|------|------|
| `ai/src/domain/llm/interfaces.py` | `ISingleTaskAgentProvider` protocol |
| `ai/src/domain/llm/types.py` | Request/result dataclasses |
| `ai/src/domain/llm/messages.py` | `ChatMessage`, `build_message_dicts()` |
| `ai/src/domain/llm/json_format.py` | `JsonOutputFormat` — JSON example shape |
| `ai/src/domain/llm/json_parser.py` | `parse_json_output()` — `<json>` → dict |
| `ai/src/domain/llm/structured_prompt.py` | Injects shape + rules into system prompt |
| `ai/src/domain/llm/structured.py` | `run_structured_completion()` — shared orchestration |
| `ai/src/domain/llm/prompt_templates.py` | Reusable system prompts (order, ticket, …) |
| `ai/src/infrastructure/llm/providers/base.py` | `BaseSingleTaskAgentProvider` — default `run_structured` |
| `ai/src/infrastructure/llm/providers/openai.py` | OpenAI implementation |
| `ai/src/infrastructure/llm/registry.py` | Provider registry |
| `ai/src/infrastructure/llm/factory.py` | `get_single_task_provider()`, bootstrap |
| `ai/src/application/single_task_agent/runner.py` | Thin delegate to registered provider |

### Flow — `run_structured`

```
Your code → provider.run_structured(request)
         → build_structured_system_prompt(base_system, output_format)
              (appends rules + <json>{example shape}</json> to system prompt)
         → provider.run(llm_request)          ← real LLM call
         → parse_json_output(raw, output_format)
         → StructuredSingleTaskAgentResult(data={...}, raw="<json>...")
```

---

## Message history

Both request types accept optional prior turns via `message_history`. Default is `()`.

```python
from ai.src.domain.llm.messages import ChatMessage, MessageRole

message_history = (
    ChatMessage(role=MessageRole.USER, content="I need to place an order."),
    ChatMessage(role=MessageRole.ASSISTANT, content="Share the line items."),
)
```

Order sent to LLM: `system` → history (`user`/`assistant`) → current `user` (`prompt`).

---

## Quick start

Requires `OPENAI_API_KEY` in `.env` at monorepo root.

```python
import asyncio
import json

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.prompt_templates import ORDER_EXTRACTION_SYSTEM
from ai.src.domain.llm.types import StructuredSingleTaskAgentRequest
from ai.src.infrastructure.llm.factory import get_single_task_provider

OUTPUT_FORMAT = JsonOutputFormat.from_file("ai/scripts/fixtures/order_json_format.json")

async def main():
    request = StructuredSingleTaskAgentRequest(
        system_prompt=ORDER_EXTRACTION_SYSTEM,
        prompt="Acme Corp: 1x Widget Pro (W-100), 2x Gadget Mini (G-200).",
        provider="openai",
        model="gpt-4o-mini",
        output_format=OUTPUT_FORMAT,
        temperature=0.1,
    )
    result = await get_single_task_provider("openai").run_structured(request)
    print(json.dumps(result.data, indent=2))

asyncio.run(main())
```

```bash
python test.py
python ai/scripts/test_single_task_agent.py structured --preset order
python ai/scripts/test_json_parser.py --preset order   # no API key
```

---

## Structured output — JSON in `<json>`

### 1. Define a JSON example (dummy values)

Users define the shape with placeholder values — e.g. `"sam"`, `""`, `0`:

```json
{
  "name": "sam",
  "products": [
    {"id": "", "title": "", "qty": 0}
  ]
}
```

Save as `ai/scripts/fixtures/order_json_format.json` or pass a dict in code.

More examples: `ticket_json_format.json`, `classification_json_format.json`.

### 2. Wrap in `JsonOutputFormat`

```python
from ai.src.domain.llm.json_format import JsonOutputFormat

# From file
fmt = JsonOutputFormat.from_file("ai/scripts/fixtures/order_json_format.json")

# From dict
fmt = JsonOutputFormat.from_example({"name": "sam", "priority": "medium"})

# From JSON string
fmt = JsonOutputFormat.from_example('{"name": "sam"}')
```

### 3. Write prompts

| Part | What to put |
|------|-------------|
| **System prompt** | Task + field semantics (allowed values, “source only”) |
| **User prompt (`prompt`)** | Context to extract from (email, chat, ticket body) |
| **JSON shape** | Auto-appended to system prompt inside `<json>...</json>` |

Reusable system prompts: `ORDER_EXTRACTION_SYSTEM`, `TICKET_EXTRACTION_SYSTEM`,
`CLASSIFICATION_EXTRACTION_SYSTEM` in `prompt_templates.py`.

### 4. Call `run_structured`

```python
result = await get_single_task_provider("openai").run_structured(
    StructuredSingleTaskAgentRequest(
        system_prompt=TICKET_EXTRACTION_SYSTEM,
        prompt=ticket_body,
        provider="openai",
        model="gpt-4o-mini",
        output_format=fmt,
    )
)

if not result.parse_success:
    raise ValueError(result.parse_errors)

data = result.data
```

### 5. Example output

**`raw`** (from LLM):

```xml
<json>
{"name": "Acme Corp", "products": [{"id": "W-100", "title": "Widget Pro", "qty": 1}]}
</json>
```

**`data`** (after parser):

```json
{
  "name": "Acme Corp",
  "products": [{"id": "W-100", "title": "Widget Pro", "qty": 1}]
}
```

---

## Creating a new structured-output agent

1. **Design JSON example** — dummy values show the shape arrays/objects use.
2. **Save** — e.g. `ai/scripts/fixtures/my_task_json_format.json`.
3. **Add system prompt** — `prompt_templates.py`.
4. **Build** — `JsonOutputFormat.from_file(...)` or `from_example(...)`.
5. **Pass context** in `prompt`.
6. **Call** `provider.run_structured()`.
7. **Handle** `parse_success` / `parse_errors`.
8. **Test parser** — `test_json_parser.py` (no API key).
9. **Test LLM** — `test.py` or CLI `structured --preset`.

---

## Adding a new LLM provider

Implement **`run`** and **`stream`**. **`run_structured`** is inherited from
`BaseSingleTaskAgentProvider` (uses `<json>` parsing by default).

Register in `ai/src/infrastructure/llm/factory.py`. Mirror tests in
`test_openai_provider.py`.

---

## Token efficiency tips

- JSON example shape is more compact than XML tags for nested/list data.
- One array entry per distinct item; use `qty` fields instead of duplicating rows.
- Keep system prompts short; put context in `prompt`.
- Use `temperature=0.1` for extraction.
- `--dry-run` prints the full system prompt without an API call.

---

## Tests

| What | Command |
|------|---------|
| JSON parser unit tests | `pytest tests/ai_tests/unit/domain/llm/test_json_parser.py -q --no-cov` |
| Provider unit tests | `pytest tests/ai_tests/unit/infrastructure/llm/ -q --no-cov` |
| Runner / structured | `pytest tests/ai_tests/unit/application/single_task_agent/ -q --no-cov` |
| Parser CLI (no LLM) | `python ai/scripts/test_json_parser.py --preset order` |
| Smoke test (real LLM) | `python test.py` |

Fixtures: `ai/scripts/fixtures/*_json_format.json`, presets in `ai/scripts/llm_presets.py`.
