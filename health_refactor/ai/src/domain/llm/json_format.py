"""JSON example-based structured output format definition."""
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JsonOutputFormat:
    """Dummy-value JSON skeleton the model must fill in.

    Example::

        {"name": "sam", "products": [{"id": "", "title": "", "qty": 0}]}

    The model replies with ``<json>...</json>`` containing valid JSON of the same shape.
    """

    template: str

    @classmethod
    def from_example(cls, example: dict[str, Any] | str) -> "JsonOutputFormat":
        """Build from a dict or JSON string (dummy values like ``sam``, ``0``, ``\"\"``)."""
        if isinstance(example, str):
            parsed = json.loads(example)
        else:
            parsed = example
        if not isinstance(parsed, dict):
            raise ValueError("JSON output format root must be an object")
        template = json.dumps(parsed, indent=2)
        return cls(template=template)

    @classmethod
    def from_file(cls, path: str) -> "JsonOutputFormat":
        from pathlib import Path

        return cls.from_example(Path(path).read_text(encoding="utf-8"))
