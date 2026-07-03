# FMCL 插件开发完整指南

> 本文档提供从零开发 FMCL 插件的完整教学，含代码示例、最佳实践和调试技巧。

---

## 目录

1. [快速开始](#1-快速开始)
2. [plugin.json 规范](#2-pluginjson-规范)
3. [PluginBase API 参考](#3-pluginbase-api-参考)
4. [钩子系统详解](#4-钩子系统详解)
5. [权限系统](#5-权限系统)
6. [UI 扩展](#6-ui-扩展)
7. [插件间通信](#7-插件间通信)
8. [配置与持久化](#8-配置与持久化)
9. [错误处理](#9-错误处理)
10. [测试与调试](#10-测试与调试)

---

## 1. 快速开始

### 1.1 最小插件

```python
# __init__.py
from plugin_manager.base import PluginBase

class MyPlugin(PluginBase):
    def on_enable(self):
        self.log("Hello FMCL!")

    def on_disable(self):
        self.log("Goodbye FMCL!")
```

```json
{
  "id": "com.example.hello",
  "name": "Hello FMCL",
  "version": "1.0.0",
  "author": "Your Name",
  "min_fmcl_version": "2.10.4",
  "description": {
    "zh_CN": "一个简单的示例插件",
    "en_US": "A simple example plugin"
  },
  "permissions": [],
  "dependencies": {},
  "tags": ["utility"],
  "homepage": "https://github.com/yourname/hello-fmcl",
  "license": "MIT",
  "entry": "__init__"
}
```

### 1.2 打包测试

```bash
# Windows PowerShell
Compress-Archive -Path my-plugin/* -DestinationPath my-plugin.fmpl

# Linux/macOS
cd my-plugin && zip -r ../my-plugin.fmpl .
```

将 `.fmpl` 文件通过 FMCL → 设置 → 插件 → 从文件安装。

---

## 2. plugin.json 规范

### 2.1 完整字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 全局唯一标识，反向域名格式 |
| `name` | string | 是 | 显示名称，最长 64 字符 |
| `version` | string | 是 | SemVer 2.0 版本号 |
| `author` | string | 是 | 作者/组织名称 |
| `min_fmcl_version` | string | 是 | 最低兼容 FMCL 版本 |
| `max_fmcl_version` | string | 否 | 最高兼容 FMCL 版本 |
| `description` | object | 是 | 多语言描述，至少含 zh_CN 和 en_US |
| `permissions` | string[] | 否 | 请求的权限列表 |
| `dependencies` | object | 否 | 依赖的插件及版本约束 |
| `conflicts` | object | 否 | 冲突的插件及版本约束 |
| `tags` | string[] | 否 | 分类标签 |
| `homepage` | string | 否 | 开源仓库或网站 URL |
| `license` | string | 否 | SPDX 许可证标识 |
| `icon` | string | 否 | 图标文件名 |
| `exports` | string[] | 否 | 导出 API 列表 |
| `imports` | string[] | 否 | 导入其他插件 API 列表 |
| `entry` | string | 否 | 入口模块名，默认 `__init__` |

### 2.2 标签分类

| 标签 | 说明 |
|------|------|
| `utility` | 实用工具 |
| `ui` | UI 扩展 |
| `gameplay` | 游戏体验 |
| `server` | 服务器相关 |
| `modpack` | 整合包相关 |
| `performance` | 性能优化 |
| `backup` | 备份还原 |
| `theme` | 主题美化 |
| `automation` | 自动化 |
| `integration` | 第三方集成 |

### 2.3 版本约束语法

```
>=1.0.0,<2.0.0     # 兼容 1.x 所有版本
==1.5.0            # 精确匹配
>=1.0              # 自动补全为 >=1.0.0
^1.2.3             # 兼容 1.x.x (>=1.2.3,<2.0.0) -- 暂不支持
```

---

## 3. PluginBase API 参考

### 3.1 属性（引擎自动注入）

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.manifest` | `PluginManifest` | 解析后的 plugin.json |
| `self.plugin_dir` | `Path` | 插件安装目录 |
| `self.data_dir` | `Path` | 插件数据目录（自动创建） |
| `self.config` | `dict` | 插件配置（可读写，自动持久化） |
| `self._manager` | `PluginManager` | 插件管理器引用 |
| `self._perm_state` | `PluginPermissionState` | 权限状态 |

### 3.2 生命周期方法

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ on_load()│ → │on_enable()│ → │ (运行中)  │ → │on_disable()│ → │on_uninstall()│
└──────────┘    └──────────┘    └──────────┘    └───────────┘    └──────────────┘
     模块导入         启用后              运行中              用户禁用          卸载前
```

```python
class MyPlugin(PluginBase):

    def on_load(self) -> None:
        """模块导入后调用。用于轻量初始化。"""
        pass

    def on_enable(self) -> None:
        """插件启用时调用。注册钩子、创建 UI。"""
        # 注册钩子
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.GAME_POST_LAUNCH,
            self._on_game_launched,
            priority=100,
        )

    def on_disable(self) -> None:
        """插件停用时调用。清理资源。"""
        pass

    def on_uninstall(self) -> None:
        """插件被卸载前调用。清理持久化数据。"""
        pass
```

### 3.3 便利方法

```python
# 日志记录
self.log("消息内容")                    # info 级别
self.log("警告消息", "warning")
self.log("错误消息", "error")

# Toast 通知 (需要 ui.notification 权限)
self.notify("标题", "消息内容", "info")
self.notify("成功", "操作完成", "success")
self.notify("警告", "注意检查", "warning")
self.notify("错误", "操作失败", "error")

# 获取默认配置
def get_default_config(self) -> dict:
    return {"enabled": True, "threshold": 100}

# 配置持久化
self.config["threshold"] = 200
self._manager.save_plugin_config(self.manifest.id)
```

---

## 4. 钩子系统详解

### 4.1 所有钩子点

| 钩子 | 策略 | 参数 | 触发时机 |
|------|------|------|----------|
| `GAME_PRE_LAUNCH` | COLLECT | version_id, command | 游戏即将启动 |
| `GAME_POST_LAUNCH` | ALL | version_id, pid | 游戏已启动 |
| `GAME_STOPPED` | ALL | exit_code | 游戏进程已停止 |
| `GAME_CRASHED` | COLLECT | crash_report | 游戏崩溃后 |
| `VERSION_PRE_INSTALL` | FIRST | version_id, mod_loader | 版本安装前 |
| `VERSION_POST_INSTALL` | ALL | version_id, success | 版本安装后 |
| `VERSION_PRE_REMOVE` | FIRST | version_id | 版本删除前 |
| `SERVER_PRE_START` | FIRST | server_name | 服务器即将启动 |
| `SERVER_POST_START` | ALL | server_name, pid | 服务器已启动 |
| `SERVER_STOPPED` | ALL | server_name, exit_code | 服务器已停止 |
| `APP_STARTUP` | ALL | — | 启动器完全初始化 |
| `APP_SHUTDOWN` | ALL | — | 启动器即将关闭 |
| `UI_TAB_REGISTER` | COLLECT | — | 请求注册标签页 |
| `UI_SIDEBAR_REGISTER` | COLLECT | — | 请求注册侧边栏 |
| `UI_SETTINGS_REGISTER` | COLLECT | — | 请求注册设置项 |
| `DOWNLOAD_PRE_DOWNLOAD` | COLLECT | — | 文件下载前 |
| `DOWNLOAD_POST_DOWNLOAD` | ALL | — | 文件下载后 |

### 4.2 钩子策略说明

```python
# COLLECT: 收集所有处理器的返回值
# 适用于 UI 注册、崩溃分析等场景
results = self._manager.emit(HookPoint.GAME_CRASHED, crash_report=report)
for result in results:
    print(result)  # 每个处理器的返回值

# FIRST: 返回第一个非 None 值
# 适用于可阻止操作（如安装前检查）
result = self._manager.emit(HookPoint.VERSION_PRE_INSTALL, version_id="1.20.4")
if result is not None:
    # 处理器返回了某个值（如拒绝安装的原因）
    pass

# ALL: 不收集返回值，纯通知
self._manager.emit(HookPoint.APP_STARTUP)
```

### 4.3 优先级

优先级数值越小越早执行，默认 100：

```python
self._manager.register_hook(
    self.manifest.id,
    HookPoint.GAME_PRE_LAUNCH,
    self._on_launch,
    priority=50,   # 较早执行
)
```

---

## 5. 权限系统

### 5.1 检查权限

```python
from plugin_manager.permissions import PluginPermission

def some_operation(self):
    if not self._perm_state.is_granted(PluginPermission.FILESYSTEM_WRITE):
        self.log("权限不足: filesystem.write", "warning")
        return
    # 执行操作...
```

### 5.2 请求权限

```python
approved = self._manager.request_permission(
    self.manifest.id,
    PluginPermission.CORE_PROCESS
)
if approved:
    self._run_external_tool()
```

---

## 6. UI 扩展

### 6.1 注册标签页

```python
from plugin_manager.base import PluginBase, HookPoint

class MyPlugin(PluginBase):
    def on_enable(self):
        self._manager.register_hook(
            self.manifest.id,
            HookPoint.UI_TAB_REGISTER,
            self._on_register_tab,
        )

    def _on_register_tab(self, **kwargs):
        return {
            "id": "my_plugin_tab",
            "text": "我的工具",      # i18n 键或直接文本
            "order": 100,
            "callback": self._create_tab_ui,
        }
```

### 6.2 创建设置面板

```python
import customtkinter as ctk

def get_settings_ui(self, parent) -> any:
    """返回设置面板框架"""
    frame = ctk.CTkFrame(parent)

    ctk.CTkLabel(frame, text="我的插件设置").pack(pady=10)

    switch_var = ctk.BooleanVar(value=self.config.get("enabled", True))
    switch = ctk.CTkSwitch(
        frame, text="启用功能",
        variable=switch_var,
        command=lambda: self._save_setting("enabled", switch_var.get()),
    )
    switch.pack(pady=5)

    return frame
```

---

## 7. 插件间通信

### 7.1 导出 API

**插件 A** (`plugin.json`):
```json
{
  "id": "com.example.provider",
  "exports": ["get_data"]
}
```

**插件 A** (`__init__.py`):
```python
class ProviderPlugin(PluginBase):
    def on_enable(self):
        self._manager.export_api(
            self.manifest.id, "get_data", self._get_data
        )

    def _get_data(self, key: str) -> Optional[str]:
        return self.config.get(key)
```

### 7.2 导入 API

**插件 B** (`plugin.json`):
```json
{
  "id": "com.example.consumer",
  "imports": ["get_data"]
}
```

**插件 B** (`__init__.py`):
```python
class ConsumerPlugin(PluginBase):
    def on_enable(self):
        get_data = self._manager.get_plugin_api(
            "com.example.provider", "get_data"
        )
        if get_data:
            value = get_data("some_key")
            self.log(f"获取到数据: {value}")
```

---

## 8. 配置与持久化

### 8.1 插件配置

每个插件有独立的配置空间，持久化路径：
```
plugins/configs/{plugin_id}.json
```

```python
class MyPlugin(PluginBase):

    def get_default_config(self) -> dict:
        return {
            "api_endpoint": "https://api.example.com",
            "poll_interval": 300,
            "last_sync": "",
        }

    def on_enable(self):
        # 读取
        interval = self.config["poll_interval"]
        self.log(f"轮询间隔: {interval}秒")

        # 修改并持久化
        self.config["last_sync"] = datetime.now().isoformat()
        self._manager.save_plugin_config(self.manifest.id)
```

### 8.2 插件数据目录

每个插件有独立的数据目录，用于存储大文件：
```
plugins/data/{plugin_id}/
```

```python
def on_enable(self):
    # self.data_dir 自动指向正确路径
    db_path = self.data_dir / "cache.db"
    log_path = self.data_dir / "plugin.log"

    # 写入数据
    (self.data_dir / "downloads").mkdir(exist_ok=True)
```

---

## 9. 错误处理

### 9.1 异常隔离

```python
def on_enable(self) -> None:
    """on_enable 中的异常会使插件进入 ERROR 状态"""
    try:
        self._dangerous_operation()
    except Exception as e:
        self.log(f"初始化失败: {e}", "error")
        raise  # 重新抛出，让引擎知道初始化失败

def _safe_file_operation(self, path: Path):
    """外部文件操作应自行处理异常"""
    try:
        data = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        self.log(f"文件不存在: {path}", "warning")
        return None
    except PermissionError:
        self.log(f"权限不足: {path}", "error")
        return None
    except Exception as e:
        self.log(f"读取文件异常: {e}", "error")
        return None
```

### 9.2 线程安全

所有 tkinter/CustomTkinter 操作必须在主线程执行：

```python
import threading

def on_enable(self):
    # 后台线程下载
    self._download_thread = threading.Thread(
        target=self._download_assets, daemon=True
    )
    self._download_thread.start()

def _download_assets(self):
    """在后台线程中执行"""
    result = requests.get("https://api.example.com/data")
    # 如果需要在 UI 上更新，使用 after
    # 主线程更新由 _manager 通知回调处理
```

---

## 10. 测试与调试

### 10.1 本地开发

1. 将插件源码放到 `plugins/installed/com.example.plugin/`
2. 确保 `plugin.json` 和 `__init__.py` 正确
3. 启动 FMCL，插件会自动被发现

### 10.2 日志查看

```python
# 插件日志会包含在 FMCL 主日志中
self.log("这条日志会出现在 latest.log")

# 也可写入独立日志文件
log_file = self.data_dir / "plugin.log"
with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"[{datetime.now()}] 调试信息\n")
```

### 10.3 常见问题排查

| 问题 | 可能原因 | 解决 |
|------|----------|------|
| 插件未出现在列表中 | `plugin.json` 格式错误 | 检查 JSON 语法，确保 `id` 字段与目录名一致 |
| 插件状态为 `incompatible` | FMCL 版本不兼容 | 检查 `min_fmcl_version` 是否 <= 当前版本 |
| 插件状态为 `error` | `on_enable()` 抛出异常 | 查看 `latest.log` 中的堆栈跟踪 |
| 钩子未触发 | 未注册或权限不足 | 确保在 `on_enable()` 中注册钩子，且持有对应权限 |
| 通知不显示 | 缺少 `ui.notification` 权限 | 在 `permissions` 中添加 `ui.notification` |

### 10.4 检查清单

在发布插件前，确认以下事项：

- [ ] `plugin.json` 字段全部填写，JSON 格式合法
- [ ] `id` 唯一且符合命名规范
- [ ] `version` 符合 SemVer 格式
- [ ] `description` 至少包含 `zh_CN` 和 `en_US`
- [ ] `permissions` 只包含实际使用的权限
- [ ] `__init__.py` 导出了 `PluginBase` 子类
- [ ] `on_enable()` 中注册了需要的钩子
- [ ] `on_disable()` 中清理了所有资源
- [ ] 本地测试通过（安装、启用、禁用、卸载）
- [ ] 不包含任何硬编码的绝对路径
