# azure-sender

[中文版 README](README.zh-CN.md)

A Python project for sending data to **Azure Event Hub** and **Azure IoT Hub**, featuring:

- ✅ Event Hub: authentication via Connection String or Azure AD (`DefaultAzureCredential`)
- ✅ IoT Hub: Device Connection String or SAS Token (built-in generation)
- ✅ Synchronous and asynchronous (`asyncio`) APIs
- ✅ Single-message and batch sending (Event Hub auto-splits batches by max size)
- ✅ `azure-sender` command-line tool
- ✅ pytest unit tests

## Project Structure

```
azure-sender/
├─ pyproject.toml
├─ .env.example
├─ src/azure_sender/
│  ├─ __init__.py
│  ├─ config.py            # Environment configuration & validation
│  ├─ event_hub_sender.py  # EventHubSender / AsyncEventHubSender
│  ├─ iot_hub_sender.py    # IoTHubSender / AsyncIoTHubSender
│  ├─ sas.py               # IoT Hub SAS Token generation
│  ├─ logging_utils.py
│  └─ cli.py               # azure-sender CLI
├─ examples/
│  ├─ send_event_hub.py
│  ├─ send_iot_hub.py
│  └─ send_async.py
└─ tests/
   ├─ test_config.py
   ├─ test_sas.py
   ├─ test_event_hub_sender.py
   └─ test_iot_hub_sender.py
```

## Installation

A virtual environment is recommended:

```bash
cd /Users/mac/azure-sender
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Copy the example file and fill in your real values:

```bash
cp .env.example .env
```

Main variables:

| Variable | Description |
| -------- | ----------- |
| `EVENT_HUB_CONNECTION_STR` | Event Hub namespace or entity connection string |
| `EVENT_HUB_NAME` | Event Hub name (required when the connection string has no `EntityPath`) |
| `EVENT_HUB_FULLY_QUALIFIED_NAMESPACE` | `<namespace>.servicebus.windows.net`, required for AAD |
| `USE_AAD_FOR_EVENT_HUB` | Set to `true` to use `DefaultAzureCredential` |
| `IOT_HUB_DEVICE_CONNECTION_STR` | Device connection string (recommended) |
| `IOT_HUB_HOSTNAME` / `IOT_HUB_DEVICE_ID` / `IOT_HUB_DEVICE_KEY` | Trio for explicit SAS mode |
| `IOT_HUB_SAS_TTL` | SAS token TTL in seconds, default `3600` |
| `IOT_HUB_SERVICE_CONNECTION_STR` | IoT Hub service-level connection string (with `SharedAccessKeyName`); required for C2D |
| `IOT_HUB_TARGET_DEVICE_ID` | Target device ID for C2D messages |

> When using AAD, run `az login` first and ensure your account has the **Azure Event Hubs Data Sender** role on the Event Hub.

## CLI Usage

```bash
# Event Hub — single message
azure-sender eventhub send '{"temperature": 22.5}' --partition-key sensor-1

# Event Hub — batch (one message per line)
azure-sender eventhub send-file ./messages.jsonl --asyncio

# IoT Hub (device side) — single message
azure-sender iothub send '{"temperature": 22.5}'

# IoT Hub (device side) — batch
azure-sender iothub send-file ./messages.jsonl --asyncio

# IoT Hub (service side, C2D) — single message
azure-sender iothub service-send '{"temperature": 22.5}'

# IoT Hub (service side, C2D) — explicit target device
azure-sender iothub service-send '{"temperature": 22.5}' --device-id my-device-1

# IoT Hub (service side, C2D) — batch
azure-sender iothub service-send-file ./messages.jsonl
```

To use a custom `.env` path:

```bash
azure-sender --env-file ./prod.env eventhub send "ping"
```

## Programming Interface

### Event Hub (sync)

```python
from azure_sender import EventHubSender

with EventHubSender() as sender:
    sender.send({"temperature": 22.5}, partition_key="sensor-1")
    sender.send_batch([{"i": i} for i in range(1000)])
```

### Event Hub (async)

```python
import asyncio
from azure_sender import AsyncEventHubSender

async def main():
    async with AsyncEventHubSender() as sender:
        await sender.send_batch([f"msg-{i}" for i in range(100)])

asyncio.run(main())
```

### IoT Hub (device, sync)

```python
from azure_sender import IoTHubSender

with IoTHubSender() as sender:
    sender.send({"temperature": 22.5})
```

### IoT Hub (device, async)

```python
import asyncio
from azure_sender import AsyncIoTHubSender

async def main():
    async with AsyncIoTHubSender() as sender:
        for i in range(10):
            await sender.send({"i": i})

asyncio.run(main())
```

### IoT Hub (service, C2D)

```python
from azure_sender import IoTHubServiceSender

with IoTHubServiceSender() as sender:
    sender.send({"temperature": 22.5})
    sender.send_batch([{"i": i} for i in range(10)])
```

You can also specify the target device ID at construction time (overriding `.env`):

```python
with IoTHubServiceSender(device_id="my-device-1") as sender:
    sender.send("hello from cloud")
```

## Testing

```bash
pytest -v
```

Unit tests mock out the Azure clients, so **no real credentials** are required to run them.

## FAQ

- **`ValueError: EVENT_HUB_CONNECTION_STR must be set or AAD must be enabled`**: check that `.env` is loaded and the variables are correct.
- **AAD authentication fails**: ensure you have run `az login` and your account holds the *Azure Event Hubs Data Sender* role.
- **IoT Hub connection drops**: the SAS token has expired — recreate the sender or increase `IOT_HUB_SAS_TTL`.
- **Single Event Hub message exceeds the batch limit**: `send_batch` automatically splits batches by the limit; a single oversized message will raise `ValueError` and must be split at the application level.

## License

MIT
