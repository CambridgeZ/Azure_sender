"""SAS Token 生成工具（用于 Azure IoT Hub 设备认证）。

参考: https://learn.microsoft.com/azure/iot-hub/iot-hub-dev-guide-sas
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from urllib.parse import quote_plus


def generate_sas_token(
    uri: str,
    key: str,
    policy_name: str | None = None,
    expiry_seconds: int = 3600,
) -> str:
    """为给定 URI 生成 SAS Token。

    Args:
        uri: 资源 URI，例如 ``<hub>.azure-devices.net/devices/<deviceId>``。
        key: Base64 编码的对称密钥。
        policy_name: 共享访问策略名（设备级 SAS 通常不需要）。
        expiry_seconds: 有效期（秒）。
    """
    if not uri:
        raise ValueError("uri 不能为空")
    if not key:
        raise ValueError("key 不能为空")

    expiry = int(time.time() + expiry_seconds)
    encoded_uri = quote_plus(uri)
    string_to_sign = f"{encoded_uri}\n{expiry}".encode("utf-8")

    try:
        decoded_key = base64.b64decode(key)
    except Exception as exc:  # pragma: no cover - 非法密钥时直接抛错
        raise ValueError("IoT Hub 设备密钥必须是有效的 Base64 字符串") from exc

    signature = base64.b64encode(
        hmac.new(decoded_key, string_to_sign, hashlib.sha256).digest()
    )
    encoded_sig = quote_plus(signature)

    token = f"SharedAccessSignature sr={encoded_uri}&sig={encoded_sig}&se={expiry}"
    if policy_name:
        token += f"&skn={policy_name}"
    return token


def device_uri(hostname: str, device_id: str) -> str:
    return f"{hostname}/devices/{device_id}"
