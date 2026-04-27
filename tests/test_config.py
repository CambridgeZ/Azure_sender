import pytest

from azure_sender.config import Settings


def test_validate_event_hub_conn_str_ok(eh_conn_settings: Settings) -> None:
    eh_conn_settings.validate_event_hub()  # should not raise


def test_validate_event_hub_aad_ok(eh_aad_settings: Settings) -> None:
    eh_aad_settings.validate_event_hub()


def test_validate_event_hub_missing_all() -> None:
    with pytest.raises(ValueError):
        Settings().validate_event_hub()


def test_validate_event_hub_aad_missing_namespace() -> None:
    with pytest.raises(ValueError):
        Settings(use_aad_for_event_hub=True, event_hub_name="x").validate_event_hub()


def test_validate_event_hub_conn_without_entitypath_requires_name() -> None:
    s = Settings(
        event_hub_connection_str=(
            "Endpoint=sb://example.servicebus.windows.net/;"
            "SharedAccessKeyName=root;SharedAccessKey=ABC=="
        )
    )
    with pytest.raises(ValueError):
        s.validate_event_hub()


def test_validate_event_hub_conn_with_entitypath_ok() -> None:
    s = Settings(
        event_hub_connection_str=(
            "Endpoint=sb://example.servicebus.windows.net/;"
            "SharedAccessKeyName=root;SharedAccessKey=ABC==;EntityPath=my-hub"
        )
    )
    s.validate_event_hub()


def test_validate_iot_hub_with_conn_str(iot_conn_settings: Settings) -> None:
    iot_conn_settings.validate_iot_hub()


def test_validate_iot_hub_with_sas_settings(iot_sas_settings: Settings) -> None:
    iot_sas_settings.validate_iot_hub()


def test_validate_iot_hub_missing_fields() -> None:
    with pytest.raises(ValueError) as ei:
        Settings(iot_hub_hostname="h").validate_iot_hub()
    assert "IOT_HUB_DEVICE_ID" in str(ei.value)
    assert "IOT_HUB_DEVICE_KEY" in str(ei.value)
