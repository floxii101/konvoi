import sys
sys.path.insert(0, '/tmp/promo')
from render import *

phones = {n: load_phone(f'/tmp/promo/screens/{n}.png') for n in ['map', 'tanken', 'panne', 'summary', 'meet']}
P = {n: v[0] for n, v in phones.items()}
OFF, SSIZE = phones['map'][1], phones['map'][2]
K = SSIZE[0] / 390.0           # CSS px -> screen px
TOP = 330
ICON = app_icon(300)

def screen_pt(css_x, css_y, top=TOP, scale=1.0, cx=W / 2):
    pw = P['map'].width * scale
    x0 = cx - pw / 2
    return (x0 + (OFF[0] + css_x * K) * scale, top + (OFF[1] + css_y * K) * scale)

def caption(img, t, t0, l1, l2, size=92):
    word_reveal(img, t, t0, 92, l1, size)
    word_reveal(img, t, t0 + 0.18, 92 + size * 1.12, l2, size)

def end_card(img, t, t0, url=True):
    p = prog(t, t0, t0 + 0.6)
    if p > 0:
        s = back_out(p)
        ic = ICON.resize((max(1, int(300 * s)), max(1, int(300 * s))), Image.LANCZOS)
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([W / 2 - 260, 640 - 260, W / 2 + 260, 640 + 260], fill=LIME + (int(70 * p),))
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        img.paste(glow, (0, 0), glow)
        img.paste(ic, (int(W / 2 - ic.width / 2), int(640 - ic.height / 2)), ic)
    word_reveal(img, t, t0 + 0.25, 860, [('Konvoi', WHITE)], 170)
    word_reveal(img, t, t0 + 0.5, 1110, [('Zusammen', MUTED), ('fahren.', MUTED)], 64, font='InterDisplay-Bold.otf')
    word_reveal(img, t, t0 + 0.62, 1195, [('Zusammen', WHITE), ('ankommen.', LIME)], 64, font='InterDisplay-Bold.otf')
    pill(img, W / 2, 1420, 'Kostenlos  ·  ohne Anmeldung', LIME, prog(t, t0 + 0.9, t0 + 1.3), size=42)
    if url:
        word_reveal(img, t, t0 + 1.1, 1540, [('Link', WHITE), ('in', WHITE), ('Bio', LIME)], 54, font='InterDisplay-Bold.otf')

# ------------------------------------------------------------------ MAIN (21.5 s)
def main_scene(t):
    img = bg_frame(t)
    if t < 4.8:
        hook_dots(img, t, 0.0, 4.6)
        word_reveal(img, t, 0.05, 330, [('Wieder', WHITE), ('jemanden', WHITE)], 112)
        word_reveal(img, t, 0.35, 470, [('verloren?', LIME)], 140)
        pill(img, 300, 760, 'Wo seid ihr?', ORANGE, prog(t, 2.6, 2.95), 44)
        pill(img, 760, 880, 'Wer muss tanken?', BLUE, prog(t, 2.9, 3.25), 44)
        pill(img, 420, 1010, 'Wartet mal!!', PINK, prog(t, 3.2, 3.55), 44)
        word_reveal(img, t, 3.75, 1520, [('Schluss', WHITE), ('mit', WHITE), ('Chaos.', WHITE)], 96)
        return img
    if t < 8.6:
        rise = ease_out(prog(t, 4.8, 5.55))
        place_phone(img, P['map'], W / 2, TOP + (1 - rise) * 1500)
        caption(img, t, 4.95, [('Alle', WHITE), ('live', LIME)], [('auf', WHITE), ('einer', WHITE), ('Karte', WHITE)])
        return img
    if t < 11.4:
        cf = ease_in_out(prog(t, 9.15, 9.55))
        crossfade_phone(img, P['map'], P['tanken'], cf, W / 2, TOP)
        x, y = screen_pt(78, 703)
        ripple(img, x, y, prog(t, 8.85, 9.5), AMBER)
        caption(img, t, 8.65, [('Ein', WHITE), ('Tipp:', WHITE)], [('Tanke', AMBER), ('für', WHITE), ('alle', WHITE)])
        return img
    if t < 13.8:
        z = ease_in_out(prog(t, 11.4, 12.1))
        sc = 1 + 0.42 * z
        place_phone(img, P['tanken'], W / 2 + 40 * z, TOP + 10 * z, sc)
        caption(img, t, 11.45, [('Sehen,', WHITE), ('wer', WHITE)], [('dabei', LIME), ('ist', WHITE)])
        return img
    if t < 16.4:
        z = 1 - ease_in_out(prog(t, 13.8, 14.3))
        sc = 1 + 0.42 * z
        cf = ease_in_out(prog(t, 13.9, 14.3))
        mix = Image.blend(P['tanken'], P['panne'], cf)
        place_phone(img, mix, W / 2 + 40 * z, TOP + 10 * z, sc)
        caption(img, t, 13.9, [('Panne?', RED)], [('Alle', WHITE), ('wissen', WHITE), ('Bescheid', WHITE)])
        return img
    if t < 18.8:
        cf = ease_in_out(prog(t, 16.4, 16.8))
        crossfade_phone(img, P['panne'], P['summary'], cf, W / 2, TOP)
        caption(img, t, 16.45, [('Jede', WHITE), ('Fahrt', WHITE)], [('zum', WHITE), ('Teilen', LIME)])
        return img
    out = ease_in_out(prog(t, 18.8, 19.3))
    if out < 1:
        place_phone(img, P['summary'], W / 2, TOP + out * 1600, 1.0, 1 - out)
    end_card(img, t, 19.1)
    return img

# ------------------------------------------------------------------ TEASER (9 s)
def teaser_scene(t):
    img = bg_frame(t)
    if t < 6.2:
        rise = ease_out(prog(t, 0.0, 0.6))
        if t < 3.3:
            place_phone(img, P['map'], W / 2, TOP + (1 - rise) * 1500)
            caption(img, t, 0.15, [('Deine', WHITE), ('Crew.', LIME)], [('Live', WHITE), ('auf', WHITE), ('der', WHITE), ('Karte.', WHITE)])
        else:
            cf = ease_in_out(prog(t, 3.65, 4.05))
            out = ease_in_out(prog(t, 5.8, 6.2))
            mix = Image.blend(P['map'], P['tanken'], cf) if cf < 1 else P['tanken']
            place_phone(img, mix, W / 2, TOP + out * 1600, 1.0, 1 - out)
            x, y = screen_pt(78, 703)
            ripple(img, x, y, prog(t, 3.35, 4.0), AMBER)
            caption(img, t, 3.35, [('Ein', WHITE), ('Tipp:', WHITE)], [('Alle', WHITE), ('zur', WHITE), ('Tanke.', AMBER)])
        return img
    end_card(img, t, 6.0)
    return img

which = sys.argv[1] if len(sys.argv) > 1 else 'both'
if which in ('main', 'both'): render('/tmp/promo/konvoi-werbung-20s.mp4', main_scene, 21.5)
if which in ('teaser', 'both'): render('/tmp/promo/konvoi-teaser-9s.mp4', teaser_scene, 9.0)
if which == 'stills':
    for tt in [1.2, 3.9, 6.5, 9.0, 10.5, 12.8, 15.0, 17.5, 21.0]:
        main_scene(tt).convert('RGB').resize((360, 640)).save(f'/tmp/promo/still_{tt:04.1f}.png')
