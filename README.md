# azure-sender

向 **Azure Event Hub** 与 **Azure IoT Hub** 发送数据的 Python 项目，支持：

- ✅ Event Hub：Connection String 与 Azure AD（`DefaultAzureCredential`）两种认证
- ✅ IoT Hub：Device Connection String 或 SAS Token（库内置生成）
- ✅ 同步 + 异步（`asyncio`）API
- ✅ 单条与批量发送（Event Hub 自动按最大批大小分批）
- ✅ CLI 命令行工具 `azure-sender`
- ✅ pytest 单元测试

## 目录结构

```
azure-sender/
├─ pyproject.toml
├─ .env.example
├─ src/azure_sender/
│  ├─ __init__.py
│  ├─ config.py            # 环境配置与校验
│  ├─ event_hub_sender.py  # EventHubSender / AsyncEventHubSender
│  ├─ iot_hub_sender.py    # IoTHubSender / AsyncIoTHubSender
│  ├─ sas.py               # IoT Hub SAS Token 生成
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

## 安装

推荐使用虚拟环境：

```bash
cd /Users/mac/azure-sender
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 配置

复制示例文件并填入你的真实值：

```bash
cp .env.example .env
```

主要变量：

| 变量 | 说明 |
| ---- | ---- |
| `EVENT_HUB_CONNECTION_STR` | Event Hub 命名空间或实体连接字符串 |
| `EVENT_HUB_NAME` | Event Hub 名称（连接串无 `EntityPath` 时必填） |
| `EVENT_HUB_FULLY_QUALIFIED_NAMESPACE` | `<namespace>.servicebus.windows.net`，AAD 方式必填 |
| `USE_AAD_FOR_EVENT_HUB` | `true` 时使用 `DefaultAzureCredential` |
| `IOT_HUB_DEVICE_CONNECTION_STR` | 设备连接字符串（推荐） |
| `IOT_HUB_HOSTNAME` / `IOT_HUB_DEVICE_ID` / `IOT_HUB_DEVICE_KEY` | 显式 SAS 模式三件套 |
| `IOT_HUB_SAS_TTL` | SAS Token 有效期（秒），默认 3600 |

> 使用 AAD 时，请先 `az login`，并确保账户对 Event Hub 拥有 **Azure Event Hubs Data Sender** 角色。

## CLI 用法

```bash
# Event Hub —— 单条
azure-sender eventhub send '{"temperature": 22.5}' --partition-key sensor-1

# Event Hub —— 批量（每行一条消息）
azure-sender eventhub send-file ./messages.jsonl --asyncio

# IoT Hub —— 单条
azure-sender iothub send '{"temperature": 22.5}'

# IoT Hub —— 批量
azure-sender iothub send-file ./messages.jsonl --asyncio
```

如需自定义 `.env` 路径：

```bash
azure-sender --env-file ./prod.env eventhub send "ping"
```

## 编程接口

### Event Hub（同步）

```python
from azure_sender import EventHubSender

with EventHubSender() as sender:
    sender.send({"temperature": 22.5}, partition_key="sensor-1")
    sender.send_batch([{"i": i} for i in range(1000)])
```

### Event Hub（异步）

```python
import asyncio
from azure_sender import AsyncEventHubSender

async def main():
    async with AsyncEventHubSender() as sender:
        await sender.send_batch([f"msg-{i}" for i in range(100)])

asyncio.run(main())
```

### IoT Hub（同步）

```python
from azure_sender import IoTHubSender

with IoTHubSender() as sender:
    sender.send({"temperature": 22.5})
```

### IoT Hub（异步）

```python
import asyncio
from azure_sender import AsyncIoTHubSender

async def main():
    async with AsyncIoTHubSender() as sender:
        for i in range(10):
            await sender.send({"i": i})

asyncio.run(main())
```

## 测试

```bash
pytest -v
```

单元测试通过 mock 替换 Azure 客户端，**无需真实凭据**即可运行。

## 常见问题

- **`ValueError: 必须设置 EVENT_HUB_CONNECTION_STR 或启用 AAD`**：检查 `.env` 是否被加载、变量是否正确。
- **AAD 认证失败**：确认已 `az login` 且账户角色为 *Azure Event Hubs Data Sender*。
- **IoT Hub 连接断开**：SAS Token 过期，重新创建 sender 或调大 `IOT_HUB_SAS_TTL`。
- **Event Hub 单条消息超过 batch 上限**：`send_batch` 会按上限自动分批；若单条消息本身超限会抛 `ValueError`，需拆分业务数据。

## License

MIT
