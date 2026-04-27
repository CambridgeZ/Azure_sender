"""同步发送示例：向 Event Hub 发送一批消息。"""

from azure_sender import EventHubSender


def main() -> None:
    messages = [
        {"device": "sensor-1", "temperature": 22.5, "humidity": 60},
        {"device": "sensor-1", "temperature": 22.7, "humidity": 61},
        "纯文本消息",
        b"\x01\x02\x03 binary",
    ]
    with EventHubSender() as sender:
        sent = sender.send_batch(messages, partition_key="sensor-1")
        print(f"已发送 {sent} 条")


if __name__ == "__main__":
    main()
