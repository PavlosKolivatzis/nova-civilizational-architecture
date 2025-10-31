"""OpenAPI example coverage for federation endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.health
def test_openapi_contains_examples(client_factory):
    client = client_factory()
    schema = client.app.openapi()
    checkpoint_post = schema["paths"]["/federation/checkpoint"]["post"]
    example = checkpoint_post["requestBody"]["content"]["application/json"]["example"]
    assert example["algo"] == "sha3-256"
    assert example["version"] == "v1"
    error_example = checkpoint_post["responses"]["415"]["content"]["application/json"]["example"]
    assert error_example["code"] == "unsupported_media_type"
