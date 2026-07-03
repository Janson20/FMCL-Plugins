# 贡献指南

感谢你对 FMCL 插件市场的贡献！提交插件前，请仔细阅读本指南。

---

## 前提条件

1. 熟悉 Python 编程
2. 了解 FMCL 插件系统架构（参见 [docs/PLUGIN_DEV.md](docs/PLUGIN_DEV.md)）
3. 已阅读 FMCL 插件权限体系（参见 [docs/PERMISSIONS.md](docs/PERMISSIONS.md)）

## 提交流程

### 1. Fork 仓库

访问 https://github.com/Janson20/FMCL-Plugins ，点击右上角 Fork。

### 2. 创建插件目录

```bash
cd plugins/
mkdir com.yourname.plugin-id
```

**命名规范**：`com.<作者名或组织>.<插件功能>`，使用小写字母、数字和连字符。

### 3. 编写插件文件

#### plugin.json（必需）

```json
{
  "id": "com.yourname.plugin-id",
  "name": "你的插件名称",
  "version": "1.0.0",
  "author": "你的名字",
  "min_fmcl_version": "2.10.4",
  "description": {
    "zh_CN": "插件功能的简要描述",
    "en_US": "Brief description of what the plugin does"
  },
  "permissions": ["ui.notification", "data.store"],
  "dependencies": {},
  "conflicts": {},
  "tags": ["utility"],
  "homepage": "https://github.com/yourname/plugin",
  "license": "MIT",
  "entry": "__init__"
}
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | 是 | 全局唯一标识 |
| `name` | 是 | 显示名称 |
| `version` | 是 | SemVer 版本号 |
| `author` | 是 | 作者名称 |
| `min_fmcl_version` | 是 | 最低 FMCL 版本 |
| `description` | 是 | 多语言描述，至少 `zh_CN` 和 `en_US` |
| `permissions` | 是 | 诚实填写，申请最小权限 |
| `tags` | 是 | 至少一个分类标签 |
| `license` | 是 | SPDX 许可证标识 |
| `dependencies` | 否 | 依赖的其他插件 |
| `conflicts` | 否 | 冲突的插件 |
| `homepage` | 否 | 项目主页 |
| `icon` | 否 | 图标文件名 |
| `entry` | 否 | 入口模块，默认 `__init__` |

#### __init__.py（必需）

入口模块必须导出一个继承自 `PluginBase` 的类。详见 [docs/PLUGIN_DEV.md](docs/PLUGIN_DEV.md)。

#### icon.png（推荐）

128×128 PNG 图标。无图标时显示默认插件图标。

### 4. 本地测试

```bash
# 在插件目录下打包
cd com.yourname.plugin-id
zip -r ../com.yourname.plugin-id.fmpl .
cd ..
# 将 .fmpl 文件放入 FMCL 测试
```

### 5. 创建 Release 并附带 .fmpl

1. 在 GitHub 仓库 Releases 页面创建新 Release
2. Tag 版本号格式：`com.yourname.plugin-id/v1.0.0`
3. 将 `.fmpl` 文件作为 Release 附件上传
4. Release 标题使用 `插件名 - v版本号` 格式

### 6. 提交 Pull Request

1. 将插件目录提交到你的 Fork
2. 发起 Pull Request 到主仓库的 `main` 分支
3. PR 标题格式：`[新插件] com.yourname.plugin-id`
4. PR 描述中说明插件功能

### 7. 审核

维护者将审核以下方面：

- [ ] 插件 ID 唯一且符合命名规范
- [ ] `plugin.json` 字段完整且合法
- [ ] 请求的权限最小且必要
- [ ] 代码无恶意行为
- [ ] 至少提供中英文描述
- [ ] Release 已创建且 `.fmpl` 已上传

## 标签分类

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

## 版本号规范

使用 [SemVer 2.0.0](https://semver.org/lang/zh-CN/)：

```
主版本号.次版本号.修订号[-预发布标签]
```

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修复

## 更新插件

1. 修改插件代码和 `plugin.json` 中的 `version` 字段
2. 创建对应版本号的新 Release
3. 在 PR 中说明更新内容

---

如有疑问，请在 [Discussions](https://github.com/Janson20/FMCL-Plugins/discussions) 中提问。
