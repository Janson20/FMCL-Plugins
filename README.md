# FMCL 插件市场

FMCL（Fusion Minecraft Launcher）的官方插件仓库。开发者可将插件以 `.fmpl` 格式提交至此仓库，用户可通过 FMCL 启动器浏览和安装。

---

## 目录结构

```
fmcl-plugins/
├── .github/workflows/        # GitHub Actions: 自动生成 index.json
├── plugins/                  # ★ 所有插件存放于此
│   └── com.example.plugin/
│       ├── plugin.json       # 插件清单（必需）
│       ├── __init__.py       # 入口模块（必需）
│       └── icon.png          # 插件图标（推荐 128x128）
├── docs/                     # 开发文档
│   ├── PLUGIN_DEV.md         # 插件开发指南
│   ├── MARKETPLACE_GUIDE.md  # 市场提交指南
│   └── PERMISSIONS.md       # 权限参考
├── scripts/
│   └── generate_index.py     # index.json 生成脚本
├── index.json                # ★ 自动生成的插件索引（勿手动编辑）
├── CONTRIBUTING.md           # 贡献指南
├── .gitignore
└── README.md                 # 本文件
```

## 如何使用

### 对于用户

在 FMCL 启动器中打开「设置 → 插件 → 打开插件管理」，即可浏览和安装本仓库中的插件。

每个插件版本通过 [GitHub Releases](https://github.com/Janson20/FMCL-Plugins/releases) 附带 `.fmpl` 文件分发。

### 对于开发者

1. Fork 本仓库
2. 在 `plugins/` 下创建你的插件目录（命名为 `com.yourname.plugin-id`）
3. 编写 `plugin.json` 和 `__init__.py`
4. 提交 Pull Request
5. 审核通过后合并，CI 自动将插件信息加入 `index.json`

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [docs/MARKETPLACE_GUIDE.md](docs/MARKETPLACE_GUIDE.md)。

## 官方插件

| 插件 | 说明 |
|------|------|
| [自动备份](plugins/com.fmcl.auto-backup/) | 游戏启动前自动备份存档，支持定时清理旧备份 |
| [Fabric API 安装器](plugins/com.fmcl.fabric-api-installer/) | 安装 Fabric 时自动下载 Fabric API 及常用前置模组 |
| [游戏时长统计](plugins/com.fmcl.playtime-tracker/) | 记录每个版本的游戏时长，UI 面板展示历史统计 |
| [主题调度器](plugins/com.fmcl.theme-scheduler/) | 根据系统时间自动切换日/夜主题 |

## 许可证

本仓库中的插件各自拥有独立许可证（在 `plugin.json` 中声明）。仓库基础设施及文档使用 MIT 协议。
