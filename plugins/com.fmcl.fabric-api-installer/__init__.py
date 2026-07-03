"""Fabric API 自动安装器 - 确保 Fabric 版本有 Fabric API 等必备模组"""

import threading
from pathlib import Path

from plugin_manager.base import PluginBase, HookPoint


FABRIC_API_PROJECT_ID = "P7dR8mSH"    # Modrinth Fabric API
MOD_MENU_PROJECT_ID = "mOgUt4GM"      # Mod Menu
SODIUM_PROJECT_ID = "AANobbMI"        # Sodium

OPTIONAL_MODS = [
    {
        "id": MOD_MENU_PROJECT_ID,
        "name": "Mod Menu",
        "desc": "Fabric 模组配置菜单",
        "default_enabled": True,
    },
    {
        "id": SODIUM_PROJECT_ID,
        "name": "Sodium",
        "desc": "高性能渲染引擎",
        "default_enabled": False,
    },
]


class FabricApiInstallerPlugin(PluginBase):
    """Fabric API 自动安装"""

    def get_default_config(self) -> dict:
        return {
            "auto_install_fabric_api": True,
            "optional_mods": {
                MOD_MENU_PROJECT_ID: True,
                SODIUM_PROJECT_ID: False,
            },
            "check_interval_days": 7,
        }

    def on_enable(self) -> None:
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.GAME_PRE_LAUNCH,
            self._on_game_pre_launch,
            priority=150,
        )
        self.log("Fabric API 自动安装器已启用")

    def on_disable(self) -> None:
        self.log("Fabric API 自动安装器已停用")

    def _on_game_pre_launch(self, **kwargs) -> None:
        """游戏启动前检查 Fabric API 是否安装"""
        version_id = kwargs.get("version_id", "")

        if "fabric" not in version_id.lower():
            return

        self.log(f"检测到 Fabric 版本: {version_id}")

        # 获取 gameDirectory（版本隔离目录）或默认 minecraft 目录
        command = kwargs.get("command", [])
        game_dir = self._extract_game_dir(command)

        if not game_dir:
            self.log("无法确定游戏目录，跳过检查")
            return

        mods_dir = Path(game_dir) / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)

        # 检查 Fabric API
        has_fabric_api = self._has_mod(mods_dir, "fabric-api")

        if not has_fabric_api and self.config.get("auto_install_fabric_api", True):
            self.log("Fabric API 未安装，正在自动下载...")
            self.notify("Fabric API 自动安装", "检测到缺失 Fabric API，正在安装...", "info")
            self._install_mod(FABRIC_API_PROJECT_ID, mods_dir, version_id, "Fabric API")

        # 检查可选模组
        for opt_mod in OPTIONAL_MODS:
            mod_id = opt_mod["id"]
            if not self.config.get("optional_mods", {}).get(mod_id, False):
                continue

            mod_name = opt_mod["name"]
            has_mod = self._has_mod_loose(mods_dir, mod_id)
            if not has_mod:
                self.log(f"{mod_name} 未安装，正在自动下载...")
                self._install_mod(mod_id, mods_dir, version_id, mod_name)

    def _has_mod(self, mods_dir: Path, prefix: str) -> bool:
        """检查 mods 目录中是否存在以指定前缀开头的 jar 文件"""
        for f in mods_dir.iterdir():
            if f.is_file() and f.name.lower().startswith(prefix.lower()):
                return True
        return False

    def _has_mod_loose(self, mods_dir: Path, project_id: str) -> bool:
        """宽松检查：遍历 mods 目录中是否有包含 project_id 文件名的 jar"""
        for f in mods_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".jar":
                # 简单检查文件名中是否包含 id（从 Modrinth 下载的 jar 通常如此）
                if project_id.lower() in f.name.lower():
                    return True
        return False

    def _install_mod(self, project_id: str, mods_dir: Path, version_id: str, display_name: str):
        """从 Modrinth 安装单个模组"""
        from modrinth import parse_game_version_from_version

        mc_version = parse_game_version_from_version(version_id)
        if not mc_version:
            self.log(f"无法从版本 ID '{version_id}' 中解析 Minecraft 版本", "warning")
            return

        try:
            from modrinth import install_mod_with_deps

            ok, msg, names = install_mod_with_deps(
                project_id=project_id,
                game_version=mc_version,
                mod_loader="fabric",
                mods_dir=str(mods_dir),
                status_callback=lambda s: self.log(s),
            )

            if ok:
                self.log(f"{display_name} 安装成功: {', '.join(names)}")
                self.notify(f"{display_name} 已安装", f"版本: {', '.join(names)}", "success")
            else:
                self.log(f"{display_name} 安装失败: {msg}", "warning")
                self.notify(f"{display_name} 安装失败", str(msg)[:100], "warning")

        except Exception as e:
            self.log(f"{display_name} 安装异常: {e}", "error")

    def _extract_game_dir(self, command) -> str:
        """从启动命令中提取 gameDirectory"""
        if not command:
            return ""
        try:
            for i, arg in enumerate(command):
                if arg == "--gameDir" and i + 1 < len(command):
                    return command[i + 1]
        except Exception:
            pass
        return ""
