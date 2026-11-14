"""Transcribe every take with Whisper and score it against the target line.
usage: python check.py DIR [DIR...]  -> prints table, writes scores.json"""
import sys, json, re, glob, os, difflib
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.dirname(__file__))
LINES = {
    'm1': "Kennt ihr das? Zu viert losgefahren … und plötzlich fehlt einer.",
    'm2': "Mit Konvoi seht ihr euch alle live auf der Karte.",
    'm3': "Einer muss tanken? Ein Tipp, und alle wissen, wohin.",
    'm4': "Und du siehst, wer mitkommt.",
    'm5': "Panne? Alle wissen sofort Bescheid.",
    'm6': "Und am Ende: eure Fahrt als Bild.",
    'm7': "Konvoi. Kostenlos, ohne Anmeldung.",
    't1': "Deine Crew. Live auf der Karte.",
    't2': "Einer muss tanken? Ein Tipp, und alle fahren hin.",
    't3': "Konvoi. Probier's aus.",
    'm5b': "Eine Panne? Alle wissen sofort Bescheid.",
    'm5c': "Panne? Alle wissen sofort Bescheid.",
    'm7b': "Konvoi! Kostenlos, ohne Anmeldung.",
}
def norm(s):
    s = s.lower().replace('convoy', 'konvoi').replace('konvoy', 'konvoi').replace('konvo ', 'konvoi ')
    return re.sub(r"[^a-zäöüß' ]", ' ', s).split()

def trimmed_len(path):
    a, sr = sf.read(path)
    if a.ndim > 1: a = a.mean(1)
    env = np.convolve(np.abs(a), np.ones(int(sr * .02)) / int(sr * .02), 'same')
    idx = np.where(env > 0.01 * env.max())[0]
    return (idx[-1] - idx[0]) / sr, a, sr, idx

m = WhisperModel('medium', device='cpu', compute_type='int8', cpu_threads=2)
res = {}
for d in sys.argv[1:]:
    for p in sorted(glob.glob(f'{d}/*.wav')):
        k = os.path.basename(p).split('_')[0]
        import subprocess
        pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                             capture_output=True, check=True).stdout
        segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), language='de', beam_size=5, initial_prompt='Konvoi')
        txt = ' '.join(s.text.strip() for s in segs)
        sim = difflib.SequenceMatcher(None, norm(LINES[k]), norm(txt)).ratio()
        dur, a, sr, idx = trimmed_len(p)
        # energy in the last 80 ms of speech relative to peak -> abrupt cut indicator
        tail = np.abs(a[max(idx[-1] - int(.08 * sr), 0):idx[-1]]).max() / np.abs(a).max()
        res[p] = dict(line=k, text=txt, sim=round(sim, 3), dur=round(dur, 2), tail=round(float(tail), 3))
        print(f'{p:28s} sim={sim:.2f} dur={dur:4.2f} tail={tail:.2f}  | {txt}', flush=True)
json.dump(res, open('scores.json', 'w'), ensure_ascii=False, indent=1)
