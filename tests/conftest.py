"""共享 fixtures。"""

import pytest

from azure_sender.config import Settings


@pytest.fixture
def eh_conn_settings() -> Settings:
    return Settings(
        event_hub_connection_str=(
            "Endpoint=sb://example.servicebus.windows.net/;"
            "SharedAccessKeyName=root;SharedAccessKey=ABCDEF=="
        ),
        event_hub_name="my-hub",
        use_aad_for_event_hub=False,
    )


@pytest.fixture
def eh_aad_settings() -> Settings:
    return Settings(
        event_hub_fully_qualified_namespace="example.servicebus.windows.net",
        event_hub_name="my-hub",
        use_aad_for_event_hub=True,
    )


@pytest.fixture
def iot_sas_settings() -> Settings:
    return Settings(
        iot_hub_hostname="myhub.azure-devices.net",
        iot_hub_device_id="device-1",
        # base64("super-secret-key")
        iot_hub_device_key="c3VwZXItc2VjcmV0LWtleQ==",
        iot_hub_sas_ttl=600,
    )


@pytest.fixture
def iot_conn_settings() -> Settings:
    return Settings(
        iot_hub_device_connection_str=(
            "HostName=myhub.azure-devices.net;DeviceId=device-1;"
            "SharedAccessKey=c3VwZXItc2VjcmV0LWtleQ=="
        )
    )
