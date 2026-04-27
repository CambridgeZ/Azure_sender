"""同步发送示例：向 IoT Hub 发送设备消息。"""

from azure_sender import IoTHubSender


def main() -> None:
    payloads = [
        {"temperature": 22.5, "humidity": 60},
        {"temperature": 22.6, "humidity": 61},
    ]
    with IoTHubSender() as sender:
        sender.send_batch(payloads)


if __name__ == "__main__":
    main()
