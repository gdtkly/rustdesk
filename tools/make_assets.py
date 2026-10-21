#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连连控远程 - 品牌素材生成器
一次性生成本项目需要的全部图标 / LOGO 资源。

用法:
    python tools/make_assets.py

设计说明（图形语言）:
    渐变圆角方块 + 白色鼠标指针 + 右上两道信号弧
    = "远程操控"（指针即操控，弧线即远程信号）

输出目录: ./branding/assets/
以后拿到正式 LOGO，把 brand.json 的 logo_source 指到你的 PNG(1024x1024)，
重新跑本脚本即可全套替换；也可以直接覆盖 branding/assets 下的文件。
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRAND = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "branding", "assets")


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lighten(c, k):
    return tuple(min(255, int(v + (255 - v) * k)) for v in c)


def darken(c, k):
    return tuple(max(0, int(v * (1 - k))) for v in c)


PRIMARY = hexrgb(BRAND["brand_color"])
GRAD_TOP = lighten(PRIMARY, 0.18)
GRAD_BOTTOM = darken(PRIMARY, 0.22)
WHITE = (255, 255, 255)
DARK = (30, 33, 38)

# ---- 造型参数（归一化到 0~1，坐标系 y 向下）----
RADIUS_RATIO = 0.225

# 鼠标指针（经典箭头），原始比例
_CURSOR_RAW = [
    (0.00, 0.00), (0.00, 0.76), (0.21, 0.58), (0.31, 0.83),
    (0.45, 0.77), (0.35, 0.53), (0.55, 0.53),
]
MARK_SIZE = 0.54          # 标记占方块边长的比例


def _center_polygon(raw, target):
    """把原始多边形等比缩放并居中到单位方块内，返回归一化顶点"""
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    k = target / max(w, h)
    ox = (1 - w * k) / 2 - min(xs) * k
    oy = (1 - h * k) / 2 - min(ys) * k
    return [(x * k + ox, y * k + oy) for x, y in raw]


CURSOR = _center_polygon(_CURSOR_RAW, MARK_SIZE)

FONT_BOLD = None
for cand in [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]:
    if os.path.exists(cand):
        FONT_BOLD = cand
        break


def cursor_points(s):
    """返回指针多边形顶点（像素坐标）"""
    return [(x * s, y * s) for x, y in CURSOR]


def draw_mark(d, s):
    """在超采样画布上画白色标记"""
    d.polygon(cursor_points(s), fill=WHITE + (255,))


def rounded_tile(size, radius_ratio=RADIUS_RATIO):
    """主图标：渐变圆角方块 + 白色指针标记"""
    S = 8
    s = size * S
    # 渐变底
    grad = Image.new("RGB", (1, s))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        t = y / max(1, s - 1)
        gd.point((0, y), tuple(int(GRAD_TOP[i] + (GRAD_BOTTOM[i] - GRAD_TOP[i]) * t) for i in range(3)))
    grad = grad.resize((s, s))

    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(s * radius_ratio), fill=255)

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    draw_mark(ImageDraw.Draw(img), s)
    return img.resize((size, size), Image.LANCZOS)


def lockup(width=300, height=60, text_color=DARK, with_tile=True):
    """横向组合 LOGO：图标 + 产品名（Flutter 首页上限 300x60）"""
    S = 4
    W, H = width * S, height * S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    tile_size = int(H * 0.90)
    ty = (H - tile_size) // 2
    if with_tile:
        img.alpha_composite(rounded_tile(tile_size, 0.24), (0, ty))
        tx = tile_size + int(H * 0.22)
    else:
        tx = 0

    name = BRAND["app_name"]
    fs = int(H * 0.62)
    font = ImageFont.truetype(FONT_BOLD, fs) if FONT_BOLD else ImageFont.load_default()
    bbox = d.textbbox((0, 0), name, font=font)
    d.text((tx, (H - (bbox[3] - bbox[1])) // 2 - bbox[1]), name,
           font=font, fill=text_color + (255,))
    return img.resize((width, height), Image.LANCZOS)


def mark_svg(size=256):
    """与位图同构的矢量版本"""
    s = size
    top = "#%02X%02X%02X" % GRAD_TOP
    bot = "#%02X%02X%02X" % GRAD_BOTTOM
    poly = " ".join(f"{x * s:.2f},{y * s:.2f}" for x, y in CURSOR)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 {s} {s}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/>
      <stop offset="1" stop-color="{bot}"/>
    </linearGradient>
  </defs>
  <rect width="{s}" height="{s}" rx="{s * RADIUS_RATIO:.1f}" ry="{s * RADIUS_RATIO:.1f}" fill="url(#g)"/>
  <polygon points="{poly}" fill="#ffffff"/>
</svg>
'''


def save_ico(img, path, sizes):
    img.save(path, format="ICO", sizes=[(s, s) for s in sizes])


def main():
    logo_src = BRAND.get("logo_source", "")
    if logo_src and os.path.exists(logo_src):
        print("使用自定义 logo_source:", logo_src)
        master = Image.open(logo_src).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    else:
        master = rounded_tile(1024)

    dirs = {
        "res": os.path.join(OUT, "res"),
        "flutter": os.path.join(OUT, "flutter"),
        "runner": os.path.join(OUT, "runner"),
        "portable": os.path.join(OUT, "portable"),
    }
    for p in dirs.values():
        os.makedirs(p, exist_ok=True)

    # --- res/ (Windows / Linux 图标) ---
    master.resize((32, 32), Image.LANCZOS).save(os.path.join(dirs["res"], "32x32.png"))
    master.resize((64, 64), Image.LANCZOS).save(os.path.join(dirs["res"], "64x64.png"))
    master.resize((128, 128), Image.LANCZOS).save(os.path.join(dirs["res"], "128x128.png"))
    master.resize((256, 256), Image.LANCZOS).save(os.path.join(dirs["res"], "128x128@2x.png"))
    master.save(os.path.join(dirs["res"], "icon.png"))              # 1024
    master.resize((1024, 1024), Image.LANCZOS).save(os.path.join(dirs["res"], "mac-icon.png"))
    save_ico(master, os.path.join(dirs["res"], "icon.ico"), [16, 24, 32, 48, 64, 128, 256])
    save_ico(master, os.path.join(dirs["res"], "tray-icon.ico"), [16, 20, 24, 32])
    open(os.path.join(dirs["res"], "logo.svg"), "w", encoding="utf-8").write(mark_svg(256))
    open(os.path.join(dirs["res"], "scalable.svg"), "w", encoding="utf-8").write(mark_svg(512))

    # --- Flutter runner exe 图标 ---
    save_ico(master, os.path.join(dirs["runner"], "app_icon.ico"), [16, 24, 32, 48, 64, 128, 256])

    # --- Flutter 应用内资源 ---
    master.resize((256, 256), Image.LANCZOS).save(os.path.join(dirs["flutter"], "icon.png"))
    open(os.path.join(dirs["flutter"], "icon.svg"), "w", encoding="utf-8").write(mark_svg(256))
    lockup(300, 60, DARK).save(os.path.join(dirs["flutter"], "logo.png"))
    lockup(300, 60, DARK).save(os.path.join(dirs["flutter"], "logo_light.png"))
    lockup(300, 60, WHITE).save(os.path.join(dirs["flutter"], "logo_dark.png"))

    # --- 自解压安装器窗口上的小标签（源码固定 96x32）---
    lab = Image.new("RGBA", (96 * 4, 32 * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(lab)
    lab.alpha_composite(rounded_tile(32 * 4, 0.24), (0, 0))
    fs = int(32 * 4 * 0.44)
    font = ImageFont.truetype(FONT_BOLD, fs) if FONT_BOLD else ImageFont.load_default()
    d.text((32 * 4 + 6, int((32 * 4 - fs) / 2) - 3), BRAND["app_name_short"],
           font=font, fill=DARK + (255,))
    lab.resize((96, 32), Image.LANCZOS).save(os.path.join(dirs["portable"], "label.png"))

    print("资源已生成 ->", OUT)
    for k, v in dirs.items():
        print(" ", k, sorted(os.listdir(v)))


if __name__ == "__main__":
    main()
