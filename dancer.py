"""
dancer.py —— 基于 YanAPI 的机器人动作库核心模块

本模块封装了与 YanAPI 交互的基础逻辑，提供统一的动作调用接口，
并预留了各类基础动作的函数接口，便于后续扩展新的动作模块。
"""

import time

try:
    import YanAPI
except ImportError:
    # 当 YanAPI 未安装时（如单元测试环境），提供一个轻量级的桩模块，
    # 避免导入错误，同时不影响核心逻辑的测试。
    import types

    YanAPI = types.SimpleNamespace(
        init=lambda ip: None,
        sync_play_motion=lambda motion_name, speed="normal": None,
    )


class RobotDancer:
    """机器人舞蹈控制类。

    负责封装 YanAPI 的调用细节，提供易用的动作接口，
    并支持通过脚本序列批量执行动作，为 AI 自动编舞提供基础设施。

    用法示例::

        dancer = RobotDancer(ip="192.168.1.100")
        dancer.stand()
        dancer.wave()
        dancer.dance_from_script([
            {"action": "stand", "duration": 1},
            {"action": "wave",  "duration": 2},
            {"action": "squat", "duration": 1},
        ])
    """

    # 允许通过 dance_from_script 调用的动作名称白名单，
    # 防止脚本数据触发任意方法调用。新增动作时请同步更新此集合。
    ALLOWED_ACTIONS: frozenset[str] = frozenset({"squat", "stand", "wave", "walk"})

    def __init__(self, ip: str = "127.0.0.1", speed: str = "normal") -> None:
        """初始化 RobotDancer 实例，配置 YanAPI 连接参数。

        Args:
            ip (str): 机器人的 IP 地址，默认为 ``"127.0.0.1"``。
            speed (str): 默认动作速度，可选 ``"slow"``、``"normal"``、``"fast"``，
                默认为 ``"normal"``。
        """
        # 保存机器人 IP 地址，供 YanAPI 初始化使用
        self.ip = ip
        # 保存默认动作速度
        self.speed = speed

        # 初始化 YanAPI 连接（设置目标机器人的 IP 地址）
        YanAPI.init(ip)

    # ------------------------------------------------------------------
    # 核心桥接方法
    # ------------------------------------------------------------------

    def action_bridge(self, motion_name: str, speed: str | None = None) -> None:
        """封装 YanAPI.sync_play_motion 调用，统一处理错误与日志。

        所有具体动作方法均应通过本方法调用底层 API，以便在一处
        集中管理重试、日志记录或速度参数覆盖等横切关注点。

        Args:
            motion_name (str): YanAPI 中注册的动作名称，例如 ``"walk"``。
            speed (str | None): 动作速度；若为 ``None`` 则使用实例默认速度。
        """
        effective_speed = speed if speed is not None else self.speed
        print(f"[RobotDancer] 执行动作: {motion_name!r}，速度: {effective_speed}")
        YanAPI.sync_play_motion(motion_name, effective_speed)

    # ------------------------------------------------------------------
    # 基础动作接口（占位方法，后续可按需丰富实现）
    # ------------------------------------------------------------------

    def squat(self, speed: str | None = None) -> None:
        """执行下蹲动作。

        机器人缓慢弯曲膝关节完成下蹲，可用于舞蹈中的节拍配合动作。

        Args:
            speed (str | None): 动作速度；若为 ``None`` 则使用实例默认速度。
        """
        # TODO: 根据实际 YanAPI 动作名称替换 "squat"
        self.action_bridge("squat", speed)

    def stand(self, speed: str | None = None) -> None:
        """执行站立/复位动作。

        使机器人恢复到标准站立姿态，通常作为舞蹈序列的起始或结束动作。

        Args:
            speed (str | None): 动作速度；若为 ``None`` 则使用实例默认速度。
        """
        # TODO: 根据实际 YanAPI 动作名称替换 "stand"
        self.action_bridge("stand", speed)

    def wave(self, speed: str | None = None) -> None:
        """执行挥手动作。

        机器人抬起一只手臂并做挥手姿态，常用于问候或舞蹈表演片段。

        Args:
            speed (str | None): 动作速度；若为 ``None`` 则使用实例默认速度。
        """
        # TODO: 根据实际 YanAPI 动作名称替换 "wave"
        self.action_bridge("wave", speed)

    def walk(self, speed: str | None = None) -> None:
        """执行行走动作。

        机器人原地踏步或向前行走一个步态周期，可用于舞蹈的移动段落。

        Args:
            speed (str | None): 动作速度；若为 ``None`` 则使用实例默认速度。
        """
        # TODO: 根据实际 YanAPI 动作名称替换 "walk"
        self.action_bridge("walk", speed)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def dance_from_script(self, script: list[dict]) -> None:
        """按照脚本列表顺序执行动作序列。

        脚本中的每个条目均为一个字典，必须包含 ``"action"`` 键（对应本类
        中已定义的方法名），可选包含 ``"duration"`` 键（单位：秒）指定动作
        结束后的等待时长，以及 ``"speed"`` 键覆盖该步骤的速度。

        Args:
            script (list[dict]): 动作脚本列表，示例::

                [
                    {"action": "stand",  "duration": 1},
                    {"action": "wave",   "duration": 2, "speed": "fast"},
                    {"action": "squat",  "duration": 1},
                    {"action": "walk",   "duration": 3},
                ]

        Raises:
            ValueError: 当脚本中包含本类未定义的动作名称时抛出。

        注意:
            若需要添加新动作，只需在类中定义同名方法即可，无需修改本方法。
        """
        print(f"[RobotDancer] 开始执行舞蹈脚本，共 {len(script)} 个动作步骤。")

        for index, step in enumerate(script, start=1):
            action_name = step.get("action")
            duration = step.get("duration", 0)
            speed = step.get("speed")  # 可选速度覆盖

            # 校验动作名称是否在白名单中，防止脚本数据触发任意方法调用
            if action_name not in self.ALLOWED_ACTIONS:
                raise ValueError(
                    f"步骤 {index}：未找到动作 {action_name!r}，"
                    "请先在 RobotDancer 类中定义对应方法，并将其加入 ALLOWED_ACTIONS。"
                )

            print(f"[RobotDancer] 步骤 {index}/{len(script)}: {action_name}")

            # 通过白名单验证后再获取方法，速度通过参数显式传递
            action_method = getattr(self, action_name)
            action_method(speed)

            # 动作完成后按脚本要求等待
            if duration > 0:
                time.sleep(duration)

        print("[RobotDancer] 舞蹈脚本执行完毕。")
