"""
Client for the VLA Manager API.

Only one call is needed: ``GET /template/{id}``, to fetch the template
``POST /evaluate/from-template`` renders.  Failures are raised as the two
exceptions below so the routes can tell "no such template" (a ``404`` the
caller caused) from "the upstream is not answering" (a ``502``).
"""

from typing import Any
from uuid import UUID

import requests

from .config import cfg
from .log import get_logger

logger = get_logger()

# The VLA Manager is a sibling service on the same network, so a request
# that has not been answered by now is not going to be.
TIMEOUT_SECONDS = 10


class TemplateNotFoundError(Exception):
    """The VLA Manager has no template with the requested ID."""

    def __init__(self, template_id: UUID) -> None:
        self.template_id = template_id
        super().__init__(f"No template {template_id} at the VLA Manager API")


class VLAManagerError(Exception):
    """The VLA Manager could not be reached, or answered unusably."""


def fetch_template(template_id: UUID) -> dict[str, Any]:
    """Return the VLA template with the given ID."""
    url = f"{cfg.vla_manager_url}/template/{template_id}"
    logger.debug("Fetching template from the VLA Manager API", url=url)
    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        raise VLAManagerError(f"Request to the VLA Manager API failed: {e}") from e

    if resp.status_code == requests.codes.not_found:
        raise TemplateNotFoundError(template_id)

    try:
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError) as e:
        raise VLAManagerError(f"Unusable VLA Manager API response: {e}") from e
