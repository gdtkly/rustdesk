#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连连控远程 —— RustDesk 源码品牌化补丁

在 rustdesk 源码根目录执行：
    python branding/apply_branding.py

它做四件事：
 1. 改应用名  -> hbb_common/config.rs 的 APP_NAME（窗口标题、安装目录、快捷方式、翻译文案都会跟着变）
 2. 写死自建服务器 -> RENDEZVOUS_SERVERS + RS_PUB_KEY
 3. 换 Windows 版本信息（公司名/产品名/版权/描述）
 4. 换主题主色，并把 branding/assets 下的图标复制到对应位置

任何一处没匹配上都会立刻报错退出（避免"编译成功但没换掉"的静默失败）。
"""
import json
import os
import re
import shutil
import sys

ROOT = os.getcwd()
BRAND_FILE = os.path.join(ROOT, "brand.json")
ASSETS = os.path.join(ROOT, "branding", "assets")

changed = []
failed = []


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def sub(path, pattern, repl, label, count=1, flags=re.M):
    """正则替换，必须命中"""
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        failed.append(f"{label}: 文件不存在 {path}")
        return
    src = read(p)
    new, n = re.subn(pattern, repl, src, count=count, flags=flags)
    if n == 0:
        failed.append(f"{label}: 未匹配到目标内容 ({path})")
        return
    if new != src:
        write(p, new)
        changed.append(f"{label}  -> {path}")


def main():
    brand = json.load(open(BRAND_FILE, encoding="utf-8"))
    app_name = brand["app_name"]
    company = brand["company_name"]
    copyright_ = brand["copyright"]
    desc = brand["file_description"]
    ip = brand["server_ip"]
    key = brand["server_key"]
    color = brand["brand_color"].lstrip("#").upper()

    print(f"品牌: {app_name} / {company} / #{color}")
    print(f"服务器: {ip}  KEY: {key[:8]}...{key[-4:]}")

    # ---------- 1. 应用名 + 服务器 + 公钥 ----------
    sub("libs/hbb_common/src/config.rs",
        r'pub static ref APP_NAME: RwLock<String> = RwLock::new\("[^"]*"\.to_owned\(\)\);',
        f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{app_name}".to_owned());',
        "APP_NAME")

    sub("libs/hbb_common/src/config.rs",
        r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
        f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{ip}"];',
        "RENDEZVOUS_SERVERS")

    sub("libs/hbb_common/src/config.rs",
        r'pub const RS_PUB_KEY: &str = "[^"]*";',
        f'pub const RS_PUB_KEY: &str = "{key}";',
        "RS_PUB_KEY")

    # ---------- 2. Windows 版本信息 ----------
    # 2a. Cargo.toml 里 winres / bundle 段
    sub("Cargo.toml",
        r'(?m)^(\s*LegalCopyright\s*=\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{copyright_}"',
        "Cargo.toml/LegalCopyright")
    sub("Cargo.toml",
        r'(?m)^(\s*ProductName\s*=\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{app_name}"',
        "Cargo.toml/ProductName")
    sub("Cargo.toml",
        r'(?m)^(\s*FileDescription\s*=\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{desc}"',
        "Cargo.toml/FileDescription")
    # macOS bundle 显示名
    sub("Cargo.toml",
        r'(?m)^(\s*name\s*=\s*)"RustDesk"\s*$',
        lambda m: f'{m.group(1)}"{app_name}"',
        "Cargo.toml/bundle name")

    # 2b. Flutter Windows Runner 的资源（这才是最终 exe 上显示的属性）
    rc = "flutter/windows/runner/Runner.rc"
    rc_map = {
        "CompanyName": company,
        "FileDescription": desc,
        "LegalCopyright": copyright_,
        "ProductName": app_name,
        "InternalName": "rustdesk",
        "OriginalFilename": "rustdesk.exe",
    }
    for k, v in rc_map.items():
        sub(rc,
            r'(?m)^(\s*VALUE\s+"' + k + r'",\s*)"[^"]*"(\s*"\\0")',
            lambda m, v=v: f'{m.group(1)}"{v}"{m.group(2)}',
            f"Runner.rc/{k}")
    # 改成 Unicode 代码页，中文属性才不会乱码
    sub(rc, r'BLOCK "040904e4"', 'BLOCK "040904b0"', "Runner.rc/codepage block")
    sub(rc, r'VALUE "Translation", 0x409, 1252', 'VALUE "Translation", 0x409, 1200',
        "Runner.rc/translation")

    # 2c. 自解压安装器自身的属性（用户双击的那个 exe 就是它）
    pk = "libs/portable/Cargo.toml"
    for k, v in (
        ("LegalCopyright", copyright_),
        ("ProductName", app_name),
        ("FileDescription", desc),
        ("OriginalFilename", "连连控远程-安装包.exe"),
    ):
        sub(pk,
            r'(?m)^(\s*' + k + r'\s*=\s*)"[^"]*"',
            lambda m, v=v: f'{m.group(1)}"{v}"',
            f"portable/Cargo.toml/{k}")

    # ---------- 3. 主题主色 ----------
    dart = "flutter/lib/common.dart"
    r_, g_, b_ = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    hex6 = f"{r_:02X}{g_:02X}{b_:02X}"
    sub(dart,
        r'(static const Color accent = Color\(0x)[0-9A-Fa-f]{2}([0-9A-Fa-f]{6})(\);)',
        lambda m: f"{m.group(1)}FF{hex6}{m.group(3)}",
        "common.dart/accent")
    sub(dart,
        r'(static const Color accent50 = Color\(0x)[0-9A-Fa-f]{2}([0-9A-Fa-f]{6})(\);)',
        lambda m: f"{m.group(1)}77{hex6}{m.group(3)}",
        "common.dart/accent50")
    sub(dart,
        r'(static const Color accent80 = Color\(0x)[0-9A-Fa-f]{2}([0-9A-Fa-f]{6})(\);)',
        lambda m: f"{m.group(1)}AA{hex6}{m.group(3)}",
        "common.dart/accent80")
    sub(dart,
        r'(static const Color button = Color\(0x)[0-9A-Fa-f]{2}([0-9A-Fa-f]{6})(\);)',
        lambda m: f"{m.group(1)}FF{hex6}{m.group(3)}",
        "common.dart/button")
    # ID 文字颜色用主色的浅一档，保证在浅色背景上也清楚
    light = f"{min(255, r_ + 40):02X}{min(255, g_ + 40):02X}{min(255, b_ + 40):02X}"
    sub(dart,
        r'(static const Color idColor = Color\(0x)[0-9A-Fa-f]{2}([0-9A-Fa-f]{6})(\);)',
        lambda m: f"{m.group(1)}FF{light}{m.group(3)}",
        "common.dart/idColor")

    # ---------- 4. 复制图标资源 ----------
    copies = [
        ("res", "res"),
        ("flutter", "flutter/assets"),
        ("runner/app_icon.ico", "flutter/windows/runner/resources/app_icon.ico"),
        ("portable/label.png", "libs/portable/src/res/label.png"),
    ]
    for src_rel, dst_rel in copies:
        src = os.path.join(ASSETS, src_rel)
        if not os.path.exists(src):
            failed.append(f"资源缺失: {src_rel}")
            continue
        if os.path.isdir(src):
            for f in os.listdir(src):
                shutil.copy2(os.path.join(src, f), os.path.join(ROOT, dst_rel, f))
            changed.append(f"图标目录 {src_rel} -> {dst_rel} ({len(os.listdir(src))} 个文件)")
        else:
            shutil.copy2(src, os.path.join(ROOT, dst_rel))
            changed.append(f"图标 {src_rel} -> {dst_rel}")

    # ---------- 结果 ----------
    print("\n===== 已修改 =====")
    for c in changed:
        print("  ✔", c)
    if failed:
        print("\n===== 失败 =====")
        for f in failed:
            print("  ✘", f)
        print("\n补丁未全部生效，中止构建。多半是 rustdesk 版本变了，需要更新正则。")
        sys.exit(1)
    print("\n品牌化完成，可以开始编译。")


if __name__ == "__main__":
    main()
