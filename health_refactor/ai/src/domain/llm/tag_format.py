"""Tag-based structured output format definition."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TagOutputFormat:
    """Empty-tag skeleton the model must fill in.

    Works for **any** tag tree you define in ``template`` — orders, tickets,
    classifications, addresses, etc. The parser maps tags to JSON:

    - Leaf tag → string (or JSON value if tag is in ``json_tags``)
    - Nested tags → object
    - Repeated sibling tags → array (automatic)
    - Tags in ``list_tags`` → always an array, even with one item

    Example template::

        <name></name>
        <products>
          <product>
            <id></id>
            <title></title>
            <qty></qty>
          </product>
        </products>

    ``list_tags`` — tag names that must always parse as JSON arrays.
    ``json_tags`` — leaf tags whose text body is JSON (optional shortcut).
    """

    template: str
    list_tags: frozenset[str] = frozenset()
    json_tags: frozenset[str] = frozenset()

    @classmethod
    def from_template(
        cls,
        template: str,
        *,
        list_tags: str | frozenset[str] = "",
        json_tags: str | frozenset[str] = "",
    ) -> "TagOutputFormat":
        """Build from template file text and comma-separated tag names."""

        def _to_set(value: str | frozenset[str]) -> frozenset[str]:
            if isinstance(value, frozenset):
                return value
            return frozenset(tag.strip() for tag in value.split(",") if tag.strip())

        return cls(
            template=template.strip(),
            list_tags=_to_set(list_tags),
            json_tags=_to_set(json_tags),
        )
