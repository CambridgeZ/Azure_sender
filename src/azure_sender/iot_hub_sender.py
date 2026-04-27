"""IoT Hub 设备消息发送器（SAS Token 认证，同步 + 异步）。

底层使用 ``azure-iot-device``：
- 同步：``IoTHubDeviceClient``
- 异步：``azure.iot.device.aio.IoTHubDeviceClient``

支持两种构造方式：
1. 直接提供 Device Connection String
2. 显式 hostname + device_id + key，由本模块手工生成 SAS Token
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Optional, Sequence, Union

from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device.aio import IoTHubDeviceClient as AsyncIoTHubDeviceClient

from .config import Settings
from .logging_utils import get_logger
from .sas import device_uri, generate_sas_token

logger = get_logger(__name__)

MessageLike = Union[str, bytes, dict, Message]


def _to_message(message: MessageLike) -> Message:
    if isinstance(message, Message):
        return message
    if isinstance(message, (bytes, bytearray)):
        return Message(bytes(message))
    if isinstance(message, str):
        return Message(message)
    if isinstance(message, dict):
        msg = Message(json.dumps(message, ensure_ascii=False))
        msg.content_type = "application/json"
        msg.content_encoding = "utf-8"
        return msg
    raise TypeError(f"不支持的消息类型: {type(message)!r}")


def _build_sas_token(settings: Settings) -> str:
    uri = device_uri(settings.iot_hub_hostname, settings.iot_hub_device_id)
    return generate_sas_token(
        uri=uri,
        key=settings.iot_hub_device_key,
        expiry_seconds=settings.iot_hub_sas_ttl,
    )


# ============================================================
# 同步
# ============================================================
class IoTHubSender:
    """同步 IoT Hub 设备消息发送器。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate_iot_hub()
        self._client: Optional[IoTHubDeviceClient] = None

    def _build_client(self) -> IoTHubDeviceClient:
        if self.settings.iot_hub_device_connection_str:
            return IoTHubDeviceClient.create_from_connection_string(
                self.settings.iot_hub_device_connection_str
            )
        token = _build_sas_token(self.settings)
        return IoTHubDeviceClient.create_from_sastoken(token)

    def __enter__(self) -> "IoTHubSender":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        if self._client is None:
            self._client = self._build_client()
        self._client.connect()

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.shutdown()
            finally:
                self._client = None

    def send(self, message: MessageLike) -> None:
        if self._client is None:
            self.connect()
        assert self._client is not None
        self._client.send_message(_to_message(message))
        logger.info("已发送 1 条消息到 IoT Hub")

    def send_batch(self, messages: Iterable[MessageLike]) -> int:
        count = 0
        for m in messages:
            self.send(m)
            count += 1
        logger.info("已发送 %d 条消息到 IoT Hub", count)
        return count


# ============================================================
# 异步
# ============================================================
class AsyncIoTHubSender:
    """异步 IoT Hub 设备消息发送器。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate_iot_hub()
        self._client: Optional[AsyncIoTHubDeviceClient] = None

    def _build_client(self) -> AsyncIoTHubDeviceClient:
        if self.settings.iot_hub_device_connection_str:
            return AsyncIoTHubDeviceClient.create_from_connection_string(
                self.settings.iot_hub_device_connection_str
            )
        token = _build_sas_token(self.settings)
        return AsyncIoTHubDeviceClient.create_from_sastoken(token)

    async def __aenter__(self) -> "AsyncIoTHubSender":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._client is None:
            self._client = self._build_client()
        await self._client.connect()

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.shutdown()
            finally:
                self._client = None

    async def send(self, message: MessageLike) -> None:
        if self._client is None:
            await self.connect()
        assert self._client is not None
        await self._client.send_message(_to_message(message))
        logger.info("已异步发送 1 条消息到 IoT Hub")

    async def send_batch(self, messages: Sequence[MessageLike]) -> int:
        if self._client is None:
            await self.connect()
        assert self._client is not None
        count = 0
        for m in messages:
            await self._client.send_message(_to_message(m))
            count += 1
        logger.info("已异步发送 %d 条消息到 IoT Hub", count)
        return count
