"""DVA Verifiable Credential Manager.

Hosted at each Participant. Owns:

* The Ed25519 signing key for that participant (loaded from a file or
  generated on first boot via PyNaCl — never a hand-rolled crypto
  primitive).
* The ``did:key`` whitelist of trusted attesters (used by the verify
  side).
* The W3C VC 2.0 JSON-LD payload shape used for the Attestation of
  Veracity (AoV) — produced and consumed verbatim, never mutated.

The service exposes ``POST /aov/issue`` (called by the DVA API during
credential issuance in the synchronous attestation flow) and
``POST /aov/verify`` (called by the DVA API during the consumer-side
verification flow).
"""

__version__ = "0.1.0"