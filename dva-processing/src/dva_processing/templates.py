"""
Template rendering for VLA Templates.

Uses Handlebars-compatible ``{{var}}`` syntax via the ``chevron`` package,
the same way the VLA Manager API renders them, so a template renders
identically whichever service asked for it.
"""

from typing import Any

import chevron


class TemplateRenderError(Exception):
    """The template could not be rendered with the model it was given."""


def render_template(implementation_template: str, model: dict[str, Any]) -> str:
    """Render a Handlebars ``{{var}}`` template string with a model dict."""
    try:
        return chevron.render(implementation_template, model)
    except Exception as e:
        raise TemplateRenderError(str(e)) from e
