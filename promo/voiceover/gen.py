"""Generate voice-over lines with Chatterbox Multilingual (German).
usage: python gen.py REF.wav OUTDIR TAKES [exaggeration] [cfg] [only_ids...]"""
import sys, os, time, torch, torchaudio
torch.set_num_threads(2)
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

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
    'm5c': "Panne?! Alle wissen sofort Bescheid.",
    'm7b': "Konvoi! Kostenlos, ohne Anmeldung.",
}
ref, outdir, takes = sys.argv[1], sys.argv[2], int(sys.argv[3])
exag = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
cfg = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
only = sys.argv[6:] or list(LINES)
os.makedirs(outdir, exist_ok=True)
m = ChatterboxMultilingualTTS.from_pretrained(device='cpu')
for k in only:
    for i in range(takes):
        torch.manual_seed(int(os.environ.get('SEED', 1000)) + i)
        t0 = time.time()
        wav = m.generate(LINES[k], language_id='de', audio_prompt_path=ref,
                         exaggeration=exag, cfg_weight=cfg, temperature=0.8)
        p = f'{outdir}/{k}_{i}.wav'
        torchaudio.save(p, wav, m.sr)
        print(p, round(wav.shape[-1] / m.sr, 2), 's  took', round(time.time() - t0, 1), flush=True)
