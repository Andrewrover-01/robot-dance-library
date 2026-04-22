# coding=UTF-8
"""YanAPI HTTP 封装模块。

该模块基于题述提供的 API 结构进行整理，统一封装机器人常用控制能力：
- 设备信息
- 媒体控制
- 动作控制
- 舵机控制
- 传感器读取
- 视觉与语音能力
- 同步等待辅助方法
"""

from __future__ import annotations

import asyncio
import json
import time
from enum import Enum, unique
from multiprocessing import Process
from socket import AF_INET, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET, socket
from typing import Dict, List, Optional

import requests

try:
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    nest_asyncio = None

try:
    import cv2  # noqa: F401
except ImportError:
    cv2 = None


# --- 全局配置与基础请求 ---
basic_url = "http://127.0.0.1:9090/v1/"
ip = "127.0.0.1"
headers = {"Content-Type": "application/json"}


def yan_api_init(robot_ip: str) -> None:
    """初始化 YanAPI 基础地址。"""

    global basic_url, ip
    basic_url, ip = f"http://{robot_ip}:9090/v1/", robot_ip


def init(robot_ip: str) -> None:
    """兼容入口：与外部调用约定保持一致。"""

    yan_api_init(robot_ip)


def _req(method: str, path: str, data=None, params=None, is_json: bool = True):
    """发送 HTTP 请求并返回统一结果。"""

    url = basic_url + path
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "PUT":
            response = requests.put(
                url,
                data=json.dumps(data) if data is not None else None,
                headers=headers,
                timeout=10,
            )
        elif method == "POST":
            response = requests.post(
                url,
                data=json.dumps(data) if data is not None else None,
                headers=headers,
                timeout=10,
            )
        elif method == "DELETE":
            response = requests.delete(
                url,
                data=json.dumps(data) if data is not None else None,
                headers=headers,
                timeout=10,
            )
        else:
            return {"code": -1, "msg": f"Unsupported method: {method}"}

        return (
            json.loads(response.content.decode("utf-8"))
            if is_json
            else response.content
        )
    except Exception as exc:  # noqa: BLE001
        return {"code": -1, "msg": str(exc)}


def __resIsSuccess(res) -> bool:
    return isinstance(res, dict) and res.get("code") == 0


# --- 1. 设备基础信息 (Devices) ---
def get_robot_battery_info():
    return _req("GET", "devices/battery")


def get_robot_fall_management_state():
    return _req("GET", "devices/fall_management")


def set_robot_fall_management_state(enable: bool):
    return _req("PUT", "devices/fall_management", {"enable": enable})


def set_robot_language(lang: str):
    return _req("PUT", "devices/languages", {"language": lang})


def get_robot_volume():
    return _req("GET", "devices/volume")


def set_robot_volume(v: int):
    return _req("PUT", "devices/volume", {"volume": v})


def get_robot_led():
    return _req("GET", "devices/led")


def set_robot_led(led_type, color, mode):
    return _req("PUT", "devices/led", {"type": led_type, "color": color, "mode": mode})


# --- 2. 媒体控制 (Media) ---
def start_play_music(name: str = ""):
    payload = {"operation": "start", "name": name} if name else {"operation": "start"}
    return _req("PUT", "media/music", payload)


def stop_play_music():
    return _req("PUT", "media/music", {"operation": "stop"})


def get_media_music_list():
    return _req("GET", "media/music/list")


# --- 3. 动作控制 (Motions) ---
def start_play_motion(
    name: str = "reset",
    direction: str = "",
    speed: str = "normal",
    repeat: int = 1,
    timestamp: int = 0,
    version: str = "v1",
):
    payload = {
        "operation": "start",
        "motion": {"name": name, "repeat": repeat, "speed": speed},
        "timestamp": timestamp,
        "version": version,
    }
    if direction:
        payload["motion"]["direction"] = direction
    return _req("PUT", "motions", payload)


def stop_play_motion(name: str = "", timestamp: int = 0, version: str = "v1"):
    return _req(
        "PUT",
        "motions",
        {"operation": "stop", "name": name, "timestamp": timestamp, "version": version},
    )


def control_motion_gait(
    speed_v: int = 0,
    speed_h: int = 0,
    steps: int = 0,
    period: int = 1,
    wave: bool = False,
):
    return _req(
        "PUT",
        "motions/gait",
        {
            "speed_v": speed_v,
            "speed_h": speed_h,
            "steps": steps,
            "period": period,
            "timestamp": int(time.time() * 1000),
            "wave": wave,
        },
    )


def get_motionlist():
    return _req("GET", "motions/list")


# --- 4. 舵机控制 (Servos) ---
def get_servos_angles(names: List[str]):
    return _req("GET", "servos/angles", params={"names": names})


def set_servos_angles(angles: Dict[str, int], runtime: int = 200):
    return _req("PUT", "servos/angles", {"angles": angles, "runtime": runtime})


def set_servos_mode(mode: str, servos: List[str]):
    return _req(
        "PUT",
        "servos/mode",
        {"mode": mode, "servos": [{"name": servo_name} for servo_name in servos]},
    )


# --- 5. 传感器 (Sensors) ---
def get_sensors_list():
    return _req("GET", "sensors/list")


def get_sensors_gyro():
    return _req("GET", "sensors/gyro")


def get_sensors_ultrasonic(id=None, slot=None):
    return _req("GET", "sensors/ultrasonic", params={"id": id, "slot": slot})


def get_sensors_touch(id=None, slot=None):
    return _req("GET", "sensors/touch", params={"id": id, "slot": slot})


# --- 6. 视觉功能 (Visions) ---
def get_visual_task_result(option, vision_type):
    return _req("GET", "visions", params={"option": option, "type": vision_type})


def start_face_recognition(vision_type, ts: int = 0):
    return _req(
        "PUT",
        "visions",
        {"option": "face", "type": vision_type, "operation": "start", "timestamp": ts},
    )


def take_vision_photo(res: str = "640x480"):
    return _req("POST", "visions/photos", {"resolution": res})


def start_qr_recognition(enableStream: bool = False):
    return _req(
        "PUT", "visions/QR", {"operation": "start", "remote_stream_enable": enableStream}
    )


# --- 7. 语音功能 (Voice) ---
def start_voice_asr(continues: bool = False, ts: int = 0):
    return _req("PUT", "voice/asr", {"continues": continues, "timestamp": ts})


def start_voice_tts(tts: str = "", interrupt: bool = True, ts: int = 0):
    return _req(
        "PUT", "voice/tts", {"tts": tts, "interrupt": interrupt, "timestamp": ts}
    )


def start_voice_iat(ts: int = 0):
    return _req("PUT", "voice/iat", {"timestamp": ts})


# --- 补充：状态获取函数 ---
def get_voice_tts_state(ts: Optional[int] = None):
    res = _req("GET", "voice/tts", params={"timestamp": ts} if ts else None)
    if __resIsSuccess(res) and isinstance(res.get("data"), str):
        res["data"] = json.loads(res["data"].strip("\x00"))
    return res


def get_voice_asr_state():
    res = _req("GET", "voice/asr")
    if __resIsSuccess(res) and isinstance(res.get("data"), str):
        res["data"] = json.loads(res["data"].strip("\x00"))
    return res


# --- 8. 同步等待逻辑 (Sync Helpers) ---
async def __wait_common(ts, get_func, args=(), target_status="idle"):
    while True:
        res = get_func(*args)
        data = res.get("data", {}) if isinstance(res, dict) else {}
        status = res.get("status", data.get("status"))
        timestamp = res.get("timestamp", data.get("timestamp"))
        if ts == timestamp and status == target_status:
            return res
        await asyncio.sleep(0.5)


def sync_do_tts(text: str, interrupt: bool = True):
    t = int(time.time())
    start_voice_tts(text, interrupt, t)
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(loop.create_task(__wait_common(t, get_voice_tts_state, (t,))))


def sync_play_motion(name: str = "reset", **kwargs):
    t = int(time.time() * 1000)
    start_play_motion(name=name, timestamp=t, **kwargs)
    # 题述中该函数给出“简略实现”，此处保持同等语义并返回 True。
    return True


# --- 9. 数据结构与辅助类 ---
class RobotBatteryInfo:
    def __init__(self, data):
        self.percent = data.get("percent", 0)
        self.charging = data.get("charging", 0)
        self.voltage = data.get("voltage", 0)


class RobotVisualTaskResult:
    def __init__(self, data):
        recognition = data.get("recognition", {})
        self.name = recognition.get("name", "")
        self.quantity = data.get("quantity", 0)
        self.gesture = data.get("gesture", "")


# --- 10. uKit2.0 控制类 ---
class ukit_controller:
    def __init__(self, port: int = 25880):
        self.port = port
        self.udp_sock = socket(AF_INET, SOCK_DGRAM)
        self.udp_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    def send_msg(self, msg: str) -> None:
        addr = ("255.255.255.255", self.port)
        self.udp_sock.sendto(msg.encode(), addr)


__all__ = [
    "init",
    "yan_api_init",
    "sync_play_motion",
    "sync_do_tts",
    "start_play_motion",
    "stop_play_motion",
    "control_motion_gait",
    "get_motionlist",
    "get_robot_battery_info",
    "get_robot_fall_management_state",
    "set_robot_fall_management_state",
    "set_robot_language",
    "get_robot_volume",
    "set_robot_volume",
    "get_robot_led",
    "set_robot_led",
    "start_play_music",
    "stop_play_music",
    "get_media_music_list",
    "get_servos_angles",
    "set_servos_angles",
    "set_servos_mode",
    "get_sensors_list",
    "get_sensors_gyro",
    "get_sensors_ultrasonic",
    "get_sensors_touch",
    "get_visual_task_result",
    "start_face_recognition",
    "take_vision_photo",
    "start_qr_recognition",
    "start_voice_asr",
    "start_voice_tts",
    "start_voice_iat",
    "get_voice_tts_state",
    "get_voice_asr_state",
    "RobotBatteryInfo",
    "RobotVisualTaskResult",
    "ukit_controller",
]
