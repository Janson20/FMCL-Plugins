# 插件市场提交指南

> 本文档详细说明如何将插件提交到 FMCL 官方插件市场。

---

## 前置条件

1. GitHub 账号
2. 已完成的 FMCL 插件（包含 `plugin.json` 和 `__init__.py`）
3. 插件已通过本地测试

## 提交流程

### 1. 准备插件

确保你的插件目录结构如下：

```
com.yourname.plugin-id/
├── plugin.json         # 必需
├── __init__.py         # 必需，包含 PluginBase 子类
└── icon.png            # 推荐，128x128
```

### 2. 打包 .fmpl

将插件目录打包为 `.fmpl` 文件：

**Windows PowerShell:**
```powershell
Compress-Archive -Path com.yourname.plugin-id/* -DestinationPath com.yourname.plugin-id.fmpl
```

**Linux/macOS:**
```bash
cd com.yourname.plugin-id && zip -r ../com.yourname.plugin-id.fmpl .
```

### 3. 创建 GitHub Release

在你的 Fork 仓库中：

1. 进入 **Releases** → **Create a new release**
2. 设置 Tag 版本号：
   ```
   com.yourname.plugin-id/v1.0.0
   ```
   格式必须为 `{插件ID}/v{版本号}`
3. 填写 Release 标题：
   ```
   你的插件名称 - v1.0.0
   ```
4. 将 `.fmpl` 文件作为附件上传
5. 在描述中说明插件功能和更新内容
6. 发布 Release

### 4. 提交 Pull Request

1. 在 `plugins/` 目录下创建你的插件文件夹
2. 将 `plugin.json` 和 `__init__.py` 放入该文件夹
3. 提交 PR 到 `Janson20/FMCL-Plugins` 的 `main` 分支

**PR 标题格式:**
```
[新插件] com.yourname.plugin-id
```

**PR 描述模板:**
```markdown
## 插件信息

- **名称**: 你的插件名称
- **版本**: 1.0.0
- **功能介绍**: （简要描述插件功能）

## 所需权限

- `ui.notification` - 用于显示操作通知
- `data.store` - 用于保存用户配置

## 测试说明

已在 FMCL v2.11.0 上测试通过。

## 截图

（可选，粘贴插件截图链接）
```

### 5. 审核通过

维护者审核通过后，CI 会自动将你的插件信息更新到 `index.json`，用户即可在 FMCL 插件管理中找到你的插件。

---

## 版本更新流程

当你的插件有更新时：

1. 修改 `plugin.json` 中的 `version` 字段
2. 创建新的 Release（Tag: `com.yourname.plugin-id/v新版本号`）
3. 将新的 `.fmpl` 上传到 Release
4. 提交 PR 更新 `plugins/` 中的源文件

**更新 PR 标题格式:**
```
[更新] com.yourname.plugin-id → v1.1.0
```

---

## 插件下架

如果需要下架插件，提交 PR 删除 `plugins/` 中对应的目录，并在 PR 中说明原因。

---

## Release Tag 规范

FMCL 客户端通过以下规则查找插件的下载地址：

```
https://github.com/Janson20/FMCL-Plugins/releases/download/{tag}/{filename}
```

- **tag**: 必须为 `{插件ID}/v{版本号}` 格式
- **filename**: 与插件 ID 同名，如 `com.yourname.plugin-id.fmpl`

正确示例：
- Tag: `com.fmcl.auto-backup/v1.0.0`
- 文件名: `com.fmcl.auto-backup.fmpl`
- 完整 URL: `https://github.com/Janson20/FMCL-Plugins/releases/download/com.fmcl.auto-backup/v1.0.0/com.fmcl.auto-backup.fmpl`

---

## 常见问题

### Q: 我的插件可以只提供源码（不打包 .fmpl）吗？

A: 不可以。市场分发基于 `.fmpl` 文件，必须创建 Release 并上传。

### Q: 可以一个 Release 包含多个版本的 .fmpl 吗？

A: 不可以。每个版本需要单独的 Release，Tag 格式为 `{插件ID}/v{版本号}`。

### Q: 我的插件依赖其他插件，如何声明？

A: 在 `plugin.json` 的 `dependencies` 字段中声明：
```json
{
  "dependencies": {
    "com.other.plugin": ">=1.0.0,<2.0.0"
  }
}
```

### Q: 如何确保我的插件没被别人抢先占用 ID？

A: 在提交 PR 前，检查 `plugins/` 目录确认没有同名文件夹即可。ID 冲突会被 CI 检测到。

### Q: 审核需要多久？

A: 一般在 1-3 个工作日内完成。如果是紧急安全修复，请在 PR 标题中标记 `[URGENT]`。
