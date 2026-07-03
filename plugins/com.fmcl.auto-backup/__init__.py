"""自动备份插件 - 游戏启动前自动备份存档，自动清理旧备份"""

import datetime
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List

from plugin_manager.base import PluginBase, HookPoint


class AutoBackupPlugin(PluginBase):
    """游戏启动前自动备份所有存档"""

    def get_default_config(self) -> dict:
        return {
            "compress_level": 6,     # zip 压缩级别 0-9
            "max_backups_per_world": 10,  # 每个世界最多保留备份数
            "enabled": True,
        }

    def on_load(self) -> None:
        self.log("自动备份插件已加载")

    def on_enable(self) -> None:
        if not self.config.get("enabled", True):
            self.log("自动备份已禁用")
            return

        self._manager.register_hook(
            self.manifest.id,
            HookPoint.GAME_PRE_LAUNCH,
            self._on_game_pre_launch,
            priority=200,  # 在 game.pre_launch 中较早执行
        )
        self.log(f"自动备份已启用 (压缩级别: {self.config['compress_level']}, 每世界保留: {self.config['max_backups_per_world']})")

    def on_disable(self) -> None:
        self.log("自动备份已停用")

    def _on_game_pre_launch(self, **kwargs) -> None:
        """游戏启动前备份所有存档"""
        if not self.config.get("enabled", True):
            return

        version_id = kwargs.get("version_id", "unknown")
        self.log(f"游戏即将启动 ({version_id})，开始自动备份...")

        try:
            # 获取 Minecraft 目录
            minecraft_dir = self._get_minecraft_dir()
            saves_dir = minecraft_dir / "saves"

            if not saves_dir.exists():
                self.log("saves 目录不存在，跳过备份")
                return

            # 枚举所有世界存档
            worlds = [d for d in saves_dir.iterdir() if d.is_dir()]
            if not worlds:
                self.log("没有找到世界存档，跳过备份")
                return

            # 备份目录: plugins/data/com.fmcl.auto-backup/backups/{世界名}/
            backup_root = self.data_dir / "backups"
            backup_root.mkdir(parents=True, exist_ok=True)

            total_backed = 0
            for world_dir in worlds:
                try:
                    self._backup_world(world_dir, backup_root)
                    total_backed += 1
                except Exception as e:
                    self.log(f"备份世界 '{world_dir.name}' 失败: {e}", "warning")

            if total_backed > 0:
                self.notify("自动备份完成", f"已备份 {total_backed} 个世界存档", "success")
                self.log(f"备份完成: {total_backed} 个世界")

        except Exception as e:
            self.log(f"自动备份异常: {e}", "error")

    def _backup_world(self, world_dir: Path, backup_root: Path):
        """备份单个世界存档并清理旧备份"""
        world_name = world_dir.name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{world_name}_{timestamp}.zip"
        backup_path = backup_root / world_name / backup_filename

        # 确保备份目录存在
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建压缩备份
        self.log(f"正在备份: {world_name}...")
        with zipfile.ZipFile(
            backup_path, "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=self.config.get("compress_level", 6),
        ) as zf:
            for file_path in world_dir.rglob("*"):
                if file_path.is_file():
                    # 跳过过大的文件（如 Dynmap 的 SQLite 数据库）
                    try:
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                    except OSError:
                        continue
                    if size_mb > 500:
                        self.log(f"跳过超大文件 ({size_mb:.0f}MB): {file_path.name}", "warning")
                        continue
                    arcname = str(file_path.relative_to(world_dir))
                    zf.write(file_path, arcname)

        backup_size = backup_path.stat().st_size / (1024 * 1024)
        self.log(f"  {world_name}: {backup_filename} ({backup_size:.1f}MB)")

        # 清理旧备份
        self._cleanup_old_backups(backup_root / world_name)

    def _cleanup_old_backups(self, world_backup_dir: Path):
        """保留最近 N 个备份，删除更旧的"""
        max_backups = self.config.get("max_backups_per_world", 10)

        backups = sorted(
            world_backup_dir.glob("*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if len(backups) <= max_backups:
            return

        for old in backups[max_backups:]:
            try:
                old.unlink()
                self.log(f"  清理旧备份: {old.name}")
            except OSError:
                pass

    def _get_minecraft_dir(self) -> Path:
        """获取 Minecraft 目录"""
        from config import Config
        try:
            mcdir = self._manager._notify_callback  # 不可用，通过反射获取
        except Exception:
            pass
        # 通过启动器配置获取
        import config
        cfg = config.Config()
        return Path(cfg.minecraft_dir)
