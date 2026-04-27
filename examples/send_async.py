"""异步示例：并发地向 Event Hub 与 IoT Hub 发送数据。"""

import asyncio

from azure_sender import AsyncEventHubSender, AsyncIoTHubSender


async def push_event_hub() -> None:
    async with AsyncEventHubSender() as s:
        await s.send_batch(
            [{"i": i, "src": "eh"} for i in range(100)],
            partition_key="demo",
        )


async def push_iot_hub() -> None:
    async with AsyncIoTHubSender() as s:
        for i in range(10):
            await s.send({"i": i, "src": "iot"})


async def main() -> None:
    await asyncio.gather(push_event_hub(), push_iot_hub())


if __name__ == "__main__":
    asyncio.run(main())
