import time

import pytest

from azure_sender.sas import device_uri, generate_sas_token


def test_device_uri() -> None:
    assert device_uri("h.azure-devices.net", "dev-1") == "h.azure-devices.net/devices/dev-1"


def test_generate_sas_token_structure() -> None:
    token = generate_sas_token(
        uri="h.azure-devices.net/devices/dev-1",
        key="c3VwZXItc2VjcmV0LWtleQ==",
        expiry_seconds=60,
    )
    assert token.startswith("SharedAccessSignature ")
    # 必含字段
    for part in ("sr=", "sig=", "se="):
        assert part in token


def test_generate_sas_token_with_policy_name() -> None:
    token = generate_sas_token(
        uri="h.azure-devices.net/devices/dev-1",
        key="c3VwZXItc2VjcmV0LWtleQ==",
        policy_name="iothubowner",
        expiry_seconds=60,
    )
    assert "skn=iothubowner" in token


def test_generate_sas_token_expiry_is_in_future() -> None:
    before = int(time.time())
    token = generate_sas_token(
        uri="h.azure-devices.net/devices/dev-1",
        key="c3VwZXItc2VjcmV0LWtleQ==",
        expiry_seconds=120,
    )
    se = int(token.split("se=")[1].split("&")[0])
    assert se >= before + 100


def test_generate_sas_token_invalid_key() -> None:
    with pytest.raises(ValueError):
        generate_sas_token(uri="x/y", key="not_base64!!!")


def test_generate_sas_token_empty_uri() -> None:
    with pytest.raises(ValueError):
        generate_sas_token(uri="", key="c3VwZXItc2VjcmV0LWtleQ==")
