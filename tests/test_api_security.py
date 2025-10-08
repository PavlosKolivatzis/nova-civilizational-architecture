
import pytest
from fastapi import HTTPException

import api.security as security


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("NOVA_API_KEY", raising=False)
    monkeypatch.delenv("NOVA_REQUIRE_SECURITY", raising=False)
    yield


def test_get_api_key_missing_env(monkeypatch):
    with pytest.raises(RuntimeError, match="NOVA_API_KEY not set"):
        security.get_api_key()


def test_get_api_key_rejects_default(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "default")

    with pytest.raises(RuntimeError, match="default value"):
        security.get_api_key()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "S3cure-Key-Value")

    assert security.get_api_key() == "S3cure-Key-Value"


@pytest.mark.asyncio
async def test_verify_api_key_success(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "good-key")

    assert await security.verify_api_key("good-key") == "good-key"


@pytest.mark.asyncio
async def test_verify_api_key_missing_header(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "good-key")

    with pytest.raises(HTTPException) as exc:
        await security.verify_api_key(None)

    err = exc.value
    assert err.status_code == 401
    assert err.detail == "Missing NOVA-API-KEY header"


@pytest.mark.asyncio
async def test_verify_api_key_invalid(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "expected")

    with pytest.raises(HTTPException) as exc:
        await security.verify_api_key("wrong")

    err = exc.value
    assert err.status_code == 403
    assert err.detail == "Invalid API key"


@pytest.mark.asyncio
async def test_verify_api_key_missing_env(monkeypatch):
    with pytest.raises(RuntimeError, match="NOVA_API_KEY not set"):
        await security.verify_api_key("anything")


def test_validate_startup_security_success(monkeypatch, capsys):
    secure_key = "x" * 32
    monkeypatch.setenv("NOVA_API_KEY", secure_key)

    assert security.validate_startup_security() is True

    captured = capsys.readouterr().out
    assert "Security: API key configured" in captured
    assert "32 chars" in captured


def test_validate_startup_security_short_key(monkeypatch):
    monkeypatch.setenv("NOVA_API_KEY", "short")

    with pytest.raises(RuntimeError, match="too short"):
        security.validate_startup_security()


def test_validate_startup_security_missing_but_optional(monkeypatch, capsys):
    monkeypatch.setenv("NOVA_REQUIRE_SECURITY", "false")

    assert security.validate_startup_security() is False

    output = capsys.readouterr().out
    assert "Security warning" in output


def test_validate_startup_security_missing_required(monkeypatch):
    monkeypatch.setenv("NOVA_REQUIRE_SECURITY", "1")

    with pytest.raises(RuntimeError, match="NOVA_API_KEY not set"):
        security.validate_startup_security()
