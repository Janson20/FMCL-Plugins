"""主题调度器 - 根据系统时间自动切换日/夜主题"""

import datetime
import threading
from typing import Optional

from plugin_manager.base import PluginBase, HookPoint


# ── 内置日/夜间主题配色 ──
DAY_THEME_COLORS = {
    "bg_dark": "#f0f2f5",
    "bg_medium": "#e4e6eb",
    "bg_light": "#d8dadf",
    "accent": "#1877f2",
    "accent_hover": "#166fe5",
    "success": "#42b72a",
    "warning": "#f7b928",
    "error": "#fa383e",
    "text_primary": "#1c1e21",
    "text_secondary": "#606770",
    "card_bg": "#ffffff",
    "card_border": "#ccd0d5",
}

NIGHT_THEME_COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b81",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "card_bg": "#1e2a4a",
    "card_border": "#2d3a5c",
}


class ThemeSchedulerPlugin(PluginBase):
    """根据系统时间自动切换主题"""

    def get_default_config(self) -> dict:
        return {
            "day_start": "06:00",       # 日间主题开始时间 (HH:MM)
            "night_start": "18:00",     # 夜间主题开始时间 (HH:MM)
            "day_accent": "#1877f2",    # 日间强调色
            "night_accent": "#e94560",  # 夜间强调色
            "enabled": True,
            "transition_notify": False,  # 切换时是否通知
        }

    def __init__(self):
        super().__init__()
        self._timer: Optional[threading.Timer] = None
        self._current_mode: Optional[str] = None  # "day" / "night"
        self._running = False

    def on_enable(self) -> None:
        if not self.config.get("enabled", True):
            self.log("主题调度已禁用")
            return

        self._running = True
        # 立即应用当前时段主题
        self._apply_current_theme()
        # 启动定时检查（每 60 秒）
        self._schedule_next_check()
        self.log("主题调度器已启用 (日间: {} - 夜间: {})".format(
            self.config["day_start"], self.config["night_start"],
        ))

    def on_disable(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self.log("主题调度器已停用")

    def _apply_current_theme(self):
        """根据当前时间判断并应用日/夜主题"""
        now = datetime.datetime.now().time()
        day_start = self._parse_time(self.config["day_start"])
        night_start = self._parse_time(self.config["night_start"])

        if day_start <= now < night_start:
            desired_mode = "day"
        else:
            desired_mode = "night"

        if desired_mode != self._current_mode:
            self._current_mode = desired_mode
            self._apply_theme(desired_mode)

    def _apply_theme(self, mode: str):
        """应用日间或夜间主题"""
        try:
            from ui.constants import COLORS
            from ui.theme_engine import get_theme_engine

            colors = DAY_THEME_COLORS if mode == "day" else NIGHT_THEME_COLORS
            accent = self.config.get("day_accent" if mode == "day" else "night_accent")

            # 更新全局颜色
            COLORS.clear()
            COLORS.update(colors)
            if accent:
                COLORS["accent"] = accent

            # 通知主题引擎重新渲染
            engine = get_theme_engine()
            if engine:
                self.log(f"已切换到{'日间' if mode == 'day' else '夜间'}主题")

            if self.config.get("transition_notify", False):
                icon = "☀️" if mode == "day" else "🌙"
                mode_name = "日间" if mode == "day" else "夜间"
                self.notify(f"{icon} 主题已切换", f"已自动切换到{mode_name}主题", "info")

        except Exception as e:
            self.log(f"主题切换失败: {e}", "error")

    def _schedule_next_check(self):
        """设置下一次定时检查"""
        if not self._running:
            return
        self._timer = threading.Timer(60, self._on_timer_tick)
        self._timer.daemon = True
        self._timer.start()

    def _on_timer_tick(self):
        """定时器回调"""
        self._apply_current_theme()
        self._schedule_next_check()

    @staticmethod
    def _parse_time(time_str: str) -> datetime.time:
        """解析 HH:MM 字符串为 time 对象"""
        parts = time_str.split(":")
        return datetime.time(
            hour=int(parts[0]),
            minute=int(parts[1]) if len(parts) > 1 else 0,
        )
