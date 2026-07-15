"""Unit tests: infrastructure/email/templates/renderer.py"""
import pytest

from backend.src.infrastructure.email.templates.renderer import (
    list_template_names,
    render_template,
    render_text_template,
)


def test_list_template_names_includes_invitation() -> None:
    assert "invitation" in list_template_names()


def test_render_template_substitutes_html_placeholders() -> None:
    html = render_template(
        "invitation",
        app_name="SupportOS AI",
        department_name="Acme Corp",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=user%40example.com&token=abc"
        ),
        expire_hours=72,
    )

    assert "SupportOS AI" in html
    assert "Acme Corp" in html
    assert "token=abc" in html
    assert "{{ department_name }}" not in html


def test_render_text_template_substitutes_txt_placeholders() -> None:
    text = render_text_template(
        "invitation",
        app_name="SupportOS AI",
        department_name="Acme Corp",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=user%40example.com&token=abc"
        ),
        expire_hours=72,
    )

    assert text is not None
    assert "Acme Corp" in text
    assert "72 hours" in text


def test_render_template_raises_when_html_missing() -> None:
    with pytest.raises(FileNotFoundError, match="not-found.html"):
        render_template("not-found", foo="bar")


def test_render_template_raises_on_missing_variable() -> None:
    with pytest.raises(KeyError, match="expire_hours"):
        render_template(
            "invitation",
            app_name="SupportOS AI",
            department_name="Acme",
            invitation_link="http://localhost/accept",
        )
