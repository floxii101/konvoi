"""Procedural, royalty-free lo-fi backing track.  usage: python music.py OUT.wav SECONDS"""
import sys, numpy as np, soundfile as sf
SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

def midi(n): return 440 * 2 ** ((n - 69) / 12)

def ep(freq, dur, vel=1.0):
    """Soft electric-piano tone."""
    n = int(dur * SR); t = np.arange(n) / SR
    env = (1 - np.exp(-t / 0.004)) * np.exp(-t / 1.1)
    tone = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t / 0.25)
            + 0.12 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t / 0.12))
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    return vel * tone * env * trem

def pad(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6).clip(0)
    s = sum(np.sin(2 * np.pi * freq * d * t + rng.random() * 6) for d in (0.997, 1.0, 1.003))
    return s * env / 3

def bass(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    env = (1 - np.exp(-t / 0.01)) * np.exp(-t / 0.9) * np.minimum(1, (dur - t) / 0.05).clip(0)
    return (np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(4 * np.pi * freq * t)) * env

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)

def hat(open_=False):
    n = int((0.12 if open_ else 0.04) * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n); x = np.diff(x, prepend=0)  # crude high-pass
    return x * np.exp(-t / (0.04 if open_ else 0.012)) * 0.25

def snap():
    n = int(0.2 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(6) / 6, 'same') - np.convolve(x, np.ones(40) / 40, 'same')
    return x * np.exp(-t / 0.05) * 0.6

def add(buf, sig, at):
    i = max(0, int(at * SR))
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i]

def reverb(x, secs=1.6, mix=0.22):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / (secs / 5))
    ir = np.convolve(ir, np.ones(30) / 30, 'same'); ir /= np.abs(ir).sum() / 4
    from numpy.fft import rfft, irfft
    L = len(x) + n; N = 1 << (L - 1).bit_length()
    wet = irfft(rfft(x, N) * rfft(ir, N), N)[:len(x)]
    return x * (1 - mix) + wet * mix

def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):  # one-pole, fine for short clips
        s = (1 - a) * v + a * s; y[i] = s
    return y

# I – V – vi – IV in C, warm voicings (maj7/add9 colours)
CHORDS = [
    (36, [52, 55, 59, 62]),   # Cmaj7(add9)  E G B D
    (43, [50, 55, 59, 62]),   # G6/9-ish     D G B D
    (45, [52, 55, 60, 64]),   # Am7          E G C E
    (41, [52, 57, 60, 64]),   # Fmaj7        E A C E
]

def render(length):
    total = length + 1.5
    n = int(total * SR)
    keys, low, drums = np.zeros(n), np.zeros(n), np.zeros(n)
    bars = int(np.ceil(length / BAR))
    for b in range(bars):
        root, notes = CHORDS[b % 4] if b < bars - 1 else CHORDS[0]
        t0 = b * BAR
        for p in notes: add(keys, 0.16 * pad(midi(p), BAR + 0.3), t0)
        # lazy EP comping: on 1, the "and" of 2, and 4 – slightly humanised
        for beat, vel in ((0, 1.0), (1.5, 0.7), (3, 0.8)):
            jitter = rng.uniform(-0.012, 0.012)
            for k, p in enumerate(notes):
                add(keys, 0.11 * vel * ep(midi(p + 12), 1.4), t0 + beat * BEAT + k * 0.012 + jitter)
        add(low, 0.42 * bass(midi(root), BEAT * 2.5), t0)
        add(low, 0.30 * bass(midi(root + 7 if b % 2 else root), BEAT * 1.4), t0 + 2.5 * BEAT)
        if b == 0: continue            # drums enter after the first bar
        for beat in (0, 2.5):
            add(drums, 0.55 * kick(), t0 + beat * BEAT)
        for beat in (1, 3):
            add(drums, 0.22 * snap(), t0 + beat * BEAT + 0.01)
        for e in range(8):
            sw = 0.035 if e % 2 else 0       # swing
            add(drums, (0.5 if e % 2 else 0.8) * hat(e == 7), t0 + e * BEAT / 2 + sw)
    keys = reverb(lowpass(keys, 3200), mix=0.3)
    mix = keys + low + reverb(drums, 0.8, 0.12) * 0.8
    mix = lowpass(mix, 7000)
    # vinyl-ish noise bed
    mix += lowpass(rng.standard_normal(n), 2500) * 0.004
    mix = mix[:int(length * SR)]
    fade_in, fade_out = int(0.25 * SR), int(1.6 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out) ** 1.5
    mix /= np.abs(mix).max() / 0.8
    st = np.stack([mix, np.roll(mix, int(0.011 * SR)) * 0.97 + mix * 0.03], 1)  # gentle width
    return st

if __name__ == '__main__':
    sf.write(sys.argv[1], render(float(sys.argv[2])), SR)
