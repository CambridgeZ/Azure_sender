"""配置加载：读取环境变量 / .env 文件。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


def _to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    """运行时配置。优先级：显式参数 > 环境变量 > .env 文件。"""

    # Event Hub
    event_hub_connection_str: Optional[str] = None
    event_hub_name: Optional[str] = None
    event_hub_fully_qualified_namespace: Optional[str] = None
    use_aad_for_event_hub: bool = False

    # IoT Hub (设备端)
    iot_hub_device_connection_str: Optional[str] = None
    iot_hub_hostname: Optional[str] = None
    iot_hub_device_id: Optional[str] = None
    iot_hub_device_key: Optional[str] = None
    iot_hub_sas_ttl: int = 3600

    # IoT Hub (服务端 C2D)
    iot_hub_service_connection_str: Optional[str] = None
    iot_hub_target_device_id: Optional[str] = None

    @classmethod
    def from_env(cls, dotenv_path: Optional[str] = None) -> "Settings":
        load_dotenv(dotenv_path=dotenv_path, override=False)
        return cls(
            event_hub_connection_str=os.getenv("EVENT_HUB_CONNECTION_STR"),
            event_hub_name=os.getenv("EVENT_HUB_NAME"),
            event_hub_fully_qualified_namespace=os.getenv(
                "EVENT_HUB_FULLY_QUALIFIED_NAMESPACE"
            ),
            use_aad_for_event_hub=_to_bool(os.getenv("USE_AAD_FOR_EVENT_HUB"), False),
            iot_hub_device_connection_str=os.getenv("IOT_HUB_DEVICE_CONNECTION_STR"),
            iot_hub_hostname=os.getenv("IOT_HUB_HOSTNAME"),
            iot_hub_device_id=os.getenv("IOT_HUB_DEVICE_ID"),
            iot_hub_device_key=os.getenv("IOT_HUB_DEVICE_KEY"),
            iot_hub_sas_ttl=int(os.getenv("IOT_HUB_SAS_TTL", "3600")),
            iot_hub_service_connection_str=os.getenv("IOT_HUB_SERVICE_CONNECTION_STR"),
            iot_hub_target_device_id=os.getenv("IOT_HUB_TARGET_DEVICE_ID"),
        )

    # ---------- 校验 ----------
    def validate_event_hub(self) -> None:
        if self.use_aad_for_event_hub:
            if not self.event_hub_fully_qualified_namespace or not self.event_hub_name:
                raise ValueError(
                    "使用 AAD 时必须设置 EVENT_HUB_FULLY_QUALIFIED_NAMESPACE 和 EVENT_HUB_NAME"
                )
        else:
            if not self.event_hub_connection_str:
                raise ValueError("必须设置 EVENT_HUB_CONNECTION_STR 或启用 AAD")
            # 当连接字符串中已包含 EntityPath 时，event_hub_name 可省略
            if "EntityPath=" not in self.event_hub_connection_str and not self.event_hub_name:
                raise ValueError(
                    "连接字符串不含 EntityPath 时必须设置 EVENT_HUB_NAME"
                )

    def validate_iot_hub(self) -> None:
        if self.iot_hub_device_connection_str:
            return
        missing = [
            k
            for k, v in {
                "IOT_HUB_HOSTNAME": self.iot_hub_hostname,
                "IOT_HUB_DEVICE_ID": self.iot_hub_device_id,
                "IOT_HUB_DEVICE_KEY": self.iot_hub_device_key,
            }.items()
            if not v
        ]
        if missing:
            raise ValueError(
                "IoT Hub 配置不完整，缺少: " + ", ".join(missing)
            )

    def validate_iot_hub_service(self) -> None:
        if not self.iot_hub_service_connection_str:
            raise ValueError("必须设置 IOT_HUB_SERVICE_CONNECTION_STR")
        if not self.iot_hub_target_device_id:
            raise ValueError("必须设置 IOT_HUB_TARGET_DEVICE_ID（目标设备 ID）")
