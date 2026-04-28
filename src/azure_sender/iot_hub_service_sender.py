"""IoT Hub 服务端消息发送器（C2D，使用服务连接字符串）。

底层使用 ``azure-iot-hub`` 的 ``IoTHubRegistryManager``，
通过服务级连接字符串向指定设备发送 Cloud-to-Device 消息。
"""

from __future__ import annotations

import json
from typing import Iterable, Optional, Union

from azure.iot.hub import IoTHubRegistryManager

from .config import Settings
from .logging_utils import get_logger

logger = get_logger(__name__)

MessageLike = Union[str, bytes, dict]


def _to_payload(message: MessageLike) -> str:
    if isinstance(message, dict):
        return json.dumps(message, ensure_ascii=False)
    if isinstance(message, (bytes, bytearray)):
        return message.decode("utf-8")
    if isinstance(message, str):
        return message
    raise TypeError(f"不支持的消息类型: {type(message)!r}")


class IoTHubServiceSender:
    """通过服务连接字符串向设备发送 C2D 消息。"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        device_id: Optional[str] = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate_iot_hub_service()
        self._device_id = device_id or self.settings.iot_hub_target_device_id
        self._client: Optional[IoTHubRegistryManager] = None

    def _build_client(self) -> IoTHubRegistryManager:
        return IoTHubRegistryManager(self.settings.iot_hub_service_connection_str)

    def __enter__(self) -> "IoTHubServiceSender":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        if self._client is None:
            self._client = self._build_client()

    def close(self) -> None:
        self._client = None

    def send(self, message: MessageLike) -> None:
        if self._client is None:
            self.connect()
        assert self._client is not None
        payload = _to_payload(message)
        self._client.send_c2d_message(self._device_id, payload)
        logger.info("已发送 1 条 C2D 消息到设备 %s", self._device_id)

    def send_batch(self, messages: Iterable[MessageLike]) -> int:
        count = 0
        for m in messages:
            self.send(m)
            count += 1
        logger.info("已发送 %d 条 C2D 消息到设备 %s", count, self._device_id)
        return count
