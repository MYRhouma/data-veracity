"""VLA Manager API — sole owner of Veracity Level Agreements.

Hosted at the Data Intermediary. Serves the VLA authoring UI and answers
``GET /vla/{id}`` requests from each participant's DVA API during VLA
resolution in the synchronous attestation flow.

This module deliberately does *not* perform any evaluation, attestation
or credential issuance — those are concerns of other components. VLA
Manager API owns only VLAs (and, eventually, VLA templates and the
"test requirements while building VLAs" proxy endpoint).
"""

__version__ = "0.1.0"