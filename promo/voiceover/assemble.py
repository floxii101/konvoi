"""Place chosen VO takes on the video timeline, mix with ducked music, mux into the videos.
usage: python assemble.py choice.json VIDEO_DIR OUT_DIR"""
import sys, json, subprocess, os, numpy as np, soundfile as sf
SR = 48000
choice = json.load(open(sys.argv[1]))
VID, OUT = sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True); os.makedirs('tmp', exist_ok=True)

# slots from promo/README.md (seconds)
TIMING = {
    'main': dict(video='konvoi-werbung-20s.mp4', music='music_main.wav', length=21.5,
                 slots=[('m1', 0.0, 4.8), ('m2', 4.8, 8.6), ('m3', 8.6, 11.4), ('m4', 11.4, 13.8),
                        ('m5', 13.8, 16.4), ('m6', 16.4, 18.8), ('m7', 18.8, 21.5)]),
    'teaser': dict(video='konvoi-teaser-9s.mp4', music='music_teaser.wav', length=9.0,
                   slots=[('t1', 0.0, 3.3), ('t2', 3.3, 6.0), ('t3', 6.0, 9.0)]),
}
LEAD = 0.18        # voice starts shortly after the cut, like a human VO
MAX_TEMPO = 1.12   # never speed a line up more than this

def load_trimmed(path, tempo=1.0):
    af = f'aresample={SR},highpass=f=70'
    if abs(tempo - 1) > 1e-3: af += f',atempo={tempo:.4f}'
    tmp = f'tmp/{os.path.basename(path)}_{tempo:.3f}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-af', af, '-ac', '1', tmp], check=True)
    a, _ = sf.read(tmp)
    env = np.convolve(np.abs(a), np.ones(960) / 960, 'same')
    idx = np.where(env > 0.01 * env.max())[0]
    a = a[max(0, idx[0] - 480):idx[-1] + 2400]
    fade = 480; a[:fade] *= np.linspace(0, 1, fade); a[-fade * 4:] *= np.linspace(1, 0, fade * 4)
    return a

for name, cfg in TIMING.items():
    L = cfg['length']; vo = np.zeros(int(L * SR)); cursor = 0.0; log = []
    slots = cfg['slots']
    for i, (k, s, e) in enumerate(slots):
        a = load_trimmed(choice[k])
        start = max(s + (0.25 if i == 0 else LEAD), cursor + 0.12)
        # a line may spill up to 0.35 s into the next shot; the last one must end before the fade
        end_target = slots[i + 1][1] + 0.35 if i + 1 < len(slots) else L - 0.3
        avail = end_target - start
        tempo = 1.0
        if len(a) / SR > avail:
            tempo = min(MAX_TEMPO, (len(a) / SR) / avail)
            a = load_trimmed(choice[k], tempo)
        j = int(start * SR); vo[j:j + len(a)] += a[:len(vo) - j]
        cursor = start + len(a) / SR
        log.append(f'{k}: {start:5.2f}–{cursor:5.2f}s (slot {s}–{e}, tempo {tempo:.2f})')
    print(name, *log, sep='\n  ')
    vo_path = f'tmp/vo_{name}.wav'; sf.write(vo_path, vo, SR)
    out = f"{OUT}/{cfg['video'].replace('.mp4', '-vo.mp4')}"
    fc = (
        # voice: presence, gentle compression
        '[1:a]equalizer=f=180:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2,'
        'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2dB,asplit[v][sc];'
        # music: quiet bed, ducked under the voice
        f'[2:a]aresample={SR},volume=-17dB[mu];'
        '[mu][sc]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=400[md];'
        '[v][md]amix=inputs=2:normalize=0,'
        'loudnorm=I=-14:TP=-1.5:LRA=9[a]'
    )
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f"{VID}/{cfg['video']}", '-i', vo_path,
                    '-i', cfg['music'], '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR), '-t', str(L),
                    '-movflags', '+faststart', out], check=True)
    print('->', out)
