"""Load and render email templates by name (HTML / optional plain text files)."""
import re
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).resolve().parent
_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def _render_string(template: str, name: str, context: dict[str, str | int]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise KeyError(f"Missing template variable {key!r} for template {name!r}")
        return str(context[key])

    return _PLACEHOLDER.sub(replace, template)


def _template_path(name: str, suffix: str) -> Path:
    return _TEMPLATES_DIR / f"{name}{suffix}"


def render_template(name: str, **context: str | int) -> str:
    """Render ``{name}.html`` with ``{{ variable }}`` placeholders."""
    path = _template_path(name, ".html")
    if not path.is_file():
        raise FileNotFoundError(f"Email HTML template not found: {path}")
    return _render_string(path.read_text(encoding="utf-8"), name, context)


def render_text_template(name: str, **context: str | int) -> str | None:
    """Render ``{name}.txt`` if present; otherwise ``None``."""
    path = _template_path(name, ".txt")
    if not path.is_file():
        return None
    return _render_string(path.read_text(encoding="utf-8"), name, context)


def list_template_names() -> list[str]:
    """Return template names that have a ``.html`` file."""
    return sorted(p.stem for p in _TEMPLATES_DIR.glob("*.html"))
