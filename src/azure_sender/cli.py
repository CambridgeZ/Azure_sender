"""命令行入口：azure-sender。

用法:
    azure-sender eventhub send "hello"
    azure-sender eventhub send-file ./messages.jsonl
    azure-sender iothub send '{"temp": 23.5}'
    azure-sender iothub send-file ./messages.jsonl --count 100
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Iterator, List, Optional

import click

from .config import Settings
from .event_hub_sender import AsyncEventHubSender, EventHubSender
from .iot_hub_sender import AsyncIoTHubSender, IoTHubSender
from .iot_hub_service_sender import IoTHubServiceSender
from .logging_utils import get_logger

logger = get_logger("azure_sender.cli")


def _read_messages(path: Path) -> Iterator[str]:
    """逐行读取消息文件，每行一条；空行被忽略。"""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.strip():
                yield line


def _parse_payload(payload: str) -> object:
    """如果是 JSON 则解析为对象，否则原样返回字符串。"""
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


# ============================================================
@click.group()
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="自定义 .env 文件路径",
)
@click.pass_context
def cli(ctx: click.Context, env_file: Optional[Path]) -> None:
    """向 Azure Event Hub / IoT Hub 发送数据。"""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = Settings.from_env(
        dotenv_path=str(env_file) if env_file else None
    )


# ============================================================
# Event Hub
# ============================================================
@cli.group("eventhub")
def eventhub_group() -> None:
    """Event Hub 相关命令。"""


@eventhub_group.command("send")
@click.argument("payload")
@click.option("--partition-key", default=None, help="分区键")
@click.option("--asyncio", "use_async", is_flag=True, help="使用异步客户端")
@click.pass_context
def eventhub_send(
    ctx: click.Context, payload: str, partition_key: Optional[str], use_async: bool
) -> None:
    """发送单条消息。PAYLOAD 可以是字符串或 JSON。"""
    settings: Settings = ctx.obj["settings"]
    msg = _parse_payload(payload)

    if use_async:

        async def _run() -> None:
            async with AsyncEventHubSender(settings) as s:
                await s.send(msg, partition_key=partition_key)

        asyncio.run(_run())
    else:
        with EventHubSender(settings) as s:
            s.send(msg, partition_key=partition_key)
    click.echo("OK")


@eventhub_group.command("send-file")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--partition-key", default=None, help="分区键")
@click.option("--asyncio", "use_async", is_flag=True, help="使用异步客户端")
@click.pass_context
def eventhub_send_file(
    ctx: click.Context, file: Path, partition_key: Optional[str], use_async: bool
) -> None:
    """从文件批量发送（每行一条消息）。"""
    settings: Settings = ctx.obj["settings"]
    messages: List[object] = [_parse_payload(line) for line in _read_messages(file)]
    if not messages:
        click.echo("文件为空，无需发送", err=True)
        sys.exit(1)

    if use_async:

        async def _run() -> int:
            async with AsyncEventHubSender(settings) as s:
                return await s.send_batch(messages, partition_key=partition_key)

        sent = asyncio.run(_run())
    else:
        with EventHubSender(settings) as s:
            sent = s.send_batch(messages, partition_key=partition_key)
    click.echo(f"已发送 {sent} 条消息")


# ============================================================
# IoT Hub
# ============================================================
@cli.group("iothub")
def iothub_group() -> None:
    """IoT Hub 相关命令。"""


@iothub_group.command("send")
@click.argument("payload")
@click.option("--asyncio", "use_async", is_flag=True, help="使用异步客户端")
@click.pass_context
def iothub_send(ctx: click.Context, payload: str, use_async: bool) -> None:
    """发送单条设备消息。PAYLOAD 可以是字符串或 JSON。"""
    settings: Settings = ctx.obj["settings"]
    msg = _parse_payload(payload)

    if use_async:

        async def _run() -> None:
            async with AsyncIoTHubSender(settings) as s:
                await s.send(msg)

        asyncio.run(_run())
    else:
        with IoTHubSender(settings) as s:
            s.send(msg)
    click.echo("OK")


@iothub_group.command("send-file")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--asyncio", "use_async", is_flag=True, help="使用异步客户端")
@click.pass_context
def iothub_send_file(ctx: click.Context, file: Path, use_async: bool) -> None:
    """从文件批量发送设备消息（每行一条）。"""
    settings: Settings = ctx.obj["settings"]
    messages: List[object] = [_parse_payload(line) for line in _read_messages(file)]
    if not messages:
        click.echo("文件为空，无需发送", err=True)
        sys.exit(1)

    if use_async:

        async def _run() -> int:
            async with AsyncIoTHubSender(settings) as s:
                return await s.send_batch(messages)

        sent = asyncio.run(_run())
    else:
        with IoTHubSender(settings) as s:
            sent = s.send_batch(messages)
    click.echo(f"已发送 {sent} 条消息")


@iothub_group.command("service-send")
@click.argument("payload")
@click.option("--device-id", default=None, help="目标设备 ID（覆盖 .env 中的 IOT_HUB_TARGET_DEVICE_ID）")
@click.pass_context
def iothub_service_send(ctx: click.Context, payload: str, device_id: Optional[str]) -> None:
    """通过服务连接字符串发送 C2D 消息。PAYLOAD 可以是字符串或 JSON。"""
    settings: Settings = ctx.obj["settings"]
    if device_id:
        settings.iot_hub_target_device_id = device_id
    msg = _parse_payload(payload)
    with IoTHubServiceSender(settings) as s:
        s.send(msg)
    click.echo("OK")


@iothub_group.command("service-send-file")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--device-id", default=None, help="目标设备 ID")
@click.pass_context
def iothub_service_send_file(ctx: click.Context, file: Path, device_id: Optional[str]) -> None:
    """通过服务连接字符串批量发送 C2D 消息（每行一条）。"""
    settings: Settings = ctx.obj["settings"]
    if device_id:
        settings.iot_hub_target_device_id = device_id
    messages: List[object] = [_parse_payload(line) for line in _read_messages(file)]
    if not messages:
        click.echo("文件为空，无需发送", err=True)
        sys.exit(1)
    with IoTHubServiceSender(settings) as s:
        sent = s.send_batch(messages)
    click.echo(f"已发送 {sent} 条消息")


if __name__ == "__main__":  # pragma: no cover
    cli()
