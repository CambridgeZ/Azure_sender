import json

import pytest
from azure.eventhub import EventData

from azure_sender.event_hub_sender import EventHubSender, _to_event_data


# ---------- _to_event_data ----------
def test_to_event_data_str() -> None:
    ed = _to_event_data("hello")
    assert isinstance(ed, EventData)
    assert ed.body_as_str() == "hello"


def test_to_event_data_bytes() -> None:
    ed = _to_event_data(b"\x01\x02")
    assert isinstance(ed, EventData)


def test_to_event_data_dict() -> None:
    ed = _to_event_data({"a": 1, "b": "中"})
    assert isinstance(ed, EventData)
    assert json.loads(ed.body_as_str()) == {"a": 1, "b": "中"}
    assert ed.properties.get("content-type") == "application/json"


def test_to_event_data_passthrough() -> None:
    src = EventData("x")
    assert _to_event_data(src) is src


def test_to_event_data_invalid_type() -> None:
    with pytest.raises(TypeError):
        _to_event_data(12345)  # type: ignore[arg-type]


# ---------- EventHubSender 行为 ----------
class _FakeBatch:
    def __init__(self, max_size: int = 2) -> None:
        self._items: list = []
        self._max = max_size

    def add(self, event) -> None:
        if len(self._items) >= self._max:
            raise ValueError("full")
        self._items.append(event)

    def __len__(self) -> int:
        return len(self._items)


class _FakeProducer:
    def __init__(self, batch_size: int = 2) -> None:
        self.sent_batches: list[_FakeBatch] = []
        self.closed = False
        self._batch_size = batch_size

    def create_batch(self, partition_key=None, partition_id=None) -> _FakeBatch:
        return _FakeBatch(self._batch_size)

    def send_batch(self, batch: _FakeBatch) -> None:
        self.sent_batches.append(batch)

    def close(self) -> None:
        self.closed = True


def test_send_single(monkeypatch, eh_conn_settings) -> None:
    fake = _FakeProducer()
    sender = EventHubSender(eh_conn_settings)
    monkeypatch.setattr(sender, "_build_client", lambda: fake)

    with sender as s:
        s.send({"hello": "world"})

    assert len(fake.sent_batches) == 1
    assert len(fake.sent_batches[0]) == 1
    assert fake.closed is True


def test_send_batch_splits_when_full(monkeypatch, eh_conn_settings) -> None:
    fake = _FakeProducer(batch_size=2)
    sender = EventHubSender(eh_conn_settings)
    monkeypatch.setattr(sender, "_build_client", lambda: fake)

    with sender as s:
        sent = s.send_batch([f"m{i}" for i in range(5)])

    assert sent == 5
    # 5 条 / 每批 2 条 -> 3 个 batch (2,2,1)
    assert [len(b) for b in fake.sent_batches] == [2, 2, 1]
