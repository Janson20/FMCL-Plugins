"""游戏时长统计插件 - 记录每个版本的游戏时长，UI 面板展示历史统计"""

import datetime
import json
import operator
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
        self._tab_container = None  # 标签页容器引用

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

        # 注册 UI 标签页
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.UI_TAB_REGISTER,
            self._on_register_tab,
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

        # 刷新标签页 UI
        self._refresh_tab_ui()

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

    @staticmethod
    def _format_duration_short(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        remain = minutes % 60
        if remain == 0:
            return f"{hours}h"
        return f"{hours}h{remain}m"

    # ── UI ──

    def _on_register_tab(self, **kwargs):
        """UI_TAB_REGISTER 钩子回调"""
        return {
            "id": "playtime_tracker_tab",
            "text": "🎮 游戏时长",
            "order": 90,
        }

    def get_tab_ui(self, parent):
        """返回标签页 UI"""
        try:
            import customtkinter as ctk
        except ImportError:
            self.log("CustomTkinter 不可用，无法创建标签页", "warning")
            return None

        from ui.constants import COLORS, FONT_FAMILY

        container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self._tab_container = container  # 保存引用以便后续刷新
        self._build_stats_ui(container, COLORS, FONT_FAMILY, ctk)
        return container

    def _refresh_tab_ui(self):
        """刷新标签页 UI（主线程安全）"""
        container = self._tab_container
        if container is None or not container.winfo_exists():
            return
        # 清除旧内容
        for w in container.winfo_children():
            w.destroy()
        # 重建
        try:
            import customtkinter as ctk
        except ImportError:
            return
        from ui.constants import COLORS, FONT_FAMILY
        self._build_stats_ui(container, COLORS, FONT_FAMILY, ctk)

    def _build_stats_ui(self, container, COLORS, FONT_FAMILY, ctk):
        """构建统计数据 UI"""
        stats = self._load_stats()

        # ── 顶部概览 ──
        overview = ctk.CTkFrame(container, fg_color=COLORS["card_bg"], corner_radius=10)
        overview.pack(fill=ctk.X, padx=4, pady=(6, 12))

        inner = ctk.CTkFrame(overview, fg_color="transparent")
        inner.pack(fill=ctk.X, padx=16, pady=(14, 14))

        total_seconds = sum(v.get("total_seconds", 0) for v in stats.values())
        total_sessions = sum(v.get("session_count", 0) for v in stats.values())
        version_count = len(stats)

        ctk.CTkLabel(
            inner,
            text=self._format_duration(total_seconds),
            font=ctk.CTkFont(family=FONT_FAMILY, size=30, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor=ctk.W)

        ctk.CTkLabel(
            inner,
            text=f"共 {total_sessions} 次游戏 · {version_count} 个版本",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor=ctk.W, pady=(2, 0))

        if not stats:
            empty = ctk.CTkLabel(
                container,
                text="暂无游戏记录\n启动一次 Minecraft 后数据将在此显示",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=COLORS["text_secondary"],
            )
            empty.pack(pady=40)
            return

        # ── 按版本统计 ──
        ctk.CTkLabel(
            container,
            text="📦 按版本统计",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor=ctk.W, padx=4, pady=(0, 6))

        # 按总时长降序排列
        sorted_versions = sorted(
            stats.items(),
            key=lambda kv: kv[1].get("total_seconds", 0),
            reverse=True,
        )

        for version_id, info in sorted_versions:
            self._create_version_card(
                container, COLORS, FONT_FAMILY, ctk,
                version_id, info,
            )

        # 底部留白
        ctk.CTkFrame(
            container, fg_color="transparent", height=20,
        ).pack(fill=ctk.X)

    def _create_version_card(self, container, COLORS, FONT_FAMILY, ctk, version_id, info):
        """创建单个版本的统计卡片"""
        total_sec = info.get("total_seconds", 0)
        session_count = info.get("session_count", 0)
        first_played = info.get("first_played", "")
        last_played = info.get("last_played", "")
        daily = info.get("daily", {})

        card = ctk.CTkFrame(container, fg_color=COLORS["card_bg"], corner_radius=8)
        card.pack(fill=ctk.X, padx=4, pady=3)

        # 顶部行: 版本名称 + 总时长
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill=ctk.X, padx=12, pady=(10, 2))

        ctk.CTkLabel(
            top,
            text=version_id,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side=ctk.LEFT)

        ctk.CTkLabel(
            top,
            text=self._format_duration(total_sec),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side=ctk.RIGHT)

        # 详情行
        detail = ctk.CTkFrame(card, fg_color="transparent")
        detail.pack(fill=ctk.X, padx=12, pady=(0, 4))

        detail_parts = [f"{session_count} 次游戏"]
        if first_played:
            detail_parts.append(f"首次: {first_played}")
        if last_played:
            detail_parts.append(f"最近: {last_played}")

        ctk.CTkLabel(
            detail,
            text=" · ".join(detail_parts),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"],
        ).pack(anchor=ctk.W)

        # ── 每日统计（最近 7 天） ──
        if daily:
            self._create_daily_bars(card, COLORS, FONT_FAMILY, ctk, daily, total_sec)

    def _create_daily_bars(self, card, COLORS, FONT_FAMILY, ctk, daily, total_sec):
        """创建每日时长柱状图（最近 7 天）"""
        sorted_days = sorted(daily.items())[-7:]

        bar_frame = ctk.CTkFrame(card, fg_color="transparent")
        bar_frame.pack(fill=ctk.X, padx=12, pady=(0, 10))

        max_sec = max(daily.values()) if daily else 1
        bar_height = 60

        for day_str, sec in sorted_days:
            col = ctk.CTkFrame(bar_frame, fg_color="transparent")
            col.pack(side=ctk.LEFT, fill=ctk.Y, padx=3)

            # 柱状图
            height = max(4, int(bar_height * sec / max_sec))
            bar = ctk.CTkFrame(
                col,
                fg_color=COLORS["accent"],
                corner_radius=3,
                width=44,
                height=height,
            )
            bar.pack(side=ctk.BOTTOM)

            # 时长标签
            label_text = self._format_duration_short(sec)
            ctk.CTkLabel(
                col,
                text=label_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                text_color=COLORS["text_secondary"],
            ).pack(side=ctk.BOTTOM)

            # 日期标签（MM-DD）
            day_label = day_str[5:]  # 去掉 "YYYY-"
            ctk.CTkLabel(
                col,
                text=day_label,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                text_color=COLORS["text_secondary"],
            ).pack(side=ctk.BOTTOM, pady=(2, 0))
