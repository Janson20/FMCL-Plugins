"""游戏时长统计插件 - 记录每个版本的游戏时长，UI 面板展示历史统计"""

import datetime
import json
from typing import Dict, List, Optional, Any

from plugin_manager.base import PluginBase, HookPoint


class PlaytimeTrackerPlugin(PluginBase):
    """游戏时长统计"""

    def get_default_config(self) -> dict:
        return {
            "show_notification_on_stop": True,
            "track_sessions": True,
        }

    def __init__(self):
        super().__init__()
        self._current_version: Optional[str] = None
        self._start_time: Optional[float] = None
        self._stats_file = None  # 在注入后设置

    def on_load(self) -> None:
        self.log("游戏时长统计插件已加载")

    def on_enable(self) -> None:
        self._stats_file = self.data_dir / "playtime_stats.json"
        self._ensure_stats_file()

        # 注册启动钩子
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.GAME_POST_LAUNCH,
            self._on_game_started,
            priority=100,
        )

        # 注册停止钩子
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.GAME_STOPPED,
            self._on_game_stopped,
            priority=100,
        )

        self.log("游戏时长统计已启用")

    def on_disable(self) -> None:
        # 如果当前正在计时，先保存
        if self._start_time is not None and self._current_version is not None:
            self._record_session()
        self.log("游戏时长统计已停用")

    def _on_game_started(self, **kwargs) -> None:
        """游戏启动后记录开始时间"""
        version_id = kwargs.get("version_id", "unknown")
        self._current_version = version_id
        self._start_time = datetime.datetime.now().timestamp()
        self.log(f"开始计时: {version_id}")

    def _on_game_stopped(self, **kwargs) -> None:
        """游戏停止后记录时长"""
        if self._start_time is None or self._current_version is None:
            return

        duration = self._record_session()

        exit_code = kwargs.get("exit_code", -1)
        self.log(f"停止计时: {self._current_version}, 时长: {self._format_duration(duration)}, 退出码: {exit_code}")

        if self.config.get("show_notification_on_stop", True):
            self.notify(
                "游戏时长",
                f"本次游戏 {self._format_duration(duration)}",
                "info",
            )

        self._current_version = None
        self._start_time = None

    def _record_session(self) -> int:
        """记录本次游戏会话，返回秒数"""
        now = datetime.datetime.now().timestamp()
        duration = int(now - self._start_time) if self._start_time else 0

        if not self._stats_file or duration < 5:
            return duration  # 忽略 5 秒以下的记录

        stats = self._load_stats()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        if self._current_version not in stats:
            stats[self._current_version] = {
                "total_seconds": 0,
                "session_count": 0,
                "first_played": today,
                "last_played": today,
                "daily": {},
            }

        entry = stats[self._current_version]
        entry["total_seconds"] += duration
        entry["session_count"] += 1
        entry["last_played"] = today

        # 每日统计
        if today not in entry.get("daily", {}):
            entry["daily"][today] = 0
        entry["daily"][today] += duration

        # 限制 daily 最多保留 365 天
        daily_keys = sorted(entry["daily"].keys())
        if len(daily_keys) > 365:
            for old_key in daily_keys[:-365]:
                del entry["daily"][old_key]

        self._save_stats(stats)
        return duration

    def get_stats(self) -> dict:
        """获取统计数据（供外部调用）"""
        return self._load_stats()

    def get_version_stats(self, version_id: str) -> Optional[dict]:
        """获取指定版本的统计"""
        stats = self._load_stats()
        return stats.get(version_id)

    def get_total_playtime(self) -> int:
        """获取总游戏时长（秒）"""
        stats = self._load_stats()
        return sum(
            v.get("total_seconds", 0)
            for v in stats.values()
        )

    def _load_stats(self) -> dict:
        if not self._stats_file or not self._stats_file.exists():
            return {}
        try:
            return json.loads(self._stats_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_stats(self, stats: dict):
        if not self._stats_file:
            return
        self._stats_file.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _ensure_stats_file(self):
        if self._stats_file and not self._stats_file.exists():
            self._stats_file.write_text("{}", encoding="utf-8")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}秒"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分钟"
        hours = minutes // 60
        remain_min = minutes % 60
        if remain_min == 0:
            return f"{hours}小时"
        return f"{hours}小时{remain_min}分钟"
