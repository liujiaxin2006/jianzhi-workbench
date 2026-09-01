#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻盈工作台 · App 图标生成器（Apple 风格）"""
from PIL import Image, ImageDraw
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(BASE, 'icons')
os.makedirs(ICONS, exist_ok=True)

S = 1024        # 绘制基准尺寸
G = 512         # 渐变源图尺寸（足够大，放大仍平滑）

def lut3(a, b, c):
    """0..255 亮度 -> 三段色 stop 的查找表"""
    out = []
    for i in range(256):
        t = i / 255.0
        if t < 0.5:
            u = t / 0.5
            v = a + (b - a) * u
        else:
            u = (t - 0.5) / 0.5
            v = b + (c - b) * u
        out.append(round(v))
    return out

# ---- 1. 对角渐变：绿(#30d158) -> 青(#0fd6a8) -> 蓝(#0a84ff) ----
green = (48, 209, 88)
teal  = (15, 214, 168)
blue  = (10, 132, 255)

grad = Image.new('L', (G, G))
gpx = grad.load()
for y in range(G):
    for x in range(G):
        gpx[x, y] = round((x + y) / (2 * G) * 255)   # 左上 0 -> 右下 255

grad = grad.resize((S, S), Image.BICUBIC)
r = grad.point(lut3(green[0], teal[0], blue[0]))
g = grad.point(lut3(green[1], teal[1], blue[1]))
b = grad.point(lut3(green[2], teal[2], blue[2]))
img = Image.merge('RGB', (r, g, b)).convert('RGBA')

# ---- 2. 白色同心环（对应 App 头部宏环 58/43/28 比例）----
draw = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
STROKE = int(0.062 * S)   # 环粗

def ring(rad_norm):
    rad = rad_norm * S
    draw.ellipse([S/2 - rad, S/2 - rad, S/2 + rad, S/2 + rad],
                 outline=white, width=STROKE)

ring(0.410)   # 外环
ring(0.305)   # 中环
ring(0.200)   # 内环

# ---- 3. 输出各尺寸 ----
def save(img, path, size):
    out = img.resize((size, size), Image.LANCZOS)
    out.save(path, 'PNG')
    print('saved', os.path.relpath(path, BASE), out.size)

save(img, os.path.join(ICONS, 'icon-512.png'), 512)
save(img, os.path.join(ICONS, 'icon-192.png'), 192)
save(img, os.path.join(ICONS, 'apple-touch-icon.png'), 180)
save(img, os.path.join(ICONS, 'favicon.png'), 64)

# ---- 4. 验证抽样 ----
print('--- 像素抽样 (RGBA) ---')
print('左上', img.getpixel((6, 6)))
print('右上', img.getpixel((S-6, 6)))
print('左下', img.getpixel((6, S-6)))
print('右下', img.getpixel((S-6, S-6)))
print('中心', img.getpixel((S//2, S//2)))
print('外环顶点', img.getpixel((S//2, S//2 - int(0.410*S))))
print('外环上方背景', img.getpixel((S//2, S//2 - int(0.41*S + 0.07*S))))
