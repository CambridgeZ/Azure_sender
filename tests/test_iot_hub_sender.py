import json

import pytest
from azure.iot.device import Message

from azure_sender.iot_hub_sender import IoTHubSender, _to_message


def test_to_message_str() -> None:
    m = _to_message("hi")
    assert isinstance(m, Message)
    assert str(m.data) in ("hi", "b'hi'") or m.data == "hi" or m.data == b"hi"


def test_to_message_dict_sets_content_type() -> None:
    m = _to_message({"a": 1})
    assert m.content_type == "application/json"
    assert m.content_encoding == "utf-8"
    payload = m.data.decode("utf-8") if isinstance(m.data, (bytes, bytearray)) else m.data
    assert json.loads(payload) == {"a": 1}


def test_to_message_passthrough() -> None:
    src = Message("x")
    assert _to_message(src) is src


def test_to_message_invalid() -> None:
    with pytest.raises(TypeError):
        _to_message(3.14)  # type: ignore[arg-type]


# ---------- 发送行为 ----------
class _FakeDeviceClient:
    def __init__(self) -> None:
        self.connected = False
        self.shutdown_called = False
        self.sent: list[Message] = []

    def connect(self) -> None:
        self.connected = True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def send_message(self, m: Message) -> None:
        self.sent.append(m)


def test_send_and_batch(monkeypatch, iot_conn_settings) -> None:
    fake = _FakeDeviceClient()
    sender = IoTHubSender(iot_conn_settings)
    monkeypatch.setattr(sender, "_build_client", lambda: fake)

    with sender as s:
        s.send("a")
        s.send_batch(["b", {"c": 1}])

    assert fake.connected is True
    assert fake.shutdown_called is True
    assert len(fake.sent) == 3


def test_sas_path_builds_token(monkeypatch, iot_sas_settings) -> None:
    """当未提供连接字符串时，应走 SAS Token 创建路径。"""
    captured = {}

    class _Stub:
        @staticmethod
        def create_from_sastoken(token: str) -> _FakeDeviceClient:
            captured["token"] = token
            return _FakeDeviceClient()

        @staticmethod
        def create_from_connection_string(_: str) -> _FakeDeviceClient:  # pragma: no cover
            raise AssertionError("不应该被调用")

    monkeypatch.setattr(
        "azure_sender.iot_hub_sender.IoTHubDeviceClient", _Stub
    )
    sender = IoTHubSender(iot_sas_settings)
    client = sender._build_client()
    assert isinstance(client, _FakeDeviceClient)
    assert captured["token"].startswith("SharedAccessSignature ")
