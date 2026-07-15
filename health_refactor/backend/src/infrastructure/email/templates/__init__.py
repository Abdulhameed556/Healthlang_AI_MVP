"""Email templates: ``{name}.html`` + optional ``{name}.txt``, rendered by name + variables."""
from backend.src.infrastructure.email.templates.renderer import (
    list_template_names,
    render_template,
    render_text_template,
)

__all__ = ["list_template_names", "render_template", "render_text_template"]
