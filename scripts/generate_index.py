#!/usr/bin/env python3
"""FMCL 插件市场 index.json 自动生成脚本

从 plugins/ 目录读取所有插件的 plugin.json，
生成统一的 index.json 索引文件。

用法:
    python scripts/generate_index.py [--repo Janson20/FMCL-Plugins]

前提:
    - plugins/ 目录存在，每个子目录为一个插件
    - 每个插件目录包含 plugin.json

输出:
    - index.json: 覆盖写入仓库根目录
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


# 插件 ID 正则要求
PLUGIN_ID_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_\-.]*$"

# 分类标签（用于 UI 筛选）
KNOWN_TAGS = {
    "utility": "实用工具",
    "ui": "UI 扩展",
    "gameplay": "游戏体验",
    "server": "服务器相关",
    "modpack": "整合包相关",
    "performance": "性能优化",
    "backup": "备份还原",
    "theme": "主题美化",
    "automation": "自动化",
    "integration": "第三方集成",
}

# 必需字段
REQUIRED_FIELDS = ["id", "name", "version", "author", "min_fmcl_version", "permissions", "tags", "license"]


def _validate_plugin(manifest: dict, plugin_id: str) -> List[str]:
    """校验单个插件清单，返回错误列表"""
    errors = []

    # 检查必需字段
    for field in REQUIRED_FIELDS:
        if field not in manifest or not manifest[field]:
            errors.append(f"缺少必需字段: {field}")

    # 检查 ID 一致性
    if manifest.get("id") != plugin_id:
        errors.append(f"plugin.json 中的 id ({manifest.get('id')}) 与目录名 ({plugin_id}) 不一致")

    # 检查 SemVer
    import re
    version = manifest.get("version", "")
    if not re.match(r"^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$", version):
        errors.append(f"版本号 '{version}' 不符合 SemVer 规范")

    # 检查描述至少有中英文之一
    desc = manifest.get("description", {})
    if not isinstance(desc, dict) or not (desc.get("zh_CN") or desc.get("en_US")):
        errors.append("description 至少需要 zh_CN 或 en_US")

    # 检查标签是否合法
    tags = manifest.get("tags", [])
    for tag in tags:
        if tag not in KNOWN_TAGS:
            # 不阻塞，只做警告
            print(f"  [WARN] {plugin_id}: 未知标签 '{tag}'", file=sys.stderr)

    # 检查许可证
    license_val = manifest.get("license", "")
    if not license_val:
        errors.append("缺少 license 字段")

    return errors


def generate_index(plugins_dir: Path, repo: str) -> Dict[str, Any]:
    """生成插件市场索引

    Args:
        plugins_dir: plugins/ 目录路径
        repo: GitHub 仓库全名，如 Janson20/FMCL-Plugins

    Returns:
        index.json 字典
    """
    if not plugins_dir.exists():
        print(f"ERROR: plugins/ 目录不存在: {plugins_dir}", file=sys.stderr)
        sys.exit(1)

    plugins: List[Dict[str, Any]] = []
    stats = {"total": 0, "valid": 0, "warning": 0, "errors": 0}
    errors_detail: List[Dict[str, Any]] = []

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue

        plugin_json = plugin_dir / "plugin.json"
        if not plugin_json.exists():
            print(f"  [SKIP] {plugin_dir.name}: 缺少 plugin.json", file=sys.stderr)
            continue

        stats["total"] += 1
        plugin_id = plugin_dir.name

        try:
            with open(plugin_json, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            errors_detail.append({
                "plugin_id": plugin_id,
                "errors": [f"JSON 解析失败: {e}"],
            })
            stats["errors"] += 1
            continue

        # 校验
        errors = _validate_plugin(manifest, plugin_id)
        if errors:
            errors_detail.append({
                "plugin_id": plugin_id,
                "errors": errors,
            })
            stats["errors"] += 1
            continue

        # 构建索引条目（包含足够用于 UI 展示的信息）
        entry = {
            "id": manifest["id"],
            "name": manifest["name"],
            "version": manifest["version"],
            "author": manifest["author"],
            "min_fmcl_version": manifest["min_fmcl_version"],
            "max_fmcl_version": manifest.get("max_fmcl_version"),
            "description": manifest.get("description", {}),
            "permissions": manifest.get("permissions", []),
            "dependencies": manifest.get("dependencies", {}),
            "tags": manifest.get("tags", []),
            "homepage": manifest.get("homepage", ""),
            "license": manifest.get("license", ""),
            "icon": manifest.get("icon", ""),
            # 下载信息（由 Release 提供）
            "download": {
                "repo": repo,
                "tag_prefix": f"{plugin_id}/v",
                "filename": f"{plugin_id}.fmpl",
            },
        }
        plugins.append(entry)
        stats["valid"] += 1
        print(f"  [OK] {plugin_id} v{manifest['version']}")

    # 按名称排序
    plugins.sort(key=lambda p: p["name"].lower())

    # 如果存在旧的 index.json，保留一些元数据
    old_update_time = None
    index_path = plugins_dir.parent / "index.json"
    if index_path.exists():
        try:
            old = json.loads(index_path.read_text(encoding="utf-8"))
            old_update_time = old.get("generated_at", None)
        except Exception:
            pass

    import datetime
    generated_at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    index = {
        "meta": {
            "name": "FMCL Plugins Index",
            "version": "1.0",
            "schema_version": 1,
            "generated_at": generated_at,
            "repo": repo,
            "base_url": f"https://github.com/{repo}",
        },
        "categories": KNOWN_TAGS,
        "stats": {
            "total_plugins": len(plugins),
            "last_updated": generated_at,
        },
        "plugins": plugins,
    }

    if errors_detail:
        index["_validation_errors"] = errors_detail

    return index


def main():
    parser = argparse.ArgumentParser(
        description="生成 FMCL 插件市场 index.json",
    )
    parser.add_argument(
        "--repo",
        default="Janson20/FMCL-Plugins",
        help="GitHub 仓库全名 (默认: Janson20/FMCL-Plugins)",
    )
    parser.add_argument(
        "--plugins-dir",
        default=None,
        help="plugins/ 目录路径 (默认: 脚本所在目录同级 plugins/ )",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径 (默认: 脚本所在目录同级的 index.json)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅校验，不写入文件 (用于 CI 检查)",
    )
    args = parser.parse_args()

    # 确定路径
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    plugins_dir = Path(args.plugins_dir) if args.plugins_dir else repo_root / "plugins"
    output_path = Path(args.output) if args.output else repo_root / "index.json"

    print(f"FMCL Plugin Index Generator", file=sys.stderr)
    print(f"  Plugins: {plugins_dir}", file=sys.stderr)
    print(f"  Output:  {output_path}", file=sys.stderr)
    print(f"  Repo:    {args.repo}", file=sys.stderr)
    print(file=sys.stderr)

    index = generate_index(plugins_dir, args.repo)

    if args.check:
        # 仅校验模式：检查是否有错误
        error_count = index.get("_validation_errors", [])
        if error_count:
            print(f"\nERROR: {len(error_count)} 个插件校验失败", file=sys.stderr)
            for e in error_count:
                print(f"  - {e['plugin_id']}: {'; '.join(e['errors'])}", file=sys.stderr)
            sys.exit(1)
        else:
            total = index["meta"].get("total_plugins", len(index.get("plugins", [])))
            print(f"\nOK: {total} 个插件校验通过", file=sys.stderr)
            sys.exit(0)

    # 写入
    output_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nindex.json 已生成: {output_path}", file=sys.stderr)
    total = index["stats"]["total_plugins"]
    print(f"共 {total} 个插件", file=sys.stderr)

    if "_validation_errors" in index:
        print(f"WARNING: 有 {len(index['_validation_errors'])} 个插学校验未通过，已记录到 _validation_errors 字段", file=sys.stderr)


if __name__ == "__main__":
    main()
