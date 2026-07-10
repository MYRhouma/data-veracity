"""Whitelist repository tests — mirror the behaviour Kotlin
``AdminRoutesTest.kt`` covers (add, list, delete)."""

from __future__ import annotations

import pytest

from dva_vc_manager.whitelist import FakeWhitelist

_KNOWN_DID_KEY = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"


@pytest.fixture
def whitelist() -> FakeWhitelist:
    return FakeWhitelist()


async def test_adds_and_lists_a_whitelist_entry(whitelist: FakeWhitelist) -> None:
    entries = await whitelist.all()
    assert entries == []

    entry = await whitelist.add(_KNOWN_DID_KEY, label="provider")
    assert entry.did_key == _KNOWN_DID_KEY
    assert entry.label == "provider"

    entries = await whitelist.all()
    assert len(entries) == 1
    assert entries[0].did_key == _KNOWN_DID_KEY


async def test_supports_optional_label(whitelist: FakeWhitelist) -> None:
    entry = await whitelist.add(_KNOWN_DID_KEY, label=None)
    assert entry.label is None

    entries = await whitelist.all()
    assert entries[0].label is None


async def test_deletes_a_whitelist_entry(whitelist: FakeWhitelist) -> None:
    await whitelist.add(_KNOWN_DID_KEY)
    removed = await whitelist.remove(_KNOWN_DID_KEY)
    assert removed is True

    entries = await whitelist.all()
    assert entries == []

    # Deleting a nonexistent entry returns False.
    again = await whitelist.remove(_KNOWN_DID_KEY)
    assert again is False


async def test_contains_and_find(whitelist: FakeWhitelist) -> None:
    assert await whitelist.contains(_KNOWN_DID_KEY) is False
    assert await whitelist.find(_KNOWN_DID_KEY) is None

    await whitelist.add(_KNOWN_DID_KEY, label="x")

    assert await whitelist.contains(_KNOWN_DID_KEY) is True
    found = await whitelist.find(_KNOWN_DID_KEY)
    assert found is not None
    assert found.label == "x"