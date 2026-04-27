"""Event Hub 发送器（同步 + 异步）。

支持两种认证：
1. Connection String
2. Azure AD（DefaultAzureCredential）

提供单条发送、批量发送以及上下文管理器。
"""

from __future__ import annotations

import json
from typing import Any, Iterable, List, Optional, Sequence, Union

from azure.eventhub import EventData, EventHubProducerClient
from azure.eventhub.aio import EventHubProducerClient as AsyncEventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

from .config import Settings
from .logging_utils import get_logger

logger = get_logger(__name__)

MessageLike = Union[str, bytes, dict, EventData]


def _to_event_data(message: MessageLike) -> EventData:
    if isinstance(message, EventData):
        return message
    if isinstance(message, (bytes, bytearray)):
        return EventData(bytes(message))
    if isinstance(message, str):
        return EventData(message)
    if isinstance(message, dict):
        ed = EventData(json.dumps(message, ensure_ascii=False))
        ed.properties = {"content-type": "application/json"}
        return ed
    raise TypeError(f"不支持的消息类型: {type(message)!r}")


# ============================================================
# 同步
# ============================================================
class EventHubSender:
    """同步 Event Hub 发送器。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate_event_hub()
        self._client: Optional[EventHubProducerClient] = None

    def _build_client(self) -> EventHubProducerClient:
        if self.settings.use_aad_for_event_hub:
            return EventHubProducerClient(
                fully_qualified_namespace=self.settings.event_hub_fully_qualified_namespace,
                eventhub_name=self.settings.event_hub_name,
                credential=DefaultAzureCredential(),
            )
        return EventHubProducerClient.from_connection_string(
            conn_str=self.settings.event_hub_connection_str,
            eventhub_name=self.settings.event_hub_name,
        )

    # ---------- 上下文管理 ----------
    def __enter__(self) -> "EventHubSender":
        self._client = self._build_client()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    # ---------- 发送 ----------
    def _ensure_client(self) -> EventHubProducerClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def send(
        self,
        message: MessageLike,
        partition_key: Optional[str] = None,
        partition_id: Optional[str] = None,
    ) -> None:
        """发送单条消息。"""
        client = self._ensure_client()
        batch = client.create_batch(
            partition_key=partition_key, partition_id=partition_id
        )
        batch.add(_to_event_data(message))
        client.send_batch(batch)
        logger.info("已发送 1 条消息到 Event Hub")

    def send_batch(
        self,
        messages: Iterable[MessageLike],
        partition_key: Optional[str] = None,
        partition_id: Optional[str] = None,
    ) -> int:
        """批量发送，自动按最大批大小分批。返回成功发送条数。"""
        client = self._ensure_client()
        total = 0
        batch = client.create_batch(
            partition_key=partition_key, partition_id=partition_id
        )
        for msg in messages:
            event = _to_event_data(msg)
            try:
                batch.add(event)
            except ValueError:
                # batch 已满，先发送再开新 batch
                client.send_batch(batch)
                total += len(batch)
                batch = client.create_batch(
                    partition_key=partition_key, partition_id=partition_id
                )
                batch.add(event)
        if len(batch) > 0:
            client.send_batch(batch)
            total += len(batch)
        logger.info("已批量发送 %d 条消息到 Event Hub", total)
        return total


# ============================================================
# 异步
# ============================================================
class AsyncEventHubSender:
    """异步 Event Hub 发送器。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate_event_hub()
        self._client: Optional[AsyncEventHubProducerClient] = None
        self._credential: Optional[AsyncDefaultAzureCredential] = None

    def _build_client(self) -> AsyncEventHubProducerClient:
        if self.settings.use_aad_for_event_hub:
            self._credential = AsyncDefaultAzureCredential()
            return AsyncEventHubProducerClient(
                fully_qualified_namespace=self.settings.event_hub_fully_qualified_namespace,
                eventhub_name=self.settings.event_hub_name,
                credential=self._credential,
            )
        return AsyncEventHubProducerClient.from_connection_string(
            conn_str=self.settings.event_hub_connection_str,
            eventhub_name=self.settings.event_hub_name,
        )

    async def __aenter__(self) -> "AsyncEventHubSender":
        self._client = self._build_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._credential is not None:
            await self._credential.close()
            self._credential = None

    async def _ensure_client(self) -> AsyncEventHubProducerClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def send(
        self,
        message: MessageLike,
        partition_key: Optional[str] = None,
        partition_id: Optional[str] = None,
    ) -> None:
        client = await self._ensure_client()
        batch = await client.create_batch(
            partition_key=partition_key, partition_id=partition_id
        )
        batch.add(_to_event_data(message))
        await client.send_batch(batch)
        logger.info("已异步发送 1 条消息到 Event Hub")

    async def send_batch(
        self,
        messages: Sequence[MessageLike],
        partition_key: Optional[str] = None,
        partition_id: Optional[str] = None,
    ) -> int:
        client = await self._ensure_client()
        total = 0
        batch = await client.create_batch(
            partition_key=partition_key, partition_id=partition_id
        )
        for msg in messages:
            event = _to_event_data(msg)
            try:
                batch.add(event)
            except ValueError:
                await client.send_batch(batch)
                total += len(batch)
                batch = await client.create_batch(
                    partition_key=partition_key, partition_id=partition_id
                )
                batch.add(event)
        if len(batch) > 0:
            await client.send_batch(batch)
            total += len(batch)
        logger.info("已异步批量发送 %d 条消息到 Event Hub", total)
        return total
