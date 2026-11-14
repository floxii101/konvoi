"""Konvoi promo video renderer: PIL frames -> ffmpeg (H.264, 1080x1920, 30 fps)."""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
def F(name, size): return ImageFont.truetype(FD + name, size)
BLACK = F('InterDisplay-Black.otf', 1)  # warm cache

LIME = (198, 244, 50); BG = (8, 9, 12); WHITE = (244, 246, 248); MUTED = (152, 161, 173)
ORANGE = (255, 138, 61); BLUE = (77, 163, 255); PINK = (255, 95, 162); AMBER = (255, 181, 71); RED = (255, 107, 74)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, b): return clamp((t - a) / (b - a))

# ---------- background ----------
def make_bg():
    bg = Image.new('RGB', (W, H), BG)
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([520, -420, 1500, 560], fill=(46, 58, 10))
    g.ellipse([-520, 520, 420, 1460], fill=(12, 30, 52))
    g.ellipse([300, 1500, 1300, 2400], fill=(28, 34, 8))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    return Image.blend(bg, glow, 1.0).point(lambda v: v)  # glow already dark
BGIMG = None
def bg_frame(t):
    global BGIMG
    if BGIMG is None:
        base = Image.new('RGB', (W, H), BG)
        glow = make_bg()
        BGIMG = Image.composite(glow, base, Image.new('L', (W, H), 255))
        # faint grid
        d = ImageDraw.Draw(BGIMG)
        for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(14, 16, 20), width=1)
        for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(14, 16, 20), width=1)
    return BGIMG.copy()

# ---------- text ----------
def text_w(font, s): return font.getlength(s)
def draw_text_center(img, y, segments, size, font='InterDisplay-Black.otf', alpha=1.0, dy=0, tracking=0):
    """segments: list of (text, color). Centered line."""
    f = F(font, size)
    total = sum(text_w(f, s) for s, _ in segments)
    layer = Image.new('RGBA', (W, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = (W - total) / 2
    for s, c in segments:
        d.text((x, size * 0.3), s, font=f, fill=c + (255,))
        x += text_w(f, s)
    if alpha < 1:
        a = layer.split()[3].point(lambda v: int(v * alpha)); layer.putalpha(a)
    img.paste(layer, (0, int(y + dy - size * 0.3)), layer)

def word_reveal(img, t, t0, y, words, size, stagger=0.09, dur=0.45, font='InterDisplay-Black.otf'):
    """words: list of (word, color). Each word slides up + fades in, centered line."""
    f = F(font, size)
    space = text_w(f, ' ')
    widths = [text_w(f, w) for w, _ in words]
    total = sum(widths) + space * (len(words) - 1)
    x = (W - total) / 2
    for i, (w, c) in enumerate(words):
        p = ease_out(prog(t, t0 + i * stagger, t0 + i * stagger + dur))
        if p > 0:
            layer = Image.new('RGBA', (int(widths[i]) + 20, int(size * 1.6)), (0, 0, 0, 0))
            ImageDraw.Draw(layer).text((0, size * 0.15), w, font=f, fill=c + (255,))
            layer.putalpha(layer.split()[3].point(lambda v: int(v * p)))
            img.paste(layer, (int(x), int(y + (1 - p) * size * 0.7)), layer)
        x += widths[i] + space

# ---------- phone ----------
SCREEN_W = 700
def load_phone(path):
    sc = Image.open(path).convert('RGB')
    sh = int(SCREEN_W * sc.height / sc.width)
    sc = sc.resize((SCREEN_W, sh), Image.LANCZOS)
    bez = 18; r = 86
    pw, ph = SCREEN_W + bez * 2, sh + bez * 2
    phone = Image.new('RGBA', (pw + 120, ph + 120), (0, 0, 0, 0))
    # shadow
    sh_l = Image.new('L', phone.size, 0)
    ImageDraw.Draw(sh_l).rounded_rectangle([60, 80, 60 + pw, 80 + ph], radius=r + 10, fill=170)
    sh_l = sh_l.filter(ImageFilter.GaussianBlur(36))
    phone.paste((0, 0, 0, 255), (0, 0), sh_l)
    d = ImageDraw.Draw(phone)
    d.rounded_rectangle([60, 60, 60 + pw, 60 + ph], radius=r + 10, fill=(26, 28, 33, 255), outline=(58, 62, 70, 255), width=3)
    mask = Image.new('L', sc.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sc.width - 1, sc.height - 1], radius=r - 8, fill=255)
    phone.paste(sc, (60 + bez, 60 + bez), mask)
    # dynamic island
    d.rounded_rectangle([60 + pw / 2 - 70, 60 + bez + 16, 60 + pw / 2 + 70, 60 + bez + 56], radius=20, fill=(0, 0, 0, 255))
    return phone, (60 + bez, 60 + bez), sc.size

def place_phone(img, phone, cx, top, scale=1.0, alpha=1.0, rot=0):
    ph = phone
    if scale != 1.0:
        ph = ph.resize((int(ph.width * scale), int(ph.height * scale)), Image.BILINEAR)
    if rot:
        ph = ph.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        ph = ph.copy(); ph.putalpha(ph.split()[3].point(lambda v: int(v * alpha)))
    img.paste(ph, (int(cx - ph.width / 2), int(top)), ph)
    return (int(cx - ph.width / 2), int(top), scale)

def crossfade_phone(img, a, b, p, cx, top, scale=1.0):
    if p <= 0: return place_phone(img, a, cx, top, scale)
    if p >= 1: return place_phone(img, b, cx, top, scale)
    mix = Image.blend(a, b, p)
    return place_phone(img, mix, cx, top, scale)

def ripple(img, x, y, p, color=WHITE):
    if p <= 0 or p >= 1: return
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    r = 20 + 90 * ease_out(p); a = int(200 * (1 - p))
    d.ellipse([x - r, y - r, x + r, y + r], outline=color + (a,), width=8)
    r2 = 26 * (1 - p * 0.5)
    d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=color + (int(150 * (1 - p)),))
    img.paste(layer, (0, 0), layer)

def pill(img, x, y, txt, color, p, size=40, fg=(11, 13, 16)):
    if p <= 0: return
    f = F('Inter-ExtraBold.otf', size)
    tw = text_w(f, txt); pw, ph = int(tw + size * 1.3), int(size * 1.9)
    s = back_out(p)
    layer = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2, fill=color + (255,))
    d.text((size * 0.65, ph / 2), txt, font=f, fill=fg + (255,), anchor='lm')
    if s != 1: layer = layer.resize((max(1, int(pw * s)), max(1, int(ph * s))), Image.BILINEAR)
    layer.putalpha(layer.split()[3].point(lambda v: int(v * clamp(p * 2))))
    img.paste(layer, (int(x - layer.width / 2), int(y - layer.height / 2)), layer)

def app_icon(size):
    S = size * 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.24), fill=LIME + (255,))
    pts = [(3, 12), (7, 12), (10, 5), (14, 19), (17, 12), (21, 12)]
    sc = S / 24 * 0.74; off = S * 0.13
    P = [(off + x * sc, off + y * sc) for x, y in pts]
    d.line(P, fill=(11, 13, 16, 255), width=int(S * 0.075), joint='curve')
    rr = S * 0.037
    for x, y in (P[0], P[-1]): d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(11, 13, 16, 255))
    return im.resize((size, size), Image.LANCZOS)

# ---------- hook scene: friends drifting apart ----------
def hook_dots(img, t, t0, t1):
    p = prog(t, t0, t1)
    d = ImageDraw.Draw(img)
    # road curve
    pts = [(x, 1250 + math.sin(x / 210) * 120) for x in range(-40, W + 60, 20)]
    d.line(pts, fill=(30, 35, 44), width=40, joint='curve')
    d.line(pts, fill=(46, 52, 62), width=6, joint='curve')
    def at(x): return (x, 1250 + math.sin(x / 210) * 120)
    lead = 300 + 520 * ease_in_out(p)
    cars = [(lead, LIME), (lead - 120, ORANGE), (lead - 230, BLUE), (lead - 130 - 380 * ease_in_out(p) - 150 * p, PINK)]
    for x, c in cars:
        cx, cy = at(x)
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=c, outline=BG, width=7)
    # question mark over lagging car
    if p > 0.45:
        cx, cy = at(cars[3][0])
        pill(img, cx, cy - 95, '?', PINK, prog(t, t0 + (t1 - t0) * 0.45, t0 + (t1 - t0) * 0.6), size=44)

# ---------- main video ----------
def render(out, scenes_fn, duration):
    n = int(duration * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        img = scenes_fn(t)
        pr.stdin.write(img.convert('RGB').tobytes())
        if i % 60 == 0: print(out, f'{t:.1f}s', file=sys.stderr)
    pr.stdin.close(); pr.wait()
