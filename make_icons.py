#!/usr/bin/env python3
"""生成「轻盈工作台」PWA 图标：渐变圆角底 + 白色营养环 + 中央叶子"""
import math
from PIL import Image, ImageDraw, ImageFilter

S = 512  # master size

# ---------- 1. 渐变圆角背景 ----------
grad = Image.new("RGB", (S, S))
gd = grad.load()
c1 = (0x00, 0x71, 0xE3)  # blue #0071e3
c2 = (0x1D, 0x9B, 0x62)  # green #1d9b62
for y in range(S):
    t = y / (S - 1)
    # 垂直渐变，右上略亮
    for x in range(S):
        g = (x / (S - 1)) * 0.35 + t * 0.65
        r = int(c1[0] + (c2[0] - c1[0]) * g)
        gg = int(c1[1] + (c2[1] - c1[1]) * g)
        b = int(c1[2] + (c2[2] - c1[2]) * g)
        gd[x, y] = (r, gg, b)

# 圆角遮罩
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
radius = int(S * 0.225)
md.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)
base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
base.paste(grad, (0, 0), mask)

# ---------- 2. 白色营养环（进度环，缺口朝下偏左） ----------
draw = ImageDraw.Draw(base)
cx, cy = S / 2, S / 2
R = S * 0.295           # 环半径
w = S * 0.115           # 环宽
box = [cx - R, cy - R, cx + R, cy + R]
# 从 95° 画到 405°（即 45°），形成 310° 的弧
draw.arc(box, start=95, end=405, fill=(255, 255, 255, 255), width=int(w))

# 环上三个小圆点作为进度刻度
dot_r = S * 0.026
for ang in (115, 250, 385):
    a = math.radians(ang)
    px, py = cx + R * math.cos(a), cy + R * math.sin(a)
    draw.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r], fill=(255, 255, 255, 255))

# ---------- 3. 中央叶子（贝塞尔构成的叶片） ----------
def quad(p0, p1, p2, steps=48):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts

leaf_w, leaf_h = S * 0.13, S * 0.235
tip = (cx, cy - leaf_h / 2)          # 叶尖
base_pt = (cx, cy + leaf_h / 2)      # 叶柄端
left_ctrl = (cx - leaf_w, cy)        # 左侧控制点
right_ctrl = (cx + leaf_w, cy)       # 右侧控制点

left = quad(base_pt, left_ctrl, tip)
right = quad(tip, right_ctrl, base_pt)
draw.polygon(left + right[1:], fill=(255, 255, 255, 255))

# 中央叶脉（细线）
draw.line([(cx, cy - leaf_h * 0.30), (cx, cy + leaf_h * 0.28)],
          fill=(0x1D, 0x9B, 0x62, 255), width=int(S * 0.012))

# 轻微柔化边缘
base = base.filter(ImageFilter.GaussianBlur(0.6))

# ---------- 4. 导出 ----------
out_dir = r"C:\Users\jiaxi\WorkBuddy\Claw\jianzhi-workbench\icons"
import os
os.makedirs(out_dir, exist_ok=True)

def save(size, path):
    im = base.resize((size, size), Image.LANCZOS)
    im.save(path, "PNG")

save(512, os.path.join(out_dir, "icon-512.png"))
save(192, os.path.join(out_dir, "icon-192.png"))
save(180, os.path.join(out_dir, "apple-touch-icon.png"))
save(64, os.path.join(out_dir, "favicon.png"))
print("icons generated:", os.listdir(out_dir))
